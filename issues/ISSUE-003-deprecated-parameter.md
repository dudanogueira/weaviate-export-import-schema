# Issue #3: Deprecation Warning for `vectorizer_config` Parameter

**Status**: ✅ FIXED

**Severity**: Low (Future Compatibility Risk)

**Affected Clients**:
- ✅ Python v4.19.2 (Fixed)

**Root Cause**: Framework code was using deprecated API parameter name

**Discovered**: 2026-02-06
**Fixed**: 2026-02-06

**Framework**: Weaviate Schema Testing Framework v0.1.0

---

## Description

The Python client generates a deprecation warning when using the `vectorizer_config` parameter in collection creation. The parameter has been renamed to `vector_config` in newer API versions.

---

## Warning Message

```
DeprecationWarning: Dep024: You are using the `vectorizer_config` argument
in `collection.config.create()`, which is deprecated.
Use the `vector_config` argument instead.
```

**Source**: `/path/to/weaviate/warnings.py:196`

---

## Expected Behavior

Code should use the recommended `vector_config` parameter to avoid deprecation warnings and ensure future compatibility.

---

## Actual Behavior

Code uses deprecated `vectorizer_config` parameter, generating warnings in test output.

---

## Minimal Reproducible Example (Python)

```python
import weaviate
from weaviate.classes.config import Configure, Property, DataType

client = weaviate.connect_to_local()

# Using DEPRECATED parameter name
client.collections.create(
    name="TestCollection",
    properties=[Property(name="text", data_type=DataType.TEXT)],
    vectorizer_config=Configure.Vectorizer.none()  # ⚠️ DEPRECATED
)

# Output shows deprecation warning:
# DeprecationWarning: Dep024: You are using the `vectorizer_config` argument
# in `collection.config.create()`, which is deprecated.
# Use the `vector_config` argument instead.

client.collections.delete("TestCollection")

# CORRECT way (new API):
client.collections.create(
    name="TestCollection2",
    properties=[Property(name="text", data_type=DataType.TEXT)],
    vector_config=Configure.Vectorizer.none()  # ✅ CORRECT
)

client.collections.delete("TestCollection2")
client.close()
```

**Expected Behavior**:
No deprecation warnings when using recommended API.

**Actual Behavior**:
```
DeprecationWarning: Dep024: You are using the `vectorizer_config` argument
```

---

## Impact

### Current Impact (Low)

- Warning noise in test output
- Minor concern for code maintainability
- May confuse users looking at framework code

### Future Impact (Medium)

- **Risk of breaking** in future client versions
- Users following framework examples will use deprecated patterns
- Technical debt that needs eventual cleanup

### User Experience

- Developers using the framework as reference will copy deprecated patterns
- CI/CD pipelines may fail if treating warnings as errors

---

## Test Output

The warning appears when running any test that creates collections with vector configurations:

```bash
$ pytest -v tests/
...
tests/test_schemas.py::test_schema_import_export[P0-single-named-vector]
/path/to/weaviate/warnings.py:196: DeprecationWarning: Dep024: ...
  warnings.warn(
...
```

---

## Why This Matters

1. **Framework is Reference Implementation**: Users look at framework code as examples
2. **Future Compatibility**: Parameter may be removed in Python client v5.x
3. **Best Practices**: Framework should demonstrate current best practices
4. **Maintenance**: Easier to update now than wait for breaking change

---

## Code Locations

**Files that need updating**:

1. `schema-generator/src/generator.py:111`
   ```python
   collection = self.client.collections.create(
       name=collection_name,
       description=config.get("description"),
       properties=properties,
       vectorizer_config=vector_config,  # ← Change to vector_config
       ...
   )
   ```

2. `test-clients/python/src/test_runner.py:119`
   ```python
   collection = self.client.collections.create(
       name=collection_name,
       description=schema.get('description'),
       properties=properties,
       vectorizer_config=vector_config,  # ← Change to vector_config
       ...
   )
   ```

---

## Fix

### Simple Find & Replace

Change all occurrences of:
```python
vectorizer_config=vector_config
```

To:
```python
vector_config=vector_config
```

**Affected Lines**:
- `schema-generator/src/generator.py:111`
- `schema-generator/src/generator.py:125` (if exists)
- `test-clients/python/src/test_runner.py:119`
- `test-clients/python/src/test_runner.py:135` (if exists)

### Testing After Fix

After making changes:

1. Run schema generation:
   ```bash
   cd schema-generator
   python -m src.cli generate-all
   # Should not show deprecation warning
   ```

2. Run Python tests:
   ```bash
   cd test-clients/python
   pytest -v
   # Should not show deprecation warning
   ```

---

## Migration Impact

**Estimated Effort**: 15 minutes

**Risk**: Very Low
- Simple parameter rename
- Functionality unchanged
- Both parameters currently work

**Testing**: Minimal
- Verify schemas still generate correctly
- Verify tests still pass
- Check for absence of warnings

---

## Recommendation

### Priority

**Low-Medium Priority**

While not urgent (deprecated parameter still works), this should be fixed because:
1. Framework is reference implementation
2. Easy fix (5 minutes)
3. Improves code quality
4. Prevents future issues

### Suggested Timeline

- **Before v1.0.0 release**: Should be fixed
- **Estimated time**: 15 minutes total
  - 5 minutes: Make changes
  - 5 minutes: Test
  - 5 minutes: Verify no warnings

---

## Resolution

**Status**: ✅ FIXED on 2026-02-06

### Changes Made

1. **Updated `schema-generator/src/generator.py:112`**
   ```python
   # Before:
   vectorizer_config=vector_config,  # ❌ Deprecated

   # After:
   vector_config=vector_config,      # ✅ Correct
   ```

2. **Updated `test-clients/python/src/test_runner.py:120`**
   ```python
   # Before:
   vectorizer_config=vector_config,  # ❌ Deprecated

   # After:
   vector_config=vector_config,      # ✅ Correct
   ```

### Verification

Tested with:
- ✅ Schema generation: No warnings
- ✅ Python test suite: No warnings
- ✅ All code now uses `vector_config` parameter

**Test Results**:
```bash
$ pytest -v tests/
# No "Dep024" or "DeprecationWarning" messages ✅
```

---

## Upstream Actions Required

- [x] Update `schema-generator/src/generator.py` ✅ DONE
- [x] Update `test-clients/python/src/test_runner.py` ✅ DONE
- [x] Run tests to verify no warnings ✅ VERIFIED
- [ ] Update any documentation examples (if needed)
- [ ] Add to CHANGELOG

---

## Related Issues

None

---

## References

- [Weaviate Python Client v4 Migration Guide](https://weaviate.io/developers/weaviate/client-libraries/python/v4)
- [Python Client Deprecation Warnings](https://weaviate.io/developers/weaviate/client-libraries/python/v4#deprecation-warnings)

---

**Last Updated**: 2026-02-06
**Reporter**: Weaviate Schema Testing Framework
**Priority**: P2 (Low-Medium)
