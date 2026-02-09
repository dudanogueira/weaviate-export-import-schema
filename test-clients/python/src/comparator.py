"""Schema comparison engine for validating import/export consistency."""

import json
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path
from deepdiff import DeepDiff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaComparator:
    """Compares two schema configurations and reports differences."""

    # Fields to ignore during comparison (timestamps, internal IDs, etc.)
    IGNORE_FIELDS = [
        "root['creationTimeUnix']",
        "root['lastUpdateTimeUnix']",
    ]

    # Fields to normalize (apply defaults if missing)
    DEFAULT_VALUES = {
        "replicationConfig.factor": 1,
        "invertedIndexConfig.indexNullState": False,
        "invertedIndexConfig.indexPropertyLength": False,
        "invertedIndexConfig.indexTimestamps": False,
    }

    def __init__(self):
        """Initialize the comparator."""
        pass

    def normalize_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a schema by removing internal fields and applying defaults.

        Args:
            schema: Schema dictionary to normalize

        Returns:
            Normalized schema dictionary
        """
        normalized = json.loads(json.dumps(schema))  # Deep copy

        # Remove timestamp fields
        normalized.pop('creationTimeUnix', None)
        normalized.pop('lastUpdateTimeUnix', None)

        # Normalize 'class' to 'name' for v3/v4 compatibility
        # Both fields refer to the collection name
        if 'class' in normalized and 'name' not in normalized:
            normalized['name'] = normalized.pop('class')
        elif 'class' in normalized and 'name' in normalized:
            # If both exist, remove 'class' and keep 'name'
            normalized.pop('class')

        # Sort properties by name for consistent comparison
        if 'properties' in normalized:
            normalized['properties'] = sorted(
                normalized['properties'],
                key=lambda p: p.get('name', '')
            )

        # Sort vectorConfig keys if present
        if 'vectorConfig' in normalized:
            normalized['vectorConfig'] = dict(sorted(normalized['vectorConfig'].items()))

        return normalized

    def compare_schemas(
        self,
        baseline: Dict[str, Any],
        exported: Dict[str, Any],
        schema_name: str = "schema"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Compare two schemas and report differences.

        Args:
            baseline: Baseline schema (source of truth)
            exported: Exported schema to compare
            schema_name: Name of schema for reporting

        Returns:
            Tuple of (is_identical, differences_dict)
        """
        logger.info(f"Comparing schemas for: {schema_name}")

        # Normalize both schemas
        norm_baseline = self.normalize_schema(baseline)
        norm_exported = self.normalize_schema(exported)

        # Deep comparison
        diff = DeepDiff(
            norm_baseline,
            norm_exported,
            ignore_order=True,
            report_repetition=True,
            verbose_level=2
        )

        if not diff:
            logger.info(f"✓ Schemas match perfectly: {schema_name}")
            return True, {}

        logger.warning(f"✗ Schemas differ: {schema_name}")
        logger.debug(f"Differences: {diff}")

        return False, diff.to_dict()

    def generate_comparison_report(
        self,
        comparisons: List[Dict[str, Any]],
        output_path: Path = None
    ) -> str:
        """Generate a human-readable comparison report.

        Args:
            comparisons: List of comparison results
            output_path: Optional path to save report

        Returns:
            Report as markdown string
        """
        total = len(comparisons)
        passed = sum(1 for c in comparisons if c['match'])
        failed = total - passed

        report = []
        report.append("# Schema Comparison Report\n")
        report.append("## Summary\n")
        report.append(f"- Total Comparisons: {total}")
        report.append(f"- Passed: {passed} ✅")
        report.append(f"- Failed: {failed} ❌")
        report.append(f"- Pass Rate: {(passed/total*100):.1f}%\n")

        if failed > 0:
            report.append("## Failures\n")
            for comp in comparisons:
                if not comp['match']:
                    report.append(f"### {comp['schema_name']}\n")
                    report.append(f"**Differences:**\n")
                    report.append(f"```json\n{json.dumps(comp['differences'], indent=2)}\n```\n")

        report_text = "\n".join(report)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to: {output_path}")

        return report_text

    def compare_files(
        self,
        baseline_path: Path,
        exported_path: Path,
        schema_name: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Compare two schema JSON files.

        Args:
            baseline_path: Path to baseline schema JSON
            exported_path: Path to exported schema JSON
            schema_name: Name of schema for reporting

        Returns:
            Tuple of (is_identical, differences_dict)
        """
        if schema_name is None:
            schema_name = baseline_path.parent.name

        with open(baseline_path) as f:
            baseline = json.load(f)

        with open(exported_path) as f:
            exported = json.load(f)

        return self.compare_schemas(baseline, exported, schema_name)
