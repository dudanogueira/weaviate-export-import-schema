#!/usr/bin/env python3
"""Check for Weaviate client version updates."""

import json
import sys
from pathlib import Path
from datetime import datetime
import argparse
import requests


def check_pypi_version(package_name: str) -> str:
    """Check latest version on PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['info']['version']
    except Exception as e:
        print(f"Error checking PyPI for {package_name}: {e}", file=sys.stderr)
        return None


def check_npm_version(package_name: str) -> str:
    """Check latest version on npm."""
    url = f"https://registry.npmjs.org/{package_name}/latest"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['version']
    except Exception as e:
        print(f"Error checking npm for {package_name}: {e}", file=sys.stderr)
        return None


def check_versions(versions_file: Path) -> dict:
    """Check for version updates."""
    with open(versions_file) as f:
        versions = json.load(f)

    updates = {}

    for client, info in versions['clients'].items():
        package_manager = info['package_manager']
        package_name = info['package_name']
        current = info['current']

        print(f"Checking {client} ({package_name})...")

        if package_manager == 'pypi':
            latest = check_pypi_version(package_name)
        elif package_manager == 'npm':
            latest = check_npm_version(package_name)
        else:
            print(f"Unknown package manager: {package_manager}", file=sys.stderr)
            continue

        if not latest:
            continue

        update_available = latest != current

        updates[client] = {
            'current': current,
            'latest': latest,
            'update_available': update_available,
            'package_name': package_name,
            'package_manager': package_manager
        }

        if update_available:
            print(f"  ⚠️  Update available: {current} -> {latest}")
        else:
            print(f"  ✅ Up to date: {current}")

    return updates


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check for client version updates")
    parser.add_argument(
        '--versions-file',
        type=Path,
        default=Path(__file__).parent / 'versions.json',
        help='Path to versions.json file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for updated versions (default: update in place)'
    )

    args = parser.parse_args()

    versions_file = args.versions_file
    output_file = args.output or versions_file

    if not versions_file.exists():
        print(f"ERROR: Versions file not found: {versions_file}", file=sys.stderr)
        return 1

    updates = check_versions(versions_file)

    # Update versions file
    updated_data = {
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'clients': updates
    }

    with open(output_file, 'w') as f:
        json.dump(updated_data, f, indent=2)

    print(f"\nVersions updated in: {output_file}")

    # Check if any updates are available
    has_updates = any(info['update_available'] for info in updates.values())

    if has_updates:
        print("\n⚠️  Updates available!")
        return 0  # Success but with updates
    else:
        print("\n✅ All clients are up to date")
        return 0


if __name__ == '__main__':
    sys.exit(main())
