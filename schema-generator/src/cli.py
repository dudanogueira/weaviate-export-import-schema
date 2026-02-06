"""CLI for generating baseline schemas."""

import argparse
import logging
import sys
from pathlib import Path

from .generator import SchemaGenerator
from .schema_definitions import (
    get_schema_definition,
    list_schemas,
    get_p0_schemas,
    SCHEMA_DEFINITIONS
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_all_command(args):
    """Generate all schemas of a specific priority."""
    output_dir = Path(args.output_dir).resolve()
    logger.info(f"Generating all {args.priority} schemas to: {output_dir}")

    generator = SchemaGenerator(weaviate_url=args.weaviate_url)

    try:
        generator.connect()

        schemas = list_schemas(priority=args.priority)
        logger.info(f"Found {len(schemas)} schemas to generate")

        for definition in schemas:
            try:
                schema_path = generator.generate_schema(
                    definition=definition,
                    output_dir=output_dir,
                    cleanup=not args.no_cleanup
                )
                logger.info(f"✓ Generated: {definition.name}")
            except Exception as e:
                logger.error(f"✗ Failed to generate {definition.name}: {e}")
                if not args.continue_on_error:
                    raise

        logger.info(f"Successfully generated {len(schemas)} schemas")

    finally:
        generator.disconnect()


def generate_one_command(args):
    """Generate a specific schema by name."""
    output_dir = Path(args.output_dir).resolve()
    schema_name = args.schema_name

    logger.info(f"Generating schema: {schema_name}")

    try:
        definition = get_schema_definition(schema_name)
    except ValueError as e:
        logger.error(str(e))
        return 1

    generator = SchemaGenerator(weaviate_url=args.weaviate_url)

    try:
        generator.connect()

        schema_path = generator.generate_schema(
            definition=definition,
            output_dir=output_dir,
            cleanup=not args.no_cleanup
        )

        logger.info(f"✓ Generated: {schema_name} -> {schema_path}")

    finally:
        generator.disconnect()


def list_command(args):
    """List all available schema definitions."""
    schemas = list_schemas(priority=args.priority)

    print(f"\nAvailable schemas ({len(schemas)}):\n")

    for schema in schemas:
        print(f"  [{schema.priority}] {schema.name}")
        print(f"      {schema.description}")
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Weaviate Schema Generator - Generate baseline test schemas"
    )

    parser.add_argument(
        '--weaviate-url',
        default='http://localhost:8080',
        help='Weaviate instance URL (default: http://localhost:8080)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # generate-all command
    generate_all_parser = subparsers.add_parser(
        'generate-all',
        help='Generate all schemas of a specific priority'
    )
    generate_all_parser.add_argument(
        '--output-dir',
        default='../schemas',
        help='Output directory for schemas (default: ../schemas)'
    )
    generate_all_parser.add_argument(
        '--priority',
        default='P0',
        help='Schema priority level to generate (default: P0)'
    )
    generate_all_parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Do not delete collections after export'
    )
    generate_all_parser.add_argument(
        '--continue-on-error',
        action='store_true',
        help='Continue generating other schemas if one fails'
    )
    generate_all_parser.set_defaults(func=generate_all_command)

    # generate-one command
    generate_one_parser = subparsers.add_parser(
        'generate-one',
        help='Generate a specific schema by name'
    )
    generate_one_parser.add_argument(
        'schema_name',
        help='Name of the schema to generate'
    )
    generate_one_parser.add_argument(
        '--output-dir',
        default='../schemas',
        help='Output directory for schema (default: ../schemas)'
    )
    generate_one_parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Do not delete collection after export'
    )
    generate_one_parser.set_defaults(func=generate_one_command)

    # list command
    list_parser = subparsers.add_parser(
        'list',
        help='List all available schema definitions'
    )
    list_parser.add_argument(
        '--priority',
        help='Filter by priority level (P0, P1, P2)'
    )
    list_parser.set_defaults(func=list_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        result = args.func(args)
        return result if result is not None else 0
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
