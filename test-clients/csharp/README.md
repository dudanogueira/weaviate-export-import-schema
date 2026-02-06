# Weaviate Schema Test - C# Client

C# client implementation for testing Weaviate schema import/export functionality.

## Overview

This module tests the C# client's ability to:
1. Load baseline schemas (JSON)
2. Import schemas into Weaviate
3. Export schemas back from Weaviate
4. Compare exported schemas against baselines

## Requirements

- .NET 8.0 SDK or higher
- Docker (for running Weaviate)

## Dependencies

- **Weaviate.Client**: 2.4.3
- **xUnit**: 2.6.3 (testing framework)
- **Newtonsoft.Json**: 13.0.3 (JSON processing)
- **DeepEqual**: 4.0.0 (deep comparison)

## Project Structure

```
csharp/
├── WeaviateSchemaTest.csproj          # Project configuration
├── SchemaTestRunner.cs                # Import/export logic
├── SchemaComparator.cs                # Schema comparison
├── SchemaTests.cs                     # xUnit tests
└── README.md                          # This file
```

## Setup

### 1. Install .NET SDK

Download from: https://dotnet.microsoft.com/download/dotnet/8.0

Verify installation:
```bash
dotnet --version
```

### 2. Restore Dependencies

```bash
cd test-clients/csharp
dotnet restore
```

### 3. Start Weaviate

```bash
# From project root
docker-compose -f docker/docker-compose.yml up -d
```

## Running Tests

### Run All Tests

```bash
dotnet test
```

### Run with Verbose Output

```bash
dotnet test --logger "console;verbosity=detailed"
```

### Run Specific Test

```bash
dotnet test --filter "TestSchemaImportExport"
```

### Generate Test Report

```bash
dotnet test --logger "trx;LogFileName=test-results.trx"
# Report generated at: TestResults/test-results.trx
```

## Test Cases

The test suite includes:

### 1. **Parametrized Schema Tests** (`TestSchemaImportExport`)
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

### 2. **Full Workflow Tests** (`TestFullWorkflow`)
Tests the complete workflow using `SchemaTestRunner.RunTest()` method.

### 3. **Normalization Tests** (`TestSchemaNormalization`)
Verifies that schemas are normalized correctly:
- Timestamps removed
- Properties sorted alphabetically
- VectorConfig keys sorted

### 4. **Comparator Tests**
- `TestComparatorIdenticalSchemas`: Verifies identical schemas match
- `TestComparatorDifferentSchemas`: Verifies differences are detected

## Environment Variables

- `WEAVIATE_URL`: Weaviate host (default: `localhost`)

Example:
```bash
export WEAVIATE_URL=my-weaviate-host
dotnet test
```

## Output

Test results are saved to:
```
test-results/
├── exported-schemas/csharp/         # Re-exported schemas
│   ├── P0-basic-text-only/
│   ├── P0-single-named-vector/
│   └── P0-multi-named-vectors/
└── reports/csharp/                  # Test reports
    └── test-results.trx
```

## Code Usage

### Basic Example

```csharp
using WeaviateSchemaTest;
using Newtonsoft.Json.Linq;

// Create test runner
var runner = new SchemaTestRunner("localhost");

// Load schema
var schema = runner.LoadSchema("path/to/schema.json");

// Import to Weaviate
var className = runner.ImportSchema(schema);

// Export from Weaviate
var exported = runner.ExportSchema(className);

// Save exported schema
runner.SaveSchema(exported, "output/path/config.json");

// Cleanup
runner.Cleanup(className);
```

### Comparison Example

```csharp
using WeaviateSchemaTest;
using Newtonsoft.Json.Linq;

var comparator = new SchemaComparator();

// Compare schemas
var result = comparator.CompareSchemas(baseline, exported, "schemaName");

if (result.IsMatch)
{
    Console.WriteLine("✓ Schemas match");
}
else
{
    Console.WriteLine("✗ Schemas differ");
    Console.WriteLine($"Differences: {result.Differences.Count}");
}
```

## Known Issues

This test suite is designed to **expose bugs** rather than hide them. The following issues are expected to be caught:

### Issue #1: Missing Collection Name
**Status**: 🔴 CONFIRMED

Weaviate's C# client does not include the collection name in exported schemas, causing all import tests to fail.

**Error**:
```
System.ArgumentException: Schema missing 'name' field
```

This is a **known bug** that affects multiple clients (Python, TypeScript, Java, C#) and is likely a Weaviate server or API design issue.

### Issue #2: Limited vectorConfig Support
**Status**: ⚠️ WARNING

The C# client has limited support for `vectorConfig` compared to Python/TypeScript clients. Some configuration options may not be fully preserved during import/export.

**Note**: This is documented in the code (SchemaTestRunner.cs:122-123).

## CI/CD Integration

Tests are automatically run in GitHub Actions on:
- Pull requests
- Pushes to main branch
- Manual workflow dispatch

See `.github/workflows/test-csharp.yml` for CI configuration.

## Troubleshooting

### .NET SDK Not Found

**Problem**: `dotnet` command not found.

**Solution**:
1. Install .NET SDK from https://dotnet.microsoft.com/download
2. Restart terminal
3. Verify: `dotnet --version`

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

### Build Errors

**Problem**: Build fails with package restore errors.

**Solution**:
```bash
dotnet clean
dotnet restore
dotnet build
```

## Development

### Adding New Test Cases

1. Add schema definition in `schema-generator/src/schema_definitions.py`
2. Generate baseline: `cd schema-generator && python -m src.cli generate-one <name>`
3. Tests will automatically pick up new schemas (no code changes needed)
4. Run tests: `dotnet test`

### Code Style

This project follows standard C# conventions:
- PascalCase for classes, methods, properties
- camelCase for local variables, parameters
- Private fields: _camelCase with underscore prefix
- Use `var` for local variables when type is obvious
- Nullable reference types enabled

Format code:
```bash
dotnet format
```

## Resources

- [Weaviate C# Client Documentation](https://weaviate.io/developers/weaviate/client-libraries/csharp)
- [Weaviate API Reference](https://weaviate.io/developers/weaviate/api)
- [xUnit Documentation](https://xunit.net/)
- [.NET Documentation](https://docs.microsoft.com/dotnet/)

## Contributing

When contributing to the C# client:

1. Write tests for new functionality
2. Ensure all tests pass: `dotnet test`
3. Follow existing code patterns
4. Document any new issues discovered
5. Do NOT add workarounds for known bugs (expose them instead)

## License

See main project LICENSE file.

## Support

For issues related to:
- **Framework**: Open issue in this repository
- **Weaviate C# Client**: https://github.com/weaviate/weaviate-dotnet-client
- **Weaviate Server**: https://github.com/weaviate/weaviate
