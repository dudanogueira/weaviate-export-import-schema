"""Pytest tests for schema import/export validation."""

import json
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_runner import TestRunner
from comparator import SchemaComparator


# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
RESULTS_DIR = PROJECT_ROOT / "test-results"


# P0 schema names
P0_SCHEMAS = [
    "P0-basic-text-only",
    "P0-single-named-vector",
    "P0-multi-named-vectors",
]


@pytest.fixture(scope="session")
def weaviate_client():
    """Create a Weaviate client for the test session."""
    runner = TestRunner()
    runner.connect()
    yield runner
    runner.disconnect()


@pytest.fixture(scope="function")
def cleanup_collections(weaviate_client):
    """Ensure clean state between tests."""
    yield
    # Cleanup happens in test_runner.run_test()


@pytest.mark.parametrize("schema_name", P0_SCHEMAS)
def test_schema_import_export(schema_name, weaviate_client, cleanup_collections):
    """Test that a schema can be imported and re-exported identically.

    This test:
    1. Loads the baseline schema JSON
    2. Imports it into Weaviate (creates collection)
    3. Exports the collection configuration
    4. Compares exported with baseline (after normalization)
    """
    # Paths
    baseline_path = SCHEMAS_DIR / schema_name / "config.json"
    output_dir = RESULTS_DIR / "exported-schemas"

    # Verify baseline exists
    assert baseline_path.exists(), f"Baseline schema not found: {baseline_path}"

    # Run test
    result = weaviate_client.run_test(
        baseline_path=baseline_path,
        output_dir=output_dir,
        schema_name=schema_name
    )

    # Verify test succeeded
    assert result['success'], f"Import/export failed: {result.get('error')}"
    assert result['exported_path'], "No exported path returned"

    # Load baseline and exported
    with open(baseline_path) as f:
        baseline = json.load(f)

    with open(result['exported_path']) as f:
        exported = json.load(f)

    # Compare schemas
    comparator = SchemaComparator()
    match, differences = comparator.compare_schemas(baseline, exported, schema_name)

    # Assert schemas match
    assert match, f"Schema mismatch for {schema_name}:\n{json.dumps(differences, indent=2)}"


def test_all_schemas_exist():
    """Verify that all P0 baseline schemas exist."""
    missing = []
    for schema_name in P0_SCHEMAS:
        schema_path = SCHEMAS_DIR / schema_name / "config.json"
        if not schema_path.exists():
            missing.append(schema_name)

    assert not missing, f"Missing baseline schemas: {missing}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
