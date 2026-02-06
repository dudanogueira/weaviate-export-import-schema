package io.weaviate.schema.test;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.weaviate.client.Config;
import io.weaviate.client.WeaviateClient;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;

import static org.junit.jupiter.api.Assertions.*;

/**
 * JUnit 5 tests for Weaviate schema import/export validation.
 * Tests all P0 schemas across the Java client.
 */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class SchemaTest {
    private static final Logger logger = LoggerFactory.getLogger(SchemaTest.class);

    private static final String WEAVIATE_URL = System.getenv().getOrDefault("WEAVIATE_URL", "localhost");
    private static final String BASELINE_DIR = "../../schemas";
    private static final String OUTPUT_DIR = "../../test-results/exported-schemas";

    private SchemaTestRunner testRunner;
    private SchemaComparator comparator;
    private ObjectMapper objectMapper;

    @BeforeAll
    void setup() {
        logger.info("Setting up Java test environment");
        logger.info("Weaviate URL: {}", WEAVIATE_URL);

        this.testRunner = new SchemaTestRunner(WEAVIATE_URL);
        this.comparator = new SchemaComparator();
        this.objectMapper = new ObjectMapper();

        // Create output directory
        new File(OUTPUT_DIR + "/java").mkdirs();
    }

    @AfterAll
    void teardown() {
        logger.info("Java test teardown complete");
    }

    /**
     * Parametrized test that runs import/export validation for all P0 schemas.
     */
    @ParameterizedTest
    @ValueSource(strings = {
        "P0-basic-text-only",
        "P0-single-named-vector",
        "P0-multi-named-vectors"
    })
    @DisplayName("Test schema import and export")
    void testSchemaImportExport(String schemaName) throws Exception {
        logger.info("\n========================================");
        logger.info("Testing schema: {}", schemaName);
        logger.info("========================================");

        // 1. Load baseline schema
        String baselinePath = Paths.get(BASELINE_DIR, schemaName, "config.json").toString();
        JsonNode baseline = testRunner.loadSchema(baselinePath);
        logger.info("Loaded baseline schema from: {}", baselinePath);

        // 2. Import schema to Weaviate
        String className = testRunner.importSchema(baseline);
        logger.info("Imported schema with class: {}", className);

        // 3. Export schema from Weaviate
        JsonNode exported = testRunner.exportSchema(className);
        logger.info("Exported schema from Weaviate");

        // 4. Save exported schema
        String outputPath = Paths.get(OUTPUT_DIR, "java", schemaName, "config.json").toString();
        testRunner.saveSchema(exported, outputPath);
        logger.info("Saved exported schema to: {}", outputPath);

        // 5. Compare baseline vs exported
        SchemaComparator.ComparisonResult result = comparator.compareSchemas(baseline, exported, schemaName);

        // 6. Cleanup
        testRunner.cleanup(className);
        logger.info("Cleaned up class: {}", className);

        // 7. Assert schemas match
        if (!result.isMatch()) {
            logger.error("Schema mismatch detected!");
            logger.error("Differences: {}", objectMapper.writerWithDefaultPrettyPrinter()
                    .writeValueAsString(result.getDifferences()));

            fail(String.format("Schema mismatch for %s. Differences: %s",
                    schemaName, result.getDifferences()));
        }

        logger.info("✓ Schema {} passed validation", schemaName);
    }

    /**
     * Test the full workflow using TestRunner.runTest() method.
     */
    @ParameterizedTest
    @ValueSource(strings = {
        "P0-basic-text-only",
        "P0-single-named-vector",
        "P0-multi-named-vectors"
    })
    @DisplayName("Test full workflow with TestRunner")
    void testFullWorkflow(String schemaName) {
        logger.info("\n========================================");
        logger.info("Testing full workflow for: {}", schemaName);
        logger.info("========================================");

        String baselinePath = Paths.get(BASELINE_DIR, schemaName, "config.json").toString();

        SchemaTestRunner.TestResult result = testRunner.runTest(baselinePath, OUTPUT_DIR, schemaName);

        if (!result.isSuccess()) {
            logger.error("Test failed for {}: {}", schemaName, result.getError());
            fail(String.format("Test failed for %s: %s", schemaName, result.getError()));
        }

        logger.info("✓ Full workflow for {} completed successfully", schemaName);
        logger.info("Exported to: {}", result.getExportedPath());
    }

    /**
     * Test schema normalization.
     */
    @Test
    @DisplayName("Test schema normalization")
    void testSchemaNormalization() throws IOException {
        logger.info("Testing schema normalization");

        String testSchema = "{"
                + "\"name\":\"Test\","
                + "\"properties\":["
                + "{\"name\":\"z_prop\"},"
                + "{\"name\":\"a_prop\"}"
                + "],"
                + "\"creationTimeUnix\":123456789,"
                + "\"lastUpdateTimeUnix\":987654321"
                + "}";

        JsonNode schema = objectMapper.readTree(testSchema);
        JsonNode normalized = comparator.normalizeSchema(schema);

        // Verify timestamps removed
        assertFalse(normalized.has("creationTimeUnix"), "creationTimeUnix should be removed");
        assertFalse(normalized.has("lastUpdateTimeUnix"), "lastUpdateTimeUnix should be removed");

        // Verify properties sorted (a_prop should come before z_prop)
        if (normalized.has("properties")) {
            JsonNode properties = normalized.get("properties");
            if (properties.size() >= 2) {
                String firstName = properties.get(0).get("name").asText();
                assertEquals("a_prop", firstName, "Properties should be sorted alphabetically");
            }
        }

        logger.info("✓ Schema normalization test passed");
    }

    /**
     * Test comparator with identical schemas.
     */
    @Test
    @DisplayName("Test comparator with identical schemas")
    void testComparatorIdenticalSchemas() throws IOException {
        logger.info("Testing comparator with identical schemas");

        String schema1 = "{\"name\":\"Test\",\"description\":\"A test schema\"}";
        String schema2 = "{\"name\":\"Test\",\"description\":\"A test schema\"}";

        JsonNode json1 = objectMapper.readTree(schema1);
        JsonNode json2 = objectMapper.readTree(schema2);

        SchemaComparator.ComparisonResult result = comparator.compareSchemas(json1, json2, "test");

        assertTrue(result.isMatch(), "Identical schemas should match");
        assertTrue(result.getDifferences().isEmpty(), "No differences should be found");

        logger.info("✓ Comparator identical schemas test passed");
    }

    /**
     * Test comparator with different schemas.
     */
    @Test
    @DisplayName("Test comparator with different schemas")
    void testComparatorDifferentSchemas() throws IOException {
        logger.info("Testing comparator with different schemas");

        String schema1 = "{\"name\":\"Test1\",\"description\":\"Schema one\"}";
        String schema2 = "{\"name\":\"Test2\",\"description\":\"Schema two\"}";

        JsonNode json1 = objectMapper.readTree(schema1);
        JsonNode json2 = objectMapper.readTree(schema2);

        SchemaComparator.ComparisonResult result = comparator.compareSchemas(json1, json2, "test");

        assertFalse(result.isMatch(), "Different schemas should not match");
        assertFalse(result.getDifferences().isEmpty(), "Differences should be found");

        logger.info("✓ Comparator different schemas test passed");
        logger.info("Differences found: {}", result.getDifferences().size());
    }
}
