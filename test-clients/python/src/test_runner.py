"""Test runner for importing and exporting Weaviate schemas."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRunner:
    """Runs import/export tests for Weaviate schemas."""

    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        """Initialize the test runner.

        Args:
            weaviate_url: URL of the Weaviate instance
        """
        self.weaviate_url = weaviate_url
        self.client: Optional[weaviate.WeaviateClient] = None

    def connect(self):
        """Connect to Weaviate instance."""
        try:
            self.client = weaviate.connect_to_local(host="localhost", port=8080)
            logger.info(f"Connected to Weaviate at {self.weaviate_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise

    def disconnect(self):
        """Disconnect from Weaviate instance."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from Weaviate")

    def load_schema(self, schema_path: Path) -> Dict[str, Any]:
        """Load a schema from JSON file.

        Args:
            schema_path: Path to schema JSON file

        Returns:
            Schema dictionary
        """
        with open(schema_path) as f:
            schema = json.load(f)
        logger.info(f"Loaded schema from: {schema_path}")
        return schema

    def import_schema(self, schema: Dict[str, Any]) -> str:
        """Import a schema into Weaviate by creating a collection.

        Args:
            schema: Schema dictionary to import

        Returns:
            Name of the created collection
        """
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")

        collection_name = schema.get('name')
        if not collection_name:
            raise ValueError("Schema missing 'name' field")

        # Delete if exists
        if self.client.collections.exists(collection_name):
            logger.info(f"Deleting existing collection: {collection_name}")
            self.client.collections.delete(collection_name)

        logger.info(f"Importing collection: {collection_name}")

        # Build properties
        properties = []
        for prop in schema.get('properties', []):
            data_type_str = prop['dataType'][0].upper()
            data_type = getattr(DataType, data_type_str)

            properties.append(
                Property(
                    name=prop['name'],
                    data_type=data_type,
                    description=prop.get('description')
                )
            )

        # Handle vector configuration
        vector_config = None

        if 'vectorConfig' in schema and schema['vectorConfig']:
            # Multi-named vectors or single named vector
            vector_configs = {}

            for vector_name, vector_def in schema['vectorConfig'].items():
                distance_str = vector_def.get('vectorIndexConfig', {}).get('distance', 'cosine')
                distance = getattr(VectorDistances, distance_str.upper())

                vector_configs[vector_name] = Configure.NamedVectors.none(
                    name=vector_name,
                    vector_index_config=Configure.VectorIndex.hnsw(
                        distance_metric=distance
                    )
                )

            # For multiple named vectors, pass the list of configs directly
            vector_config = list(vector_configs.values())

        # Create collection
        try:
            if vector_config:
                collection = self.client.collections.create(
                    name=collection_name,
                    description=schema.get('description'),
                    properties=properties,
                    vectorizer_config=vector_config,
                    replication_config=Configure.replication(
                        factor=schema.get('replicationConfig', {}).get('factor', 1)
                    ),
                    inverted_index_config=Configure.inverted_index(
                        index_null_state=schema.get('invertedIndexConfig', {}).get('indexNullState', False),
                        index_property_length=schema.get('invertedIndexConfig', {}).get('indexPropertyLength', False),
                        index_timestamps=schema.get('invertedIndexConfig', {}).get('indexTimestamps', False)
                    )
                )
            else:
                # Collection without vectors
                collection = self.client.collections.create(
                    name=collection_name,
                    description=schema.get('description'),
                    properties=properties,
                    replication_config=Configure.replication(
                        factor=schema.get('replicationConfig', {}).get('factor', 1)
                    ),
                    inverted_index_config=Configure.inverted_index(
                        index_null_state=schema.get('invertedIndexConfig', {}).get('indexNullState', False),
                        index_property_length=schema.get('invertedIndexConfig', {}).get('indexPropertyLength', False),
                        index_timestamps=schema.get('invertedIndexConfig', {}).get('indexTimestamps', False)
                    )
                )

            logger.info(f"Successfully imported collection: {collection_name}")
            return collection_name

        except Exception as e:
            logger.error(f"Failed to import collection: {e}")
            raise

    def export_schema(self, collection_name: str) -> Dict[str, Any]:
        """Export a collection's schema configuration.

        Args:
            collection_name: Name of the collection to export

        Returns:
            Dictionary containing the collection configuration
        """
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")

        try:
            collection = self.client.collections.get(collection_name)
            config = collection.config.get()
            exported = config.to_dict()

            logger.info(f"Exported schema for collection: {collection_name}")
            return exported

        except Exception as e:
            logger.error(f"Failed to export schema: {e}")
            raise

    def save_schema(self, schema: Dict[str, Any], output_path: Path):
        """Save schema to JSON file.

        Args:
            schema: Schema dictionary to save
            output_path: Path to save the JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=2)

        logger.info(f"Saved schema to: {output_path}")

    def cleanup(self, collection_name: str):
        """Delete a collection from Weaviate.

        Args:
            collection_name: Name of the collection to delete
        """
        if not self.client:
            return

        try:
            if self.client.collections.exists(collection_name):
                self.client.collections.delete(collection_name)
                logger.info(f"Cleaned up collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup collection: {e}")

    def run_test(
        self,
        baseline_path: Path,
        output_dir: Path,
        schema_name: str
    ) -> Dict[str, Any]:
        """Run a complete import/export test.

        Args:
            baseline_path: Path to baseline schema JSON
            output_dir: Directory to save exported schema
            schema_name: Name of the schema being tested

        Returns:
            Test result dictionary
        """
        result = {
            'schema_name': schema_name,
            'success': False,
            'error': None,
            'exported_path': None
        }

        try:
            # Load baseline
            baseline = self.load_schema(baseline_path)

            # Import schema
            collection_name = self.import_schema(baseline)

            # Export schema
            exported = self.export_schema(collection_name)

            # Save exported schema
            output_path = output_dir / "python" / schema_name / "config.json"
            self.save_schema(exported, output_path)

            result['success'] = True
            result['exported_path'] = str(output_path)

            # Cleanup
            self.cleanup(collection_name)

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Test failed for {schema_name}: {e}")

        return result
