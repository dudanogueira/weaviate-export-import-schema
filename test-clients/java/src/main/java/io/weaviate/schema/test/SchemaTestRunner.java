package io.weaviate.schema.test;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.weaviate.client.Config;
import io.weaviate.client.WeaviateClient;
import io.weaviate.client.base.Result;
import io.weaviate.client.v1.schema.model.Property;
import io.weaviate.client.v1.schema.model.WeaviateClass;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Test runner for importing and exporting Weaviate schemas.
 */
public class SchemaTestRunner {
    private static final Logger logger = LoggerFactory.getLogger(SchemaTestRunner.class);

    private final WeaviateClient client;
    private final ObjectMapper objectMapper;
    private final String weaviateUrl;

    public SchemaTestRunner(String weaviateUrl) {
        this.weaviateUrl = weaviateUrl;
        Config config = new Config("http", weaviateUrl + ":8080");
        this.client = new WeaviateClient(config);
        this.objectMapper = new ObjectMapper();
    }

    /**
     * Load a schema from JSON file.
     */
    public JsonNode loadSchema(String schemaPath) throws IOException {
        logger.info("Loading schema from: {}", schemaPath);
        File file = new File(schemaPath);
        return objectMapper.readTree(file);
    }

    /**
     * Import a schema into Weaviate by creating a class.
     */
    public String importSchema(JsonNode schema) throws Exception {
        String className = schema.has("name") ? schema.get("name").asText() : null;

        if (className == null) {
            throw new IllegalArgumentException("Schema missing 'name' field");
        }

        logger.info("Importing class: {}", className);

        // Delete if exists
        Result<WeaviateClass> existsResult = client.schema().classGetter().withClassName(className).run();
        if (existsResult.getResult() != null) {
            logger.info("Deleting existing class: {}", className);
            client.schema().classDeleter().withClassName(className).run();
        }

        // Build WeaviateClass from JSON
        WeaviateClass weaviateClass = buildWeaviateClass(schema);

        // Create the class
        Result<Boolean> result = client.schema().classCreator().withClass(weaviateClass).run();

        if (result.hasErrors()) {
            throw new Exception("Failed to create class: " + result.getError());
        }

        logger.info("Successfully imported class: {}", className);
        return className;
    }

    /**
     * Build a WeaviateClass object from JSON schema.
     */
    private WeaviateClass buildWeaviateClass(JsonNode schema) {
        WeaviateClass.WeaviateClassBuilder builder = WeaviateClass.builder();

        // Set class name
        if (schema.has("name")) {
            builder.className(schema.get("name").asText());
        }

        // Set description
        if (schema.has("description")) {
            builder.description(schema.get("description").asText());
        }

        // Build properties
        if (schema.has("properties")) {
            List<Property> properties = new ArrayList<>();
            schema.get("properties").forEach(prop -> {
                Property.PropertyBuilder propBuilder = Property.builder()
                        .name(prop.get("name").asText());

                if (prop.has("dataType")) {
                    List<String> dataTypes = new ArrayList<>();
                    prop.get("dataType").forEach(dt -> dataTypes.add(dt.asText()));
                    propBuilder.dataType(dataTypes);
                }

                if (prop.has("description")) {
                    propBuilder.description(prop.get("description").asText());
                }

                properties.add(propBuilder.build());
            });
            builder.properties(properties);
        }

        // Set vectorizer
        if (schema.has("vectorizer")) {
            builder.vectorizer(schema.get("vectorizer").asText());
        } else {
            builder.vectorizer("none");
        }

        // Note: Java client has limited support for vectorConfig
        // This is a known limitation that the framework will expose

        return builder.build();
    }

    /**
     * Export a class's schema configuration.
     */
    public JsonNode exportSchema(String className) throws Exception {
        logger.info("Exporting schema for class: {}", className);

        Result<WeaviateClass> result = client.schema().classGetter().withClassName(className).run();

        if (result.hasErrors()) {
            throw new Exception("Failed to export schema: " + result.getError());
        }

        WeaviateClass weaviateClass = result.getResult();

        // Convert WeaviateClass to JsonNode
        String json = objectMapper.writeValueAsString(weaviateClass);
        JsonNode exported = objectMapper.readTree(json);

        logger.info("Exported schema for class: {}", className);
        return exported;
    }

    /**
     * Save schema to JSON file.
     */
    public void saveSchema(JsonNode schema, String outputPath) throws IOException {
        Path path = Paths.get(outputPath);
        Files.createDirectories(path.getParent());

        objectMapper.writerWithDefaultPrettyPrinter()
                .writeValue(path.toFile(), schema);

        logger.info("Saved schema to: {}", outputPath);
    }

    /**
     * Delete a class from Weaviate.
     */
    public void cleanup(String className) {
        try {
            Result<WeaviateClass> existsResult = client.schema().classGetter().withClassName(className).run();
            if (existsResult.getResult() != null) {
                client.schema().classDeleter().withClassName(className).run();
                logger.info("Cleaned up class: {}", className);
            }
        } catch (Exception e) {
            logger.warn("Failed to cleanup class: {}", e.getMessage());
        }
    }

    /**
     * Run a complete import/export test.
     */
    public TestResult runTest(String baselinePath, String outputDir, String schemaName) {
        TestResult result = new TestResult(schemaName);

        try {
            // Load baseline
            JsonNode baseline = loadSchema(baselinePath);

            // Import schema
            String className = importSchema(baseline);

            // Export schema
            JsonNode exported = exportSchema(className);

            // Save exported schema
            String outputPath = Paths.get(outputDir, "java", schemaName, "config.json").toString();
            saveSchema(exported, outputPath);

            result.setSuccess(true);
            result.setExportedPath(outputPath);

            // Cleanup
            cleanup(className);

        } catch (Exception e) {
            result.setSuccess(false);
            result.setError(e.getMessage());
            logger.error("Test failed for {}: {}", schemaName, e.getMessage(), e);
        }

        return result;
    }

    /**
     * Result of a test run.
     */
    public static class TestResult {
        private final String schemaName;
        private boolean success;
        private String error;
        private String exportedPath;

        public TestResult(String schemaName) {
            this.schemaName = schemaName;
            this.success = false;
        }

        public String getSchemaName() {
            return schemaName;
        }

        public boolean isSuccess() {
            return success;
        }

        public void setSuccess(boolean success) {
            this.success = success;
        }

        public String getError() {
            return error;
        }

        public void setError(String error) {
            this.error = error;
        }

        public String getExportedPath() {
            return exportedPath;
        }

        public void setExportedPath(String exportedPath) {
            this.exportedPath = exportedPath;
        }
    }
}
