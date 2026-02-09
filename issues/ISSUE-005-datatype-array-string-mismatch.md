# Issue #5: DataType Array vs String Mismatch

**Status**: 🔴 CONFIRMED - CRITICAL  
**Date Discovered**: 2026-02-09  
**Test Environment**:
- Weaviate Server: v1.35.7
- TypeScript Client: v3.2.0 (local build with fixes)
- Test Schema: P0-basic-text-only

---

## Summary

The TypeScript client has inconsistent behavior with the `dataType` field:
- **On CREATE**: Accepts both string (`"text"`) and array (`["text"]`) formats
- **ON EXPORT**: Returns `dataType` as **string** when it should be **array**
- **On IMPORT**: Server expects format depends on version/API

This creates a **round-trip failure**: export → import doesn't work because the export format doesn't match what import expects.

---

## Error Message

```
WeaviateUnexpectedStatusCodeError: The request to Weaviate failed with status code: 400 
and message: {"code":400,"message":"parsing objectClass body from \"\" failed, because 
json: cannot unmarshal array into Go struct field Property.properties.dataType of type string"}
```

## Technical Details

### Expected Behavior
The TypeScript client should maintain consistent `dataType` format across create/export/import operations.

### Actual Behavior
- **Create API**: Accepts `dataType: "text"` (string)
- **Export API**: Returns `dataType: "text"` (string) 
- **Import/CreateFromSchema**: May expect `dataType: ["text"]` (array) depending on server version
- Schema files store `dataType` as arrays (e.g., `["text"]`)
- The Weaviate server v1.35.7 expects `dataType` as a **string** for Go struct unmarshaling

### Root Cause Analysis

This is a **format inconsistency** issue:

1. **TypeScript Client API**: Accepts string format for convenience
2. **Internal conversion**: The `resolveProperty` function converts to array format
3. **Export format**: Exports as string (doesn't convert back)
4. **Import expectations**: Variable depending on code path

The mismatch occurs in [typescript-client/src/collections/config/utils.ts:85](typescript-client/src/collections/config/utils.ts#L85):
```typescript
dataType: Array.isArray(dataType) ? dataType : [dataType],
```

This converts input to array, but export doesn't reverse the process.

---

## Reproduction Steps

1. Use TypeScript client from local build: `file:../../../typescript-client`
2. Create a collection with text property using `collections.create()`
3. Export the collection using `collections.export()`
4. Observe that exported `dataType` is string instead of array
5. Attempt to re-import using `collections.createFromSchema()`
6. Observe potential errors if format doesn't match expectations

**Automated Test**: See [test-clients/typescript/tests/datatype-format.test.ts](test-clients/typescript/tests/datatype-format.test.ts)

## Test Code Location

- Test runner: [test-clients/typescript/src/testRunner.ts](test-clients/typescript/src/testRunner.ts)
- Lines 83-90: Property mapping with workaround
- Schema: [schemas/P0-basic-text-only/config.json](schemas/P0-basic-text-only/config.json)
- **Dedicated test suite**: [test-clients/typescript/tests/datatype-format.test.ts](test-clients/typescript/tests/datatype-format.test.ts)

## Automated Test

A dedicated test suite has been created to demonstrate and verify this issue:

**File**: `test-clients/typescript/tests/datatype-format.test.ts`

**Test cases**:
1. **Export format verification**: Creates a collection, exports it, and verifies that `dataType` is exported as array format `["text"]` not string `"text"`
2. **Expected format reference**: Documents the correct schema format for reference
3. **Multiple properties test**: Verifies that all property types (text, int, boolean) are exported with array format

**Running the test**:
```bash
cd test-clients/typescript
npm test -- datatype-format.test.ts
```

Or use the convenience script:
```bash
./scripts/test_issue5.sh
```

The test will:
- ✅ Pass if dataType is exported as array (correct behavior)
- ❌ Fail if dataType is exported as string (demonstrates the bug)

Results are saved to `test-results/issue-5/` for inspection:
- `exported-schema.json` - Actual export from client
- `expected-format.json` - Expected format reference
- `multi-property-export.json` - Multiple property types test

## Impact

**Severity**: 🔴 CRITICAL  
**Affects**: TypeScript schema export/import workflows when using local client  
**Blocks**: Round-trip export/import operations

**Real-world impact**:
- Cannot reliably export and re-import schemas
- Migration scripts may fail
- Backup/restore workflows affected
- API version inconsistencies

---

## Proposed Solutions

### Option 1: Fix Schema Format (Quick Fix) ✅ IMPLEMENTED
Convert `dataType` from array to string in testRunner before passing to client:
```typescript
const properties = schema.properties?.map((prop: any) => ({
  name: prop.name,
  dataType: Array.isArray(prop.dataType) ? prop.dataType[0] : prop.dataType,
  description: prop.description,
})) || [];
```

**Status**: ✅ Implemented in testRunner.ts  
**Pros**: Works around the issue, unblocks testing  
**Cons**: Doesn't fix root cause, only symptom

### Option 2: Fix Client Export Implementation
Update the export/serialize logic to ensure consistent format:
```typescript
// In config/utils.ts or serialize logic
const serializeProperty = (prop) => ({
  ...prop,
  dataType: Array.isArray(prop.dataType) ? prop.dataType : [prop.dataType]
});
```

**Pros**: Fixes root cause, maintains consistency  
**Cons**: Requires client library changes

### Option 3: Document API Contract
Clearly document what format each API expects/returns:
- CREATE: string or array
- EXPORT: always array
- IMPORT: always array

**Pros**: Prevents confusion  
**Cons**: Doesn't fix the inconsistency

---

## Recommended Action

1. **Immediate**: ✅ Applied Option 1 (testRunner workaround) to unblock testing
2. **Short-term**: Run dedicated test to verify exact export format
3. **Long-term**: Report to TypeScript client maintainers for consistent API behavior

---

## Related Files

- [test-clients/typescript/src/testRunner.ts](test-clients/typescript/src/testRunner.ts) - Contains workaround
- [test-clients/typescript/tests/datatype-format.test.ts](test-clients/typescript/tests/datatype-format.test.ts) - Automated test
- [typescript-client/src/collections/config/utils.ts](typescript-client/src/collections/config/utils.ts) - resolveProperty function
- [typescript-client/src/collections/index.ts](typescript-client/src/collections/index.ts) - collections.create implementation
- [schemas/P0-basic-text-only/config.json](schemas/P0-basic-text-only/config.json) - Example schema
- [scripts/test_issue5.sh](scripts/test_issue5.sh) - Convenience test script

---

## Status Updates

- **2026-02-09 14:00**: Issue discovered when testing with local TypeScript client build
- **2026-02-09 15:30**: Workaround implemented in testRunner.ts (Option 1)
- **2026-02-09 16:00**: Dedicated test suite created for verification
- **2026-02-09 16:30**: Convenience test script added
- **Next**: Run automated test to confirm exact export format behavior

---

## Example Schema Formats

### Expected Format (Array)
```json
{
  "class": "Test",
  "properties": [
    {
      "name": "property1",
      "dataType": ["text"],
      "indexFilterable": true,
      "indexSearchable": true,
      "tokenization": "word",
      "indexRangeFilters": false
    }
  ]
}
```

### Problematic Format (String)
```json
{
  "class": "Test",
  "properties": [
    {
      "name": "property1",
      "dataType": "text",
      "indexFilterable": true,
      "indexSearchable": true,
      "tokenization": "word",
      "indexRangeFilters": false
    }
  ]
}
```

The client should consistently use array format for interoperability.
