#!/bin/bash
# Setup local development environment

set -e

echo "Setting up Weaviate Schema Export/Import Testing Framework..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Start Weaviate
echo ""
echo "Starting Weaviate..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for Weaviate to be ready
echo "Waiting for Weaviate to be ready..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null; then
        echo "Weaviate is ready!"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ $elapsed -ge $timeout ]; then
    echo "ERROR: Weaviate failed to start within ${timeout} seconds"
    exit 1
fi

# Setup Python environment
echo ""
echo "Setting up Python environment..."
cd "$PROJECT_ROOT/schema-generator"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate baseline schemas
echo ""
echo "Generating baseline schemas..."
python -m src.cli generate-all --output-dir ../schemas

# Setup Python test client
echo ""
echo "Setting up Python test client..."
cd "$PROJECT_ROOT/test-clients/python"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Setup TypeScript test client
echo ""
echo "Setting up TypeScript test client..."
cd "$PROJECT_ROOT/test-clients/typescript"
if command -v npm &> /dev/null; then
    npm install
    echo "TypeScript client setup complete"
else
    echo "WARNING: npm not found. Skipping TypeScript setup."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run tests:"
echo "  Python:     cd test-clients/python && source .venv/bin/activate && pytest -v"
echo "  TypeScript: cd test-clients/typescript && npm test"
echo ""
echo "To compare results:"
echo "  python scripts/compare_results.py"
