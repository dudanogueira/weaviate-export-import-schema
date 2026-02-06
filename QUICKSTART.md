# Quick Start Guide

Get up and running with the Weaviate Schema Testing Framework in 5 minutes.

## Prerequisites Check

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python3 --version  # Need 3.11+

# Check Node.js (optional, for TypeScript tests)
node --version     # Need 18+
npm --version
```

## Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
# Clone the repository (if not already done)
cd weaviate-export-import-schema

# Make scripts executable
chmod +x scripts/*.sh

# Run automated setup
./scripts/setup_local_env.sh
```

This script will:
1. ✅ Start Weaviate
2. ✅ Setup Python environments
3. ✅ Generate baseline schemas
4. ✅ Install all dependencies

Then run all tests:

```bash
./scripts/run_all_tests.sh
```

## Option 2: Manual Setup

### Step 1: Start Weaviate

```bash
docker-compose -f docker/docker-compose.yml up -d

# Wait for Weaviate to be ready
curl http://localhost:8080/v1/.well-known/ready
```

### Step 2: Generate Baseline Schemas

```bash
cd schema-generator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate schemas
python -m src.cli generate-all --output-dir ../schemas

# Verify schemas
ls -la ../schemas/
```

You should see:
- `P0-basic-text-only/config.json`
- `P0-single-named-vector/config.json`
- `P0-multi-named-vectors/config.json`

### Step 3: Run Python Tests

```bash
cd ../test-clients/python

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v tests/
```

Expected output:
```
test_schemas.py::test_schema_import_export[P0-basic-text-only] PASSED
test_schemas.py::test_schema_import_export[P0-single-named-vector] PASSED
test_schemas.py::test_schema_import_export[P0-multi-named-vectors] PASSED
test_schemas.py::test_all_schemas_exist PASSED
```

### Step 4: Run TypeScript Tests (Optional)

```bash
cd ../typescript

# Install dependencies
npm install

# Run tests
npm test
```

### Step 5: Compare Results

```bash
cd ../..

# Run comparison
python scripts/compare_results.py

# View report
cat test-results/comparisons/report.md
```

## Verify Installation

Check that everything is working:

```bash
# List generated schemas
ls -la schemas/*/config.json

# Check Weaviate is running
curl http://localhost:8080/v1/.well-known/ready

# Verify Python can import modules
cd schema-generator
source .venv/bin/activate
python -c "from src.schema_definitions import P0_SCHEMAS; print('✅ OK')"
```

## Common Issues

### Port 8080 already in use

```bash
# Find and stop the process
lsof -i :8080
kill -9 <PID>

# Or use a different port in docker-compose.yml
```

### Docker not starting

```bash
# Check Docker daemon
docker ps

# View logs
docker-compose -f docker/docker-compose.yml logs

# Clean start
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

### Python import errors

```bash
# Ensure virtual environment is activated
which python  # Should show .venv path

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Schemas not found

```bash
# Regenerate schemas
cd schema-generator
source .venv/bin/activate
python -m src.cli generate-all --output-dir ../schemas
```

## Next Steps

1. **Review the schemas**: Check `schemas/README.md` for schema details
2. **Run in CI**: Push to GitHub to trigger workflows
3. **Add more schemas**: Edit `schema-generator/src/schema_definitions.py`
4. **Add more clients**: Follow the pattern in `test-clients/`

## CLI Commands

### Schema Generator

```bash
# List available schemas
python -m src.cli list

# Generate all P0 schemas
python -m src.cli generate-all

# Generate specific schema
python -m src.cli generate-one P0-basic-text-only

# Get help
python -m src.cli --help
```

### Version Checker

```bash
cd version-tracking
python check_versions.py
```

### Docker Management

```bash
# Start Weaviate
docker-compose -f docker/docker-compose.yml up -d

# Stop Weaviate
docker-compose -f docker/docker-compose.yml down

# Stop and remove volumes (clean state)
docker-compose -f docker/docker-compose.yml down -v

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

## Development Workflow

1. Make changes to schema definitions
2. Regenerate schemas: `python -m src.cli generate-all`
3. Run tests: `./scripts/run_all_tests.sh`
4. Compare results: `python scripts/compare_results.py`
5. Commit if all pass

## Getting Help

- 📖 Read [README.md](README.md) for full documentation
- 🔍 Check [schemas/README.md](schemas/README.md) for schema details
- 📋 Review [IMPLEMENTATION.md](IMPLEMENTATION.md) for implementation details
- 🐛 Report issues on GitHub
