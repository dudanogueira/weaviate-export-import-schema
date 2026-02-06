#!/usr/bin/env python3
"""Cross-client schema comparison script."""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Add test-clients/python to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "test-clients" / "python" / "src"))

from comparator import SchemaComparator


def find_exported_schemas(results_dir: Path) -> Dict[str, Dict[str, Path]]:
    """Find all exported schemas organized by client and schema name.

    Returns:
        Dict with structure: {client_name: {schema_name: schema_path}}
    """
    exported_dir = results_dir / "exported-schemas"
    schemas = {}

    if not exported_dir.exists():
        return schemas

    for client_dir in exported_dir.iterdir():
        if not client_dir.is_dir():
            continue

        client_name = client_dir.name
        schemas[client_name] = {}

        for schema_dir in client_dir.iterdir():
            if not schema_dir.is_dir():
                continue

            schema_name = schema_dir.name
            config_file = schema_dir / "config.json"

            if config_file.exists():
                schemas[client_name][schema_name] = config_file

    return schemas


def load_baseline_schemas(schemas_dir: Path) -> Dict[str, Path]:
    """Load all baseline schema paths.

    Returns:
        Dict with structure: {schema_name: schema_path}
    """
    baselines = {}

    for schema_dir in schemas_dir.iterdir():
        if not schema_dir.is_dir():
            continue

        config_file = schema_dir / "config.json"
        if config_file.exists():
            baselines[schema_dir.name] = config_file

    return baselines


def compare_all_schemas(
    baselines: Dict[str, Path],
    exported: Dict[str, Dict[str, Path]],
    comparator: SchemaComparator
) -> List[Dict[str, Any]]:
    """Compare all exported schemas against baselines.

    Returns:
        List of comparison results
    """
    results = []

    for schema_name, baseline_path in baselines.items():
        with open(baseline_path) as f:
            baseline = json.load(f)

        for client_name, client_schemas in exported.items():
            if schema_name not in client_schemas:
                results.append({
                    'schema_name': schema_name,
                    'client': client_name,
                    'match': False,
                    'error': 'Schema not exported by client',
                    'differences': {}
                })
                continue

            exported_path = client_schemas[schema_name]
            with open(exported_path) as f:
                exported_schema = json.load(f)

            match, differences = comparator.compare_schemas(
                baseline,
                exported_schema,
                f"{client_name}/{schema_name}"
            )

            results.append({
                'schema_name': schema_name,
                'client': client_name,
                'match': match,
                'differences': differences,
                'baseline_path': str(baseline_path),
                'exported_path': str(exported_path)
            })

    return results


def generate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics."""
    total = len(results)
    passed = sum(1 for r in results if r['match'])
    failed = total - passed

    # Per-client stats
    clients = {}
    for result in results:
        client = result['client']
        if client not in clients:
            clients[client] = {'total': 0, 'passed': 0, 'failed': 0}

        clients[client]['total'] += 1
        if result['match']:
            clients[client]['passed'] += 1
        else:
            clients[client]['failed'] += 1

    # Per-schema stats
    schemas = {}
    for result in results:
        schema = result['schema_name']
        if schema not in schemas:
            schemas[schema] = {'total': 0, 'passed': 0, 'failed': 0}

        schemas[schema]['total'] += 1
        if result['match']:
            schemas[schema]['passed'] += 1
        else:
            schemas[schema]['failed'] += 1

    return {
        'total': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': (passed / total * 100) if total > 0 else 0,
        'clients': clients,
        'schemas': schemas
    }


def generate_markdown_report(
    summary: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> str:
    """Generate markdown report."""
    lines = []

    lines.append("# Schema Comparison Report\n")
    lines.append("## Summary\n")
    lines.append(f"- Total Tests: {summary['total']}")
    lines.append(f"- Passed: {summary['passed']} ✅")
    lines.append(f"- Failed: {summary['failed']} ❌")
    lines.append(f"- Pass Rate: {summary['pass_rate']:.1f}%\n")

    lines.append("## Results by Client\n")
    for client, stats in summary['clients'].items():
        pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status = "✅" if stats['failed'] == 0 else "❌"
        lines.append(f"### {client} {status}")
        lines.append(f"- Total: {stats['total']}")
        lines.append(f"- Passed: {stats['passed']}")
        lines.append(f"- Failed: {stats['failed']}")
        lines.append(f"- Pass Rate: {pass_rate:.1f}%\n")

    lines.append("## Results by Schema\n")
    for schema, stats in summary['schemas'].items():
        pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status = "✅" if stats['failed'] == 0 else "❌"
        lines.append(f"### {schema} {status}")
        lines.append(f"- Total Clients: {stats['total']}")
        lines.append(f"- Passed: {stats['passed']}")
        lines.append(f"- Failed: {stats['failed']}")
        lines.append(f"- Pass Rate: {pass_rate:.1f}%\n")

    # Show failures in detail
    failures = [r for r in results if not r['match']]
    if failures:
        lines.append("## Detailed Failures\n")
        for failure in failures:
            lines.append(f"### {failure['client']} / {failure['schema_name']}\n")

            if 'error' in failure:
                lines.append(f"**Error:** {failure['error']}\n")
            else:
                lines.append("**Differences:**\n")
                lines.append(f"```json\n{json.dumps(failure['differences'], indent=2)}\n```\n")
    else:
        lines.append("## Cross-Language Consistency\n")
        lines.append("✅ All clients produced identical schemas for all test cases.\n")

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare exported schemas across clients"
    )
    parser.add_argument(
        '--results-dir',
        type=Path,
        default=PROJECT_ROOT / "test-results",
        help='Test results directory'
    )
    parser.add_argument(
        '--schemas-dir',
        type=Path,
        default=PROJECT_ROOT / "schemas",
        help='Baseline schemas directory'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for comparison report (default: test-results/comparisons/report.md)'
    )

    args = parser.parse_args()

    results_dir = args.results_dir
    schemas_dir = args.schemas_dir
    output_path = args.output or (results_dir / "comparisons" / "report.md")

    print("Loading schemas...")
    baselines = load_baseline_schemas(schemas_dir)
    exported = find_exported_schemas(results_dir)

    print(f"Found {len(baselines)} baseline schemas")
    print(f"Found {len(exported)} clients with exported schemas")

    if not baselines:
        print("ERROR: No baseline schemas found")
        return 1

    if not exported:
        print("ERROR: No exported schemas found")
        return 1

    print("\nComparing schemas...")
    comparator = SchemaComparator()
    results = compare_all_schemas(baselines, exported, comparator)

    print("\nGenerating report...")
    summary = generate_summary(results)
    report = generate_markdown_report(summary, results)

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)
    print(f"Report saved to: {output_path}")

    # Save JSON summary
    json_path = output_path.parent / "summary.json"
    with open(json_path, 'w') as f:
        json.dump({
            'summary': summary,
            'results': results
        }, f, indent=2)
    print(f"JSON summary saved to: {json_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {summary['total']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")

    return 0 if summary['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
