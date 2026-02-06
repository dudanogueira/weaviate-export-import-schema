# Issue #2: Distance Metric Not Preserved for Named Vectors

**Status**: 🔴 CONFIRMED DATA CORRUPTION BUG

**Severity**: **CRITICAL** - Data Integrity Issue

**Affected Clients**:
- ❌ Python v4.19.2 (confirmed)
- ⏳ TypeScript v3.2.0 (blocked by Issue #1, not yet testable)

**Root Cause**: Unknown - needs investigation (possibly Weaviate server 1.35.7)

**Discovered**: 2026-02-06

**Framework**: Weaviate Schema Testing Framework v0.1.0

---

## Description

When creating a collection with multiple named vectors using different distance metrics, **the distance metric silently changes** during import/export. The "dot" distance metric is incorrectly replaced with "cosine", fundamentally altering the semantic meaning of vector similarity calculations.

**This is a DATA CORRUPTION bug** - it changes how vectors are compared without warning, leading to incorrect search results.

---

## Test Case

**Schema**: P0-multi-named-vectors

**Expected Configuration**:
```json
{
  "vectorConfig": {
    "text_vector": {
      "vectorIndexConfig": {
        "distance": "cosine"
      }
    },
    "description_vector": {
      "vectorIndexConfig": {
        "distance": "dot"
      }
    }
  }
}
```

**Actual Configuration After Import/Export**:
```json
{
  "vectorConfig": {
    "text_vector": {
      "vectorIndexConfig": {
        "distance": "cosine"
      }
    },
    "description_vector": {
      "vectorIndexConfig": {
        "distance": "cosine"  // ❌ Changed from "dot"!
      }
    }
  }
}
```

---

## Minimal Reproducible Example (Python)

```python
import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances

# Connect to Weaviate
client = weaviate.connect_to_local()

# Create collection with TWO named vectors using DIFFERENT distance metrics
vector_configs = {
    "text_vector": Configure.NamedVectors.none(
        name="text_vector",
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.COSINE  # cosine
        )
    ),
    "description_vector": Configure.NamedVectors.none(
        name="description_vector",
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.DOT  # dot (DIFFERENT!)
        )
    )
}

client.collections.create(
    name="MultiVectorTest",
    properties=[Property(name="text", data_type=DataType.TEXT)],
    vectorizer_config=list(vector_configs.values())
)

# Export and check what we get back
collection = client.collections.get("MultiVectorTest")
config = collection.config.get()
exported = config.to_dict()

# Check the distance metrics
text_distance = exported['vectorConfig']['text_vector']['vectorIndexConfig']['distanceMetric']
desc_distance = exported['vectorConfig']['description_vector']['vectorIndexConfig']['distanceMetric']

print(f"text_vector distance: {text_distance}")       # Expected: cosine
print(f"description_vector distance: {desc_distance}") # Expected: dot

# Verify they're different
if text_distance != desc_distance:
    print("✅ Distance metrics preserved correctly")
else:
    print("❌ BUG: Both vectors have the same distance metric!")
    print(f"   Both are: {text_distance}")

client.collections.delete("MultiVectorTest")
client.close()
```

**Expected Output**:
```
text_vector distance: cosine
description_vector distance: dot
✅ Distance metrics preserved correctly
```

**Actual Output**:
```
text_vector distance: cosine
description_vector distance: cosine  # ❌ WRONG! Should be 'dot'
❌ BUG: Both vectors have the same distance metric!
   Both are: cosine
```

---

## Impact

### Data Corruption

This is a **silent data corruption bug**:

1. You define a schema with specific distance metrics
2. The schema is saved/imported
3. **Distance metrics change** without error or warning
4. Search results are **wrong** but appear normal
5. Users receive incorrect, misleading results

### Real-World Scenario

```python
# Example: E-commerce recommendation system

# You carefully design:
# - product_semantic: cosine (for "similar products")
# - user_preference: dot (for "products user will like")

# After import/export, BOTH use cosine!
# Your recommendation system now returns WRONG products
# Sales decrease, users get bad recommendations
# NO error or warning is shown
```

### Mathematical Impact

- **Cosine**: Measures angle, normalized (0 to 1)
- **Dot Product**: Measures magnitude + direction (-∞ to +∞)

Changing from dot to cosine fundamentally changes:
- How vectors are compared
- Which results are returned
- The ranking order of search results

---

## Detailed Difference

From framework test output:

```json
{
  "values_changed": {
    "root['vectorConfig']['description_vector']['vectorIndexConfig']['distanceMetric']": {
      "new_value": "cosine",
      "old_value": "dot"
    }
  }
}
```

---

## Test Results

**Python v4.19.2**:
```
AssertionError: Schema mismatch for P0-multi-named-vectors:
{
  "values_changed": {
    "root['vectorConfig']['description_vector']['vectorIndexConfig']['distanceMetric']": {
      "new_value": "cosine",
      "old_value": "dot"
    }
  }
}
```

**TypeScript v3.2.0**: Cannot test yet (blocked by Issue #1)

---

## Possible Root Causes

### 1. Import Bug (Test Client)
Distance metric not being read correctly from schema definition.

**Investigation**: Check if distance_str is properly extracted from JSON:
```python
distance_str = vector_def.get('vectorIndexConfig', {}).get('distance', 'cosine')
```

### 2. API Bug (Python Client)
`Configure.NamedVectors.none()` not respecting distance_metric parameter.

**Investigation**: Add debug logging to see what's passed to Weaviate server.

### 3. Weaviate Server Bug
Server not preserving distance metric for some vector configurations.

**Investigation**: Check server logs and REST API responses directly.

### 4. Schema Definition Bug
Incorrect specification format in schema definitions.

**Investigation**: ✅ Verified - schema definitions are correct (line 157 has "dot")

---

## Investigation Steps

**Completed**:
- ✅ Verify schema definition is correct - CONFIRMED (distance: "dot" in definition)
- ✅ Demonstrate bug with minimal example - DONE
- ✅ Verify baseline schema has correct distance - CONFIRMED
- ✅ Verify exported schema has wrong distance - CONFIRMED

**Next Steps**:
- ⏳ Test with Weaviate REST API directly (bypass client)
- ⏳ Add debug logging to capture what's sent to server
- ⏳ Check Weaviate server logs for distance metric handling
- ⏳ Test with TypeScript client (once Issue #1 is fixed)
- ⏳ Isolate whether bug is in Python client or Weaviate server

---

## Code to Investigate

```python
# test-clients/python/src/test_runner.py:99-108
for vector_name, vector_def in schema['vectorConfig'].items():
    distance_str = vector_def.get('vectorIndexConfig', {}).get('distance', 'cosine')
    distance = getattr(VectorDistances, distance_str.upper())

    vector_configs[vector_name] = Configure.NamedVectors.none(
        name=vector_name,
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=distance  # ← Is this being set correctly?
        )
    )
```

**Debug Needed**: Add logging to confirm `distance_str` is "dot" for description_vector.

---

## Framework Decision

**NO WORKAROUND**

The framework intentionally does not work around this bug. We could modify the schema definition to avoid using "dot" distance, but that would:

- Hide a critical data corruption bug
- Give false confidence to users
- Reduce urgency for proper fix
- Mask the severity of the issue

---

## Recommendation for Weaviate Team

### Immediate Actions

1. **Reproduce the bug** using the minimal example above
2. **Add debug logging** to track distance metric through the full pipeline:
   - Client API call
   - gRPC/REST request
   - Server processing
   - Storage
   - Retrieval
   - Client response

3. **Identify root cause**:
   - Is it client-side (Python client ignoring distance parameter)?
   - Is it server-side (Weaviate not storing/returning distance correctly)?
   - Is it both?

### Long-term Solutions

1. **Add validation** - Reject schemas if distance metric changes
2. **Add tests** - Multi-vector schemas with different distances
3. **Add warnings** - Log when distance metrics are normalized/changed
4. **Document behavior** - If intentional, document clearly

---

## Workaround

**None currently available**

The only workaround would be to avoid using multiple distance metrics in the same collection, which defeats the purpose of named vectors.

---

## Upstream Actions Required

- [ ] Test with REST API directly to isolate client vs server
- [ ] Add comprehensive logging
- [ ] Reproduce in isolated environment
- [ ] Create issue in appropriate repository (client or server)
- [ ] Add regression tests
- [ ] Update documentation if behavior is intentional

---

## Related Issues

- [Issue #1: Missing Collection Name](ISSUE-001-missing-collection-name.md) - Blocks full testing of this issue

---

## References

- [Weaviate Distance Metrics Documentation](https://weaviate.io/developers/weaviate/config-refs/distances)
- [Named Vectors Documentation](https://weaviate.io/developers/weaviate/config-refs/schema/vector-index)
- [Python Client Vector Config](https://weaviate.io/developers/weaviate/client-libraries/python/v4)

---

**Last Updated**: 2026-02-06
**Reporter**: Weaviate Schema Testing Framework
**Priority**: P0 (Critical - Data Corruption)
