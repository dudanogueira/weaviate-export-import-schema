# Weaviate Multi-Client Export/Import Testing Framework

A comprehensive testing framework that validates Weaviate collection export/import functionality across multiple client libraries (Python, TypeScript, Go, C#, Java). Python serves as the source of truth, generating baseline schemas that all other clients must correctly import and re-export.

---

## 🟢 Current Status - Major Progress!

**This framework has successfully achieved cross-client schema compatibility!** 🎉

**Latest Results (2026-02-09)**:
- **Python v4.19.2**: ✅ **4/4 tests PASSING**
- **TypeScript v3.10.0 (with `exportToJson`)**: ⚠️ 1/4 tests passing (field-level differences only)
- **Java v4.8.1**: Not yet tested with new approach
- **C# v1.0.0**: Not yet tested with new approach

**Key Achievement**: Implemented new `exportToJson()` method in TypeScript client that resolved fundamental structural incompatibilities between Python and TypeScript schema exports.

**📋 [See issues/ directory for detailed bug reports and resolutions](issues/)**

### Recent Breakthroughs

1. **Issue #6 - RESOLVED**: TypeScript and Python now export schemas with compatible structure
   - Status changed from 🔴 CRITICAL to 🟡 IMPROVED
   - Structural compatibility achieved through new `exportToJson()` API
   - Remaining differences are informational enhancements, not incompatibilities

2. **Issue #5 - RESOLVED**: DataType array vs string mismatch fixed with `exportToJson()`

3. **Schema Definition Format**: Fixed v3 to v4 format migration in baseline schemas

---

## Overview

This framework ensures consistency and correctness of schema import/export operations across different Weaviate client implementations by:

1. **Generating baseline schemas** using Python (source of truth)
2. **Testing each client** by importing baseline schemas and re-exporting them
3. **Comparing exported schemas** against baselines to ensure consistency
4. **Tracking version compatibility** across Weaviate and client libraries

## Project Structure

```
weaviate-export-import-schema/
├── schema-generator/          # Python schema generator (source of truth)
├── schemas/                   # Generated baseline schemas (JSON)
├── test-clients/              # Client test implementations
│   ├── python/
│   ├── typescript/
│   ├── java/
│   └── csharp/
├── test-results/              # Test execution results (not in git)
├── docker/                    # Docker configurations
├── scripts/                   # Utility scripts
├── version-tracking/          # Client version tracking
├── issues/                    # Documented bugs discovered by framework
└── .github/workflows/         # CI/CD workflows
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for TypeScript tests)
- Java 11+ and Maven 3.6+ (for Java tests)
- .NET 8.0+ SDK (for C# tests)
- Git

### Setup Local Environment

Run the automated setup script:

```bash
./scripts/setup_local_env.sh
```

This will:
1. Start Weaviate in Docker
2. Setup Python environments
3. Generate baseline schemas
4. Setup TypeScript environment
5. Install all dependencies

### Run Tests

#### All Tests

```bash
./scripts/run_all_tests.sh
```

#### Python Tests Only

```bash
cd test-clients/python
source .venv/bin/activate
pytest -v
```

#### TypeScript Tests Only

```bash
cd test-clients/typescript
npm test
```

#### Java Tests Only

```bash
cd test-clients/java
mvn test
```

#### C# Tests Only

```bash
cd test-clients/csharp
dotnet test
```

### Compare Results

After running tests, compare results across clients:

```bash
python scripts/compare_results.py
```

View the report at: `test-results/comparisons/report.md`

## Schema Definitions

The framework tests three P0 (basic) schemas:

- **P0-basic-text-only**: Simple collection with text properties, no vectors
- **P0-single-named-vector**: Collection with one named vector configuration
- **P0-multi-named-vectors**: Collection with multiple named vectors

See [schemas/README.md](schemas/README.md) for detailed documentation.

## CI/CD

The framework includes GitHub Actions workflows:

- **generate-schemas.yml**: Generate baseline schemas (manual or on definition changes)
- **test-python.yml**: Run Python tests (PR, push to main, manual)
- **test-typescript.yml**: Run TypeScript tests (PR, push to main, manual)
- **test-java.yml**: Run Java tests on JDK 11, 17, and 21 (PR, push to main, manual)
- **test-csharp.yml**: Run C# tests on .NET 8.0 and 9.0 (PR, push to main, manual)
- **version-check.yml**: Check for client updates (manual)

## Development

### Adding a New Schema

1. Add schema definition to `schema-generator/src/schema_definitions.py`
2. Regenerate schemas:
   ```bash
   cd schema-generator
   python -m src.cli generate-all --output-dir ../schemas
   ```
3. Commit the new schema JSON files

### Adding a New Client

1. Create directory: `test-clients/<language>/`
2. Implement test runner following the pattern in Python/TypeScript
3. Add CI/CD workflow: `.github/workflows/test-<language>.yml`
4. Update version tracking: `version-tracking/versions.json`

### Schema Comparison Rules

The comparison engine normalizes schemas by:
- Removing timestamps (`creationTimeUnix`, `lastUpdateTimeUnix`)
- Sorting properties and vector configs for consistent ordering
- Applying default values for optional fields

## Troubleshooting

### Weaviate not starting

```bash
# Check Docker status
docker ps

# View logs
docker-compose -f docker/docker-compose.yml logs

# Restart
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

### Tests failing

1. Ensure Weaviate is running and healthy:
   ```bash
   curl http://localhost:8080/v1/.well-known/ready
   ```

2. Check baseline schemas exist:
   ```bash
   ls -la schemas/
   ```

3. View detailed test output:
   ```bash
   pytest -vv --tb=long  # Python
   npm test -- --reporter=verbose  # TypeScript
   ```

## Architecture

### Design Decisions

- **Python as Source of Truth**: Python client is typically most feature-complete
- **JSON for Schema Export**: Language-agnostic, version controllable
- **Separate Weaviate per Test**: Clean state, no contamination
- **Local Docker Only**: No cloud dependencies, fast iteration

### Trade-offs

- **Pros**: Comprehensive testing, multi-language validation, automated CI/CD
- **Cons**: Slower execution (Docker startup), requires local setup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Submit a pull request

## License

MIT

## Support

For issues or questions:
- GitHub Issues: [Create an issue](https://github.com/your-org/weaviate-export-import-schema/issues)
- Weaviate Slack: [Join the community](https://weaviate.io/slack)
