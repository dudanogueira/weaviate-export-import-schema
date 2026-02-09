"""Schema definitions - source of truth for all test schemas.

Priority Levels:
- P0: Basic schemas testing fundamental import/export functionality
- P1: Intermediate schemas (future)
- P2: Advanced schemas (future)
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class SchemaDefinition:
    """Represents a complete schema definition for testing."""
    name: str
    description: str
    priority: str
    collection_config: Dict[str, Any]


# P0 Schemas: Basic functionality tests

P0_BASIC_TEXT_ONLY = SchemaDefinition(
    name="P0-basic-text-only",
    description="Simple collection with text properties only, no vectors",
    priority="P0",
    collection_config={
        "name": "BasicTextOnly",
        "description": "Test collection with text properties and no vector configuration",
        "properties": [
            {
                "name": "title",
                "dataType": ["text"],
                "description": "Title of the document"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Main content of the document"
            },
            {
                "name": "category",
                "dataType": ["text"],
                "description": "Category classification"
            }
        ],
        "vectorConfig": {
            "default": {
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": {
                    "ef": -1,
                    "efConstruction": 128,
                    "maxConnections": 32,
                    "dynamicEfMin": 100,
                    "dynamicEfMax": 500,
                    "dynamicEfFactor": 8,
                    "skip": False,
                    "flatSearchCutoff": 40000,
                    "distance": "cosine"
                },
                "vectorizer": {
                    "none": {}
                }
            }
        },
        "replicationConfig": {
            "factor": 1
        },
        "invertedIndexConfig": {
            "indexNullState": False,
            "indexPropertyLength": False,
            "indexTimestamps": False
        }
    }
)

P0_SINGLE_NAMED_VECTOR = SchemaDefinition(
    name="P0-single-named-vector",
    description="Collection with one named vector configuration",
    priority="P0",
    collection_config={
        "name": "SingleNamedVector",
        "description": "Test collection with a single named vector",
        "properties": [
            {
                "name": "text",
                "dataType": ["text"],
                "description": "Text content to vectorize"
            },
            {
                "name": "metadata",
                "dataType": ["text"],
                "description": "Additional metadata"
            }
        ],
        "vectorConfig": {
            "default": {
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": {
                    "ef": -1,
                    "efConstruction": 128,
                    "maxConnections": 32,
                    "dynamicEfMin": 100,
                    "dynamicEfMax": 500,
                    "dynamicEfFactor": 8,
                    "skip": False,
                    "flatSearchCutoff": 40000,
                    "distance": "cosine"
                },
                "vectorizer": {
                    "none": {}
                }
            }
        },
        "replicationConfig": {
            "factor": 1
        },
        "invertedIndexConfig": {
            "indexNullState": False,
            "indexPropertyLength": False,
            "indexTimestamps": False
        }
    }
)

P0_MULTI_NAMED_VECTORS = SchemaDefinition(
    name="P0-multi-named-vectors",
    description="Collection with multiple named vectors",
    priority="P0",
    collection_config={
        "name": "MultiNamedVectors",
        "description": "Test collection with multiple named vector configurations",
        "properties": [
            {
                "name": "text",
                "dataType": ["text"],
                "description": "Main text content"
            },
            {
                "name": "description",
                "dataType": ["text"],
                "description": "Description field"
            }
        ],
        "vectorConfig": {
            "text_vector": {
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": {
                    "ef": -1,
                    "efConstruction": 128,
                    "maxConnections": 32,
                    "dynamicEfMin": 100,
                    "dynamicEfMax": 500,
                    "dynamicEfFactor": 8,
                    "skip": False,
                    "flatSearchCutoff": 40000,
                    "distance": "cosine"
                },
                "vectorizer": {
                    "none": {}
                }
            },
            "description_vector": {
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": {
                    "ef": -1,
                    "efConstruction": 128,
                    "maxConnections": 32,
                    "dynamicEfMin": 100,
                    "dynamicEfMax": 500,
                    "dynamicEfFactor": 8,
                    "skip": False,
                    "flatSearchCutoff": 40000,
                    "distance": "dot"
                },
                "vectorizer": {
                    "none": {}
                }
            }
        },
        "replicationConfig": {
            "factor": 1
        },
        "invertedIndexConfig": {
            "indexNullState": False,
            "indexPropertyLength": False,
            "indexTimestamps": False
        }
    }
)


# Registry of all schema definitions
SCHEMA_DEFINITIONS: Dict[str, SchemaDefinition] = {
    "P0-basic-text-only": P0_BASIC_TEXT_ONLY,
    "P0-single-named-vector": P0_SINGLE_NAMED_VECTOR,
    "P0-multi-named-vectors": P0_MULTI_NAMED_VECTORS,
}


def get_schema_definition(name: str) -> SchemaDefinition:
    """Get a schema definition by name."""
    if name not in SCHEMA_DEFINITIONS:
        raise ValueError(f"Unknown schema: {name}. Available: {list(SCHEMA_DEFINITIONS.keys())}")
    return SCHEMA_DEFINITIONS[name]


def list_schemas(priority: str = None) -> List[SchemaDefinition]:
    """List all schema definitions, optionally filtered by priority."""
    schemas = list(SCHEMA_DEFINITIONS.values())
    if priority:
        schemas = [s for s in schemas if s.priority == priority]
    return schemas


def get_p0_schemas() -> List[SchemaDefinition]:
    """Get all P0 (basic) schema definitions."""
    return list_schemas(priority="P0")
