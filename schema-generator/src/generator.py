"""Schema generator - creates and exports baseline schemas from definitions."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import weaviate

from .schema_definitions import SchemaDefinition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaGenerator:
    """Generates baseline schemas from definitions and exports them to JSON."""

    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        """Initialize the schema generator.

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

    def create_collection_from_definition(self, definition: SchemaDefinition) -> str:
        """Create a collection in Weaviate from a schema definition.

        Args:
            definition: Schema definition to create

        Returns:
            Collection name that was created
        """
        if not self.client:
            raise RuntimeError("Not connected to Weaviate. Call connect() first.")

        config = definition.collection_config
        collection_name = config["name"]

        # Delete collection if it already exists
        if self.client.collections.exists(collection_name):
            logger.info(f"Deleting existing collection: {collection_name}")
            self.client.collections.delete(collection_name)

        logger.info(f"Creating collection: {collection_name}")

        # Create collection directly from dictionary
        try:
            self.client.collections.create_from_dict(config)
            logger.info(f"Successfully created collection: {collection_name}")
            return collection_name

        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise

    def export_collection_schema(self, collection_name: str) -> Dict[str, Any]:
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

            # Convert to dictionary
            exported = config.to_dict()

            logger.info(f"Exported schema for collection: {collection_name}")
            return exported

        except Exception as e:
            logger.error(f"Failed to export schema for {collection_name}: {e}")
            raise

    def save_schema_to_file(self, schema: Dict[str, Any], output_path: Path):
        """Save schema dictionary to JSON file.

        Args:
            schema: Schema dictionary to save
            output_path: Path to save the JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=2)

        logger.info(f"Saved schema to: {output_path}")

    def cleanup_collection(self, collection_name: str):
        """Delete a collection from Weaviate.

        Args:
            collection_name: Name of the collection to delete
        """
        if not self.client:
            return

        try:
            if self.client.collections.exists(collection_name):
                self.client.collections.delete(collection_name)
                logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection_name}: {e}")

    def generate_schema(
        self,
        definition: SchemaDefinition,
        output_dir: Path,
        cleanup: bool = True
    ) -> Path:
        """Generate a baseline schema from a definition.

        Args:
            definition: Schema definition to generate from
            output_dir: Directory to save the schema JSON
            cleanup: Whether to delete the collection after export

        Returns:
            Path to the generated schema file
        """
        logger.info(f"Generating schema: {definition.name}")

        # Create collection
        collection_name = self.create_collection_from_definition(definition)

        try:
            # Export schema
            schema = self.export_collection_schema(collection_name)

            # Save to file
            schema_dir = output_dir / definition.name
            schema_path = schema_dir / "config.json"
            self.save_schema_to_file(schema, schema_path)

            # Save metadata
            metadata = {
                "name": definition.name,
                "description": definition.description,
                "priority": definition.priority,
                "collection_name": collection_name
            }
            metadata_path = schema_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Successfully generated schema: {definition.name}")
            return schema_path

        finally:
            # Cleanup
            if cleanup:
                self.cleanup_collection(collection_name)
