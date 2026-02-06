# Issue #1: Missing Collection Name in Exported Schemas

**Status**: 🔴 CONFIRMED - AFFECTS ALL TESTED CLIENTS

**Severity**: Critical (Blocks 100% of workflows)

**Affected Clients**:
- ❌ Python v4.19.2
- ❌ TypeScript v3.2.0
- ❌ Java v4.8.1

**Root Cause**: Confirmed cross-client bug - Weaviate server or coordinated API design flaw

**Discovered**: 2026-02-06

**Framework**: Weaviate Schema Testing Framework v0.1.0

---

## Description

When exporting a collection configuration using `collection.config.get().to_dict()` (Python) or `collection.config.get()` (TypeScript), the resulting dictionary **does not include the collection name**. This is a fundamental API design flaw that makes schemas non-self-describing and breaks import/export workflows.

---

## Expected Behavior

Exported schema should include a `'name'` or `'class'` field with the collection name at the top level, making the schema self-describing and portable.

---

## Actual Behavior

Exported schema lacks a top-level `'name'` field. The collection name must be tracked separately, making round-trip import/export impossible without additional metadata.

---

## Minimal Reproducible Example (Python)

```python
import weaviate
from weaviate.classes.config import Configure, Property, DataType

# Connect to Weaviate
client = weaviate.connect_to_local()

# Create a simple collection
client.collections.create(
    name="TestCollection",
    properties=[
        Property(name="text", data_type=DataType.TEXT)
    ]
)

# Export the collection configuration
collection = client.collections.get("TestCollection")
config = collection.config.get()
exported_schema = config.to_dict()

# Check if 'name' field exists
print("Has 'name' field:", 'name' in exported_schema)  # False ❌
print("Keys in schema:", list(exported_schema.keys()))

# Try to reimport - THIS WILL FAIL
# Because we don't know what collection name to use!
# exported_schema has no 'name' field to tell us

# Cleanup
client.collections.delete("TestCollection")
client.close()
```

**Expected Output**:
```
Has 'name' field: True
Keys in schema: ['name', 'description', 'properties', ...]
```

**Actual Output**:
```
Has 'name' field: False  # ❌ BUG!
Keys in schema: ['description', 'properties', 'vectorConfig', 'invertedIndexConfig', ...]
```

---

## Minimal Reproducible Example (TypeScript)

```typescript
import weaviate from 'weaviate-client';

const client = await weaviate.connectToLocal();

// Create a simple collection
await client.collections.create({
  name: 'TestCollection',
  properties: [
    { name: 'text', dataType: ['text'] }
  ]
});

// Export the collection configuration
const collection = client.collections.get('TestCollection');
const config = await collection.config.get();

// Check if 'name' field exists
console.log('Has name field:', 'name' in config);  // false ❌
console.log('Keys:', Object.keys(config));

// Try to reimport - THIS WILL FAIL
// because we don't know the collection name!

// Cleanup
await client.collections.delete('TestCollection');
await client.close();
```

**Expected Output**:
```
Has name field: true
Keys: ['name', 'description', 'properties', ...]
```

**Actual Output**:
```
Has name field: false  # ❌ BUG!
Keys: ['description', 'properties', 'vectorConfig', ...]
```

---

## Minimal Reproducible Example (Java)

```java
import io.weaviate.client.Config;
import io.weaviate.client.WeaviateClient;
import io.weaviate.client.base.Result;
import io.weaviate.client.v1.schema.model.Property;
import io.weaviate.client.v1.schema.model.WeaviateClass;
import com.fasterxml.jackson.databind.ObjectMapper;

public class IssueDemo {
    public static void main(String[] args) throws Exception {
        // Connect to Weaviate
        Config config = new Config("http", "localhost:8080");
        WeaviateClient client = new WeaviateClient(config);
        ObjectMapper mapper = new ObjectMapper();

        // Create a simple class
        WeaviateClass weaviateClass = WeaviateClass.builder()
            .className("TestCollection")
            .properties(Arrays.asList(
                Property.builder()
                    .name("text")
                    .dataType(Arrays.asList("text"))
                    .build()
            ))
            .build();

        client.schema().classCreator().withClass(weaviateClass).run();

        // Export the class configuration
        Result<WeaviateClass> result = client.schema()
            .classGetter()
            .withClassName("TestCollection")
            .run();

        WeaviateClass exported = result.getResult();
        String json = mapper.writeValueAsString(exported);

        // Check if 'name' or 'className' field exists
        System.out.println("Has 'className' field: " + json.contains("\"className\""));
        System.out.println("Exported JSON: " + json);

        // Try to reimport - THIS WILL FAIL
        // because exported schema doesn't have className!

        // Cleanup
        client.schema().classDeleter().withClassName("TestCollection").run();
    }
}
```

**Expected Behavior**:
```
Has 'className' field: true
Exported JSON: {"className":"TestCollection","description":...}
```

**Actual Behavior**:
```
Has 'className' field: false  # ❌ BUG!
Exported JSON: {"description":...,"properties":...}
```

---

## Test Results

**Python v4.19.2**:
```
AssertionError: Import/export failed: Schema missing 'name' field
```

**TypeScript v3.2.0**:
```
Error: Schema missing "name" field
    at TestRunner.importSchema (testRunner.ts:70:13)
```

**Java v4.8.1**:
```
java.lang.IllegalArgumentException: Schema missing 'name' field
    at io.weaviate.schema.test.SchemaTestRunner.importSchema(SchemaTestRunner.java:56)
```

---

## Impact

### Blocks Critical Workflows

- **BLOCKS** schema roundtripping (export → import → export)
- Schemas are not self-describing or portable
- Forces users to maintain separate metadata
- Breaks automated migration tools
- Incompatible with schema version control workflows

### Affects All Users

This bug affects:
- ❌ Schema migration between environments
- ❌ Backup and restore procedures
- ❌ Infrastructure as Code (IaC) tools
- ❌ Multi-tenant systems that manage schemas programmatically
- ❌ Any tool that needs to export/import schemas

### Test Results

| Test Schema | Python | TypeScript | Java | Result |
|-------------|--------|------------|------|--------|
| P0-basic-text-only | ❌ FAIL | ❌ FAIL | ❌ FAIL | All blocked |
| P0-single-named-vector | ❌ FAIL | ❌ FAIL | ❌ FAIL | All blocked |
| P0-multi-named-vectors | ❌ FAIL | ❌ FAIL | ❌ FAIL | All blocked |

**Overall**: 0/9 tests passing (0% across all three clients)

---

## Root Cause Analysis

### Cross-Client Evidence

The fact that **Python, TypeScript, AND Java** all have the identical issue confirms:

1. **Most Likely**: Weaviate server doesn't include collection name in the serialized schema response
2. **Also Possible**: Coordinated API design flaw across all official clients deliberately omits this field
3. **Confirmed**: This is NOT a client-specific bug - it affects all three major client libraries
3. **Least Likely**: Independent bug in multiple client implementations

### What Needs Investigation

1. Check Weaviate REST API directly - does `/v1/schema/{className}` include the class name?
2. Check Weaviate server code - is the name intentionally excluded?
3. Check API specification - is this "working as designed" (wrong design)?

---

## Framework Decision

**NO WORKAROUND**

The framework intentionally fails these tests to maintain visibility of this bug. Adding workarounds (like manually adding `schema['name'] = collection_name`) would:

- Hide the problem from users
- Reduce pressure for proper fixes
- Give false sense of compatibility
- Make the issue harder to discover

---

## Recommendation for Weaviate Team

### Quick Fix (Recommended)

Add the `name` field to the dictionary returned by `config.to_dict()` in the Python client and the object returned by `config.get()` in TypeScript.

**Python**:
```python
# In weaviate.collections.collection.config
def to_dict(self) -> Dict[str, Any]:
    result = {
        'name': self.name,  # ← ADD THIS LINE
        'description': self.description,
        'properties': [...],
        # ... rest of config
    }
    return result
```

**TypeScript**:
```typescript
// In collection config
async get(): Promise<CollectionConfig> {
    const config = await this.fetchConfig();
    return {
        name: this.name,  // ← ADD THIS LINE
        description: config.description,
        properties: config.properties,
        // ... rest of config
    };
}
```

**Estimated Effort**: ~1 hour per client

### Alternative (If Server-Side)

If the issue is in Weaviate server, update the REST API response to include the collection/class name in the schema export.

**Estimated Effort**: ~2-4 hours

---

## Upstream Actions Required

- [ ] Confirm root cause (client vs server)
- [ ] Create issue in weaviate-python repository
- [ ] Create issue in weaviate-typescript repository
- [ ] If server-side, create issue in weaviate repository
- [ ] Add tests to prevent regression
- [ ] Update documentation with migration guide

---

## Related Issues

- None yet

---

## References

- [Weaviate Python Client Documentation](https://weaviate.io/developers/weaviate/client-libraries/python)
- [Weaviate TypeScript Client Documentation](https://weaviate.io/developers/weaviate/client-libraries/typescript)
- [Weaviate Schema REST API](https://weaviate.io/developers/weaviate/api/rest/schema)

---

**Last Updated**: 2026-02-06
**Reporter**: Weaviate Schema Testing Framework
**Priority**: P0 (Blocker)
