# Schema Definitions

This directory contains baseline schema configurations that serve as the source of truth for testing import/export functionality across Weaviate clients.

## Schema Organization

Each schema is stored in its own directory with the following structure:

```
<schema-name>/
├── config.json        # Full collection configuration
└── metadata.json      # Schema metadata
```

## P0 Schemas (Basic)

### P0-basic-text-only

**Purpose**: Test basic collection with text properties only, no vector configuration.

**Features**:
- Three text properties: `title`, `content`, `category`
- No vectorizer configuration
- Basic inverted index settings
- Replication factor: 1

**Use Case**: Validates that clients can handle simple text-only collections without vector configurations.

**Expected Behavior**: All clients should create identical collections and export identical configurations.

---

### P0-single-named-vector

**Purpose**: Test collection with a single named vector configuration.

**Features**:
- Two text properties: `text`, `metadata`
- One named vector: `default`
- HNSW index with cosine distance
- Standard HNSW parameters (ef, efConstruction, maxConnections)

**Use Case**: Validates that clients correctly handle named vector configurations, which is the modern Weaviate pattern.

**Expected Behavior**:
- Clients should preserve HNSW configuration
- Vector index parameters should match exactly
- Distance metric should be cosine

---

### P0-multi-named-vectors

**Purpose**: Test collection with multiple named vectors.

**Features**:
- Two text properties: `text`, `description`
- Two named vectors:
  - `text_vector`: HNSW with cosine distance
  - `description_vector`: HNSW with dot product distance
- Independent configuration for each vector

**Use Case**: Validates that clients can handle multiple vector configurations on a single collection, enabling multi-vector search capabilities.

**Expected Behavior**:
- Both vectors should be preserved
- Distance metrics should differ (cosine vs dot)
- HNSW parameters should be independent

## Schema Format

All schemas follow the Weaviate collection configuration format:

```json
{
  "name": "CollectionName",
  "description": "Collection description",
  "properties": [
    {
      "name": "propertyName",
      "dataType": ["text"],
      "description": "Property description"
    }
  ],
  "vectorConfig": {
    "vectorName": {
      "vectorIndexType": "hnsw",
      "vectorIndexConfig": {
        "ef": -1,
        "efConstruction": 128,
        "maxConnections": 32,
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
    "indexNullState": false,
    "indexPropertyLength": false,
    "indexTimestamps": false
  }
}
```

## Schema Generation

Schemas are generated using the Python schema generator:

```bash
cd schema-generator
python -m src.cli generate-all --output-dir ../schemas
```

## Schema Validation

Each schema is validated by:

1. Creating the collection in Weaviate
2. Exporting the configuration
3. Comparing with the definition
4. Verifying all parameters are preserved

## Adding New Schemas

To add a new schema:

1. Add definition to `schema-generator/src/schema_definitions.py`
2. Run generator to create baseline
3. Document the schema in this README
4. Update test clients to include the new schema

## Future Schemas

### P1 Schemas (Intermediate)
- Collections with references/cross-references
- Collections with nested properties
- Collections with custom tokenization
- Collections with property-level vectorizers

### P2 Schemas (Advanced)
- Multi-tenancy configurations
- Sharding configurations
- Module-specific settings
- Custom vector index types

## Notes

- Schemas use `"none"` vectorizer to avoid external dependencies
- All schemas use replication factor of 1 for simplicity
- Timestamps are excluded from comparisons as they vary by creation time
- Schemas are sorted and normalized before comparison
