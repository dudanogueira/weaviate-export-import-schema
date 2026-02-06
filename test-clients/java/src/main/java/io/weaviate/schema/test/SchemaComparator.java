package io.weaviate.schema.test;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * Schema comparison engine for validating import/export consistency.
 */
public class SchemaComparator {
    private static final Logger logger = LoggerFactory.getLogger(SchemaComparator.class);
    private final ObjectMapper objectMapper;

    // Fields to ignore during comparison (timestamps, internal IDs, etc.)
    private static final Set<String> IGNORE_FIELDS = new HashSet<>(Arrays.asList(
            "creationTimeUnix",
            "lastUpdateTimeUnix"
    ));

    public SchemaComparator() {
        this.objectMapper = new ObjectMapper();
    }

    /**
     * Normalize a schema by removing internal fields and applying defaults.
     */
    public JsonNode normalizeSchema(JsonNode schema) {
        JsonNode normalized = schema.deepCopy();

        // Remove timestamp fields
        if (normalized.isObject()) {
            ObjectNode obj = (ObjectNode) normalized;
            IGNORE_FIELDS.forEach(obj::remove);

            // Sort properties by name for consistent comparison
            if (obj.has("properties") && obj.get("properties").isArray()) {
                ArrayNode properties = (ArrayNode) obj.get("properties");
                List<JsonNode> propList = new ArrayList<>();
                properties.forEach(propList::add);

                propList.sort((a, b) -> {
                    String nameA = a.has("name") ? a.get("name").asText() : "";
                    String nameB = b.has("name") ? b.get("name").asText() : "";
                    return nameA.compareTo(nameB);
                });

                obj.remove("properties");
                ArrayNode sortedProps = obj.putArray("properties");
                propList.forEach(sortedProps::add);
            }

            // Sort vectorConfig keys if present
            if (obj.has("vectorConfig") && obj.get("vectorConfig").isObject()) {
                ObjectNode vectorConfig = (ObjectNode) obj.get("vectorConfig");
                Map<String, JsonNode> sortedMap = new TreeMap<>();
                vectorConfig.fields().forEachRemaining(entry ->
                    sortedMap.put(entry.getKey(), entry.getValue())
                );

                obj.remove("vectorConfig");
                ObjectNode sortedVectorConfig = obj.putObject("vectorConfig");
                sortedMap.forEach(sortedVectorConfig::set);
            }
        }

        return normalized;
    }

    /**
     * Compare two schemas and report differences.
     *
     * @param baseline Baseline schema (source of truth)
     * @param exported Exported schema to compare
     * @param schemaName Name of schema for reporting
     * @return ComparisonResult containing match status and differences
     */
    public ComparisonResult compareSchemas(JsonNode baseline, JsonNode exported, String schemaName) {
        logger.info("Comparing schemas for: {}", schemaName);

        // Normalize both schemas
        JsonNode normBaseline = normalizeSchema(baseline);
        JsonNode normExported = normalizeSchema(exported);

        // Check for equality
        if (normBaseline.equals(normExported)) {
            logger.info("✓ Schemas match perfectly: {}", schemaName);
            return new ComparisonResult(true, new HashMap<>());
        }

        // Find differences
        Map<String, Object> differences = findDifferences(normBaseline, normExported, "root");

        logger.warn("✗ Schemas differ: {}", schemaName);
        logger.debug("Differences: {}", differences);

        return new ComparisonResult(false, differences);
    }

    /**
     * Find differences between two JSON nodes.
     */
    private Map<String, Object> findDifferences(JsonNode obj1, JsonNode obj2, String path) {
        Map<String, Object> differences = new HashMap<>();

        if (obj1.getNodeType() != obj2.getNodeType()) {
            Map<String, Object> diff = new HashMap<>();
            diff.put("type", "type_mismatch");
            diff.put("value1", obj1.getNodeType().toString());
            diff.put("value2", obj2.getNodeType().toString());
            differences.put(path, diff);
            return differences;
        }

        if (obj1.isObject()) {
            Set<String> allKeys = new HashSet<>();
            obj1.fieldNames().forEachRemaining(allKeys::add);
            obj2.fieldNames().forEachRemaining(allKeys::add);

            for (String key : allKeys) {
                if (!obj1.has(key)) {
                    Map<String, Object> diff = new HashMap<>();
                    diff.put("type", "missing_in_first");
                    diff.put("value2", obj2.get(key));
                    differences.put(path + "." + key, diff);
                } else if (!obj2.has(key)) {
                    Map<String, Object> diff = new HashMap<>();
                    diff.put("type", "missing_in_second");
                    diff.put("value1", obj1.get(key));
                    differences.put(path + "." + key, diff);
                } else {
                    differences.putAll(findDifferences(obj1.get(key), obj2.get(key), path + "." + key));
                }
            }
        } else if (obj1.isArray()) {
            if (obj1.size() != obj2.size()) {
                Map<String, Object> diff = new HashMap<>();
                diff.put("type", "array_length_mismatch");
                diff.put("length1", obj1.size());
                diff.put("length2", obj2.size());
                differences.put(path, diff);
            }

            int maxLen = Math.max(obj1.size(), obj2.size());
            for (int i = 0; i < maxLen; i++) {
                if (i < obj1.size() && i < obj2.size()) {
                    differences.putAll(findDifferences(obj1.get(i), obj2.get(i), path + "[" + i + "]"));
                }
            }
        } else {
            if (!obj1.equals(obj2)) {
                Map<String, Object> diff = new HashMap<>();
                diff.put("type", "value_mismatch");
                diff.put("value1", obj1);
                diff.put("value2", obj2);
                differences.put(path, diff);
            }
        }

        return differences;
    }

    /**
     * Result of a schema comparison.
     */
    public static class ComparisonResult {
        private final boolean match;
        private final Map<String, Object> differences;

        public ComparisonResult(boolean match, Map<String, Object> differences) {
            this.match = match;
            this.differences = differences;
        }

        public boolean isMatch() {
            return match;
        }

        public Map<String, Object> getDifferences() {
            return differences;
        }
    }
}
