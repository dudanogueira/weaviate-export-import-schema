# Getting Started Checklist

Follow this checklist to get the framework up and running.

## ✅ Prerequisites

- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed (optional, for TypeScript tests)
- [ ] Git installed

Verify installations:
```bash
docker --version && docker-compose --version && python3 --version && node --version
```

## ✅ Initial Setup

### Option A: Automated (Recommended)

- [ ] Navigate to project directory
- [ ] Make scripts executable: `chmod +x scripts/*.sh`
- [ ] Run setup: `./scripts/setup_local_env.sh`
- [ ] Wait for completion (may take 2-3 minutes)

### Option B: Manual

- [ ] Start Weaviate: `docker-compose -f docker/docker-compose.yml up -d`
- [ ] Wait for Weaviate to be ready: `curl http://localhost:8080/v1/.well-known/ready`
- [ ] Setup Python schema generator:
  ```bash
  cd schema-generator
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- [ ] Generate baseline schemas:
  ```bash
  python -m src.cli generate-all --output-dir ../schemas
  ```
- [ ] Verify schemas created: `ls -la ../schemas/*/config.json`

## ✅ Verify Installation

- [ ] Check Weaviate is running:
  ```bash
  curl http://localhost:8080/v1/.well-known/ready
  # Expected: {"status":"ok"}
  ```

- [ ] Check schemas generated:
  ```bash
  ls -la schemas/
  # Expected: 3 directories (P0-basic-text-only, P0-single-named-vector, P0-multi-named-vectors)
  ```

- [ ] Test schema generator CLI:
  ```bash
  cd schema-generator
  source .venv/bin/activate
  python -m src.cli list
  # Expected: List of 3 schemas
  ```

## ✅ Run Your First Test

### Python Tests

- [ ] Navigate to Python test client: `cd test-clients/python`
- [ ] Setup virtual environment:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- [ ] Run tests: `pytest -v tests/`
- [ ] Check results: All 4 tests should pass ✅

### TypeScript Tests (Optional)

- [ ] Navigate to TypeScript test client: `cd test-clients/typescript`
- [ ] Install dependencies: `npm install`
- [ ] Run tests: `npm test`
- [ ] Check results: All 4 tests should pass ✅

## ✅ Compare Results

- [ ] Navigate to project root: `cd ../..`
- [ ] Run comparison: `python scripts/compare_results.py`
- [ ] View report: `cat test-results/comparisons/report.md`
- [ ] Expected: 100% pass rate ✅

## ✅ Understand the Project

- [ ] Read [README.md](README.md) for overview
- [ ] Review [QUICKSTART.md](QUICKSTART.md) for quick reference
- [ ] Check [schemas/README.md](schemas/README.md) for schema details
- [ ] Explore [IMPLEMENTATION.md](IMPLEMENTATION.md) for technical details

## ✅ Try CLI Commands

### Schema Generator

- [ ] List schemas: `python -m src.cli list`
- [ ] Generate specific schema: `python -m src.cli generate-one P0-basic-text-only`
- [ ] Get help: `python -m src.cli --help`

### Version Checker

- [ ] Check versions: `python version-tracking/check_versions.py`
- [ ] Review output for any available updates

## ✅ Run Full Test Suite

- [ ] Execute: `./scripts/run_all_tests.sh`
- [ ] Wait for completion (may take 1-2 minutes)
- [ ] Review summary output
- [ ] Check detailed reports in `test-results/`

## ✅ Explore Generated Files

- [ ] **Baseline Schemas**: `schemas/P0-*/config.json`
- [ ] **Exported Schemas**: `test-results/exported-schemas/*/P0-*/config.json`
- [ ] **Test Reports**: `test-results/reports/*/junit.xml`
- [ ] **Comparison Report**: `test-results/comparisons/report.md`
- [ ] **JSON Summary**: `test-results/comparisons/summary.json`

## ✅ Development Workflow

### Add a New Schema

- [ ] Open `schema-generator/src/schema_definitions.py`
- [ ] Add new schema definition
- [ ] Regenerate: `python -m src.cli generate-all`
- [ ] Commit new schema files
- [ ] Run tests to validate

### Modify Existing Schema

- [ ] Update definition in `schema_definitions.py`
- [ ] Regenerate schemas
- [ ] Run tests to see impact
- [ ] Update documentation if needed

## ✅ CI/CD Setup

- [ ] Push code to GitHub
- [ ] Enable GitHub Actions
- [ ] Create a test PR to trigger workflows
- [ ] Review workflow runs in Actions tab
- [ ] Check test results and artifacts

## ✅ Troubleshooting

If you encounter issues:

- [ ] Check Docker is running: `docker ps`
- [ ] View Weaviate logs: `docker-compose -f docker/docker-compose.yml logs`
- [ ] Restart Weaviate: `docker-compose -f docker/docker-compose.yml restart`
- [ ] Clean restart: `docker-compose -f docker/docker-compose.yml down -v && docker-compose -f docker/docker-compose.yml up -d`
- [ ] Check Python virtual environment is activated: `which python`
- [ ] Reinstall dependencies if needed

## ✅ Next Steps

### For Testing
- [ ] Run tests regularly to catch regressions
- [ ] Add more test schemas as needed
- [ ] Monitor test results in CI/CD

### For Development
- [ ] Add more client implementations (Go, C#, Java)
- [ ] Extend to P1/P2 schemas
- [ ] Implement performance benchmarking
- [ ] Add custom comparison rules

### For Production
- [ ] Setup scheduled CI runs
- [ ] Configure notifications
- [ ] Create compatibility matrix dashboard
- [ ] Implement automated version updates

## 🎉 You're Ready!

Once all checkboxes are complete, you have:

✅ A working local development environment
✅ Generated baseline schemas
✅ Passing tests for Python and TypeScript clients
✅ Comparison reports showing consistency
✅ Understanding of the project structure
✅ Ability to add new schemas and clients

## 📚 Quick Reference

| Task | Command |
|------|---------|
| Start Weaviate | `docker-compose -f docker/docker-compose.yml up -d` |
| Generate schemas | `cd schema-generator && python -m src.cli generate-all` |
| Run Python tests | `cd test-clients/python && pytest -v` |
| Run TypeScript tests | `cd test-clients/typescript && npm test` |
| Compare results | `python scripts/compare_results.py` |
| Run all tests | `./scripts/run_all_tests.sh` |
| Check versions | `python version-tracking/check_versions.py` |
| Stop Weaviate | `docker-compose -f docker/docker-compose.yml down` |

## 🆘 Getting Help

- Review documentation files in project root
- Check troubleshooting section in README.md
- Examine test output for specific error messages
- Review GitHub Actions logs for CI issues

---

**Happy Testing! 🚀**
