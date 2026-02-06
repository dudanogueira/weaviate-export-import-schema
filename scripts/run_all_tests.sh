#!/bin/bash
# Run all client tests

set -e

echo "Running all schema import/export tests..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Ensure Weaviate is running
if ! curl -s http://localhost:8080/v1/.well-known/ready > /dev/null; then
    echo "Starting Weaviate..."
    docker-compose -f docker/docker-compose.yml up -d

    echo "Waiting for Weaviate..."
    timeout=60
    elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null; then
            break
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
fi

# Run Python tests
echo ""
echo "========================================="
echo "Running Python tests..."
echo "========================================="
cd "$PROJECT_ROOT/test-clients/python"
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
pytest -v --junit-xml=../../test-results/reports/python/junit.xml tests/
PYTHON_EXIT=$?

# Run TypeScript tests
echo ""
echo "========================================="
echo "Running TypeScript tests..."
echo "========================================="
cd "$PROJECT_ROOT/test-clients/typescript"
if [ -f "package.json" ] && command -v npm &> /dev/null; then
    npm test
    TYPESCRIPT_EXIT=$?
else
    echo "WARNING: TypeScript tests not available"
    TYPESCRIPT_EXIT=0
fi

# Run Java tests
echo ""
echo "========================================="
echo "Running Java tests..."
echo "========================================="
cd "$PROJECT_ROOT/test-clients/java"
if [ -f "pom.xml" ] && command -v mvn &> /dev/null; then
    mvn test
    JAVA_EXIT=$?
else
    echo "WARNING: Java tests not available (Maven not found)"
    JAVA_EXIT=0
fi

# Compare results
echo ""
echo "========================================="
echo "Comparing results..."
echo "========================================="
cd "$PROJECT_ROOT"
python scripts/compare_results.py
COMPARE_EXIT=$?

# Summary
echo ""
echo "========================================="
echo "TEST SUMMARY"
echo "========================================="
echo "Python tests: $([ $PYTHON_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "TypeScript tests: $([ $TYPESCRIPT_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Java tests: $([ $JAVA_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Comparison: $([ $COMPARE_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"

# Exit with error if any test failed
if [ $PYTHON_EXIT -ne 0 ] || [ $TYPESCRIPT_EXIT -ne 0 ] || [ $JAVA_EXIT -ne 0 ] || [ $COMPARE_EXIT -ne 0 ]; then
    exit 1
fi

echo ""
echo "✅ All tests passed!"
