# Weaviate Schema Test - Java Client

Java client implementation for testing Weaviate schema import/export functionality.

## Overview

This module tests the Java client's ability to:
1. Load baseline schemas (JSON)
2. Import schemas into Weaviate
3. Export schemas back from Weaviate
4. Compare exported schemas against baselines

## Requirements

- Java 11 or higher
- Maven 3.6+
- Docker (for running Weaviate)

## Dependencies

- **Weaviate Java Client**: 4.8.1
- **JUnit 5**: 5.10.1
- **Jackson**: 2.16.0 (JSON processing)
- **SLF4J**: 2.0.9 (logging)

## Project Structure

```
java/
├── pom.xml                                    # Maven configuration
├── src/
│   ├── main/
│   │   └── java/io/weaviate/schema/test/
│   │       ├── SchemaTestRunner.java          # Import/export logic
│   │       └── SchemaComparator.java          # Schema comparison
│   └── test/
│       └── java/io/weaviate/schema/test/
│           └── SchemaTest.java                # JUnit 5 tests
└── README.md                                  # This file
```

## Setup

### 1. Install Maven Dependencies

```bash
cd test-clients/java
mvn clean install
```

### 2. Start Weaviate

```bash
# From project root
docker-compose -f docker/docker-compose.yml up -d
```

## Running Tests

### Run All Tests

```bash
mvn test
```

### Run Specific Test

```bash
mvn test -Dtest=SchemaTest#testSchemaImportExport
```

### Run with Verbose Output

```bash
mvn test -X
```

### Generate Test Report

```bash
mvn surefire-report:report
# Report generated at: target/site/surefire-report.html
```

## Test Cases

The test suite includes:

### 1. **Parametrized Schema Tests** (`testSchemaImportExport`)
Tests all P0 schemas:
- `P0-basic-text-only`
- `P0-single-named-vector`
- `P0-multi-named-vectors`

For each schema:
1. Load baseline JSON
2. Import to Weaviate
3. Export from Weaviate
4. Save exported schema
5. Compare baseline vs exported
6. Cleanup

### 2. **Full Workflow Tests** (`testFullWorkflow`)
Tests the complete workflow using `SchemaTestRunner.runTest()` method.

### 3. **Normalization Tests** (`testSchemaNormalization`)
Verifies that schemas are normalized correctly:
- Timestamps removed
- Properties sorted alphabetically
- VectorConfig keys sorted

### 4. **Comparator Tests**
- `testComparatorIdenticalSchemas`: Verifies identical schemas match
- `testComparatorDifferentSchemas`: Verifies differences are detected

## Environment Variables

- `WEAVIATE_URL`: Weaviate host (default: `localhost`)
- `WEAVIATE_PORT`: Weaviate port (default: `8080`)

Example:
```bash
export WEAVIATE_URL=my-weaviate-host
mvn test
```

## Output

Test results are saved to:
```
test-results/
├── exported-schemas/java/           # Re-exported schemas
│   ├── P0-basic-text-only/
│   ├── P0-single-named-vector/
│   └── P0-multi-named-vectors/
└── reports/java/                    # JUnit XML reports
    └── TEST-*.xml
```

## Code Usage

### Basic Example

```java
import io.weaviate.schema.test.SchemaTestRunner;
import com.fasterxml.jackson.databind.JsonNode;

// Create test runner
SchemaTestRunner runner = new SchemaTestRunner("localhost");

// Load schema
JsonNode schema = runner.loadSchema("path/to/schema.json");

// Import to Weaviate
String className = runner.importSchema(schema);

// Export from Weaviate
JsonNode exported = runner.exportSchema(className);

// Save exported schema
runner.saveSchema(exported, "output/path/config.json");

// Cleanup
runner.cleanup(className);
```

### Comparison Example

```java
import io.weaviate.schema.test.SchemaComparator;
import com.fasterxml.jackson.databind.JsonNode;

SchemaComparator comparator = new SchemaComparator();

// Compare schemas
SchemaComparator.ComparisonResult result =
    comparator.compareSchemas(baseline, exported, "schemaName");

if (result.isMatch()) {
    System.out.println("✓ Schemas match");
} else {
    System.out.println("✗ Schemas differ");
    System.out.println(result.getDifferences());
}
```

## Known Issues

This test suite is designed to **expose bugs** rather than hide them. The following issues are expected to be caught:

### Issue #1: Missing Collection Name
**Status**: 🔴 CONFIRMED

Weaviate's Java client does not include the collection name in exported schemas, causing all import tests to fail.

**Error**:
```
java.lang.IllegalArgumentException: Schema missing 'name' field
```

This is a **known bug** that affects multiple clients (Python, TypeScript, Java) and is likely a Weaviate server or API design issue.

### Issue #2: Limited vectorConfig Support
**Status**: ⚠️ WARNING

The Java client has limited support for `vectorConfig` compared to Python/TypeScript clients. Some configuration options may not be fully preserved during import/export.

**Note**: This is documented in the code (SchemaTestRunner.java:127-128).

## CI/CD Integration

Tests are automatically run in GitHub Actions on:
- Pull requests
- Pushes to main branch
- Manual workflow dispatch

See `.github/workflows/test-java.yml` for CI configuration.

## Troubleshooting

### Maven Build Fails

**Problem**: `mvn clean install` fails with compilation errors.

**Solution**:
1. Verify Java version: `java -version` (must be 11+)
2. Update Maven: `mvn --version`
3. Clear Maven cache: `rm -rf ~/.m2/repository`

### Weaviate Connection Refused

**Problem**: Tests fail with "Connection refused" error.

**Solution**:
1. Ensure Weaviate is running: `docker ps`
2. Check Weaviate logs: `docker logs weaviate`
3. Verify port 8080 is exposed: `curl http://localhost:8080/v1/schema`

### All Tests Fail with "Schema missing 'name' field"

**Problem**: Every schema test fails immediately.

**Solution**: This is **expected behavior** due to Issue #1 (confirmed bug). The framework intentionally exposes this bug rather than working around it.

To verify the framework is working correctly:
1. Check that schemas are being loaded: Look for "Loading schema from:" in logs
2. Check that import succeeds: Look for "Successfully imported class:" in logs
3. The failure should occur during the second import attempt (when trying to re-import exported schema)

### Test Output Too Verbose

**Problem**: Too much logging output during tests.

**Solution**: Adjust SLF4J configuration in `src/main/resources/simplelogger.properties`:
```properties
org.slf4j.simpleLogger.defaultLogLevel=warn
```

## Development

### Adding New Test Cases

1. Add schema definition in `schema-generator/src/schema_definitions.py`
2. Generate baseline: `cd schema-generator && python -m src.cli generate-one <name>`
3. Add to test parameters in `SchemaTest.java`:
```java
@ValueSource(strings = {
    "P0-basic-text-only",
    "P0-single-named-vector",
    "P0-multi-named-vectors",
    "P1-your-new-schema"  // Add here
})
```
4. Run tests: `mvn test`

### Code Style

This project follows standard Java conventions:
- Class names: PascalCase
- Method names: camelCase
- Constants: UPPER_SNAKE_CASE
- Indentation: 4 spaces
- Line length: 120 characters

Format code:
```bash
mvn formatter:format
```

## Resources

- [Weaviate Java Client Documentation](https://weaviate.io/developers/weaviate/client-libraries/java)
- [Weaviate API Reference](https://weaviate.io/developers/weaviate/api)
- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [Maven Documentation](https://maven.apache.org/guides/)

## Contributing

When contributing to the Java client:

1. Write tests for new functionality
2. Ensure all tests pass: `mvn test`
3. Follow existing code patterns
4. Document any new issues discovered
5. Do NOT add workarounds for known bugs (expose them instead)

## License

See main project LICENSE file.

## Support

For issues related to:
- **Framework**: Open issue in this repository
- **Weaviate Java Client**: https://github.com/weaviate/weaviate-java-client
- **Weaviate Server**: https://github.com/weaviate/weaviate
