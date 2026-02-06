# Issue #4: Pytest Collection Warning for TestRunner Class

**Status**: ⚠️ WARNING

**Severity**: Low (Cosmetic)

**Affected Components**:
- Framework code organization (not a Weaviate bug)

**Root Cause**: Class naming pattern conflicts with pytest conventions

**Discovered**: 2026-02-06

**Framework**: Weaviate Schema Testing Framework v0.1.0

---

## Description

Pytest attempts to collect `TestRunner` class as a test class because it starts with "Test", but it has an `__init__` constructor which test classes shouldn't have. This generates a warning during test collection.

**This is a framework code organization issue, not a Weaviate bug.**

---

## Warning Message

```
PytestCollectionWarning: cannot collect test class 'TestRunner'
because it has a __init__ constructor (from: tests/test_schemas.py)
```

**Source**: Pytest test collection phase

---

## Expected Behavior

Pytest should only attempt to collect actual test classes, not utility classes used by tests.

---

## Actual Behavior

Pytest warns about `TestRunner` class during test discovery, creating noise in test output.

---

## Current File Structure

```
test-clients/python/
├── src/
│   ├── test_runner.py          # Contains TestRunner class
│   └── comparator.py
└── tests/
    └── test_schemas.py         # Pytest discovers this
```

**test_runner.py**:
```python
class TestRunner:  # ⚠️ Starts with "Test"
    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        self.weaviate_url = weaviate_url
        # ... rest of implementation
```

---

## Minimal Reproducible Example

1. Create a file `src/test_runner.py` with:
   ```python
   class TestRunner:
       def __init__(self):
           pass
   ```

2. Import it in a test file:
   ```python
   from src.test_runner import TestRunner
   ```

3. Run pytest:
   ```bash
   pytest -v tests/
   ```

4. See the warning:
   ```
   PytestCollectionWarning: cannot collect test class 'TestRunner'
   because it has a __init__ constructor
   ```

---

## Why This Happens

Pytest automatically tries to collect classes as test classes if they:
- Start with "Test" (case-sensitive)
- Are in files discovered during test collection

However, test classes in pytest should NOT have `__init__` constructors. Since `TestRunner` has one, pytest warns that it can't collect it as a test class.

---

## Impact

### Current Impact

- **Minimal**: Just warning noise in test output
- Doesn't affect test execution or results
- May confuse developers reviewing test output

### User Experience

```bash
$ pytest -v
...
PytestCollectionWarning: cannot collect test class 'TestRunner'
...
================================ 3 passed in 1.20s =================================
```

While tests pass, the warning suggests something might be wrong.

---

## Three Ways to Fix

### Option 1: Rename the Class (Simplest)

**Change**:
```python
class SchemaTestRunner:  # ✅ Doesn't start with "Test"
    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        self.weaviate_url = weaviate_url
```

**Pros**:
- Simple, clear fix
- No pytest configuration needed
- More descriptive name

**Cons**:
- Need to update all imports
- Changes public API

**Files to update**:
- `src/test_runner.py` - Rename class
- `tests/test_schemas.py` - Update import

---

### Option 2: Add `__test__ = False` (Quick Fix)

**Change**:
```python
class TestRunner:
    __test__ = False  # ✅ Tell pytest to ignore this class

    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        self.weaviate_url = weaviate_url
```

**Pros**:
- No API changes
- Single line fix
- Explicit intent

**Cons**:
- Less intuitive
- Every Test* class needs this
- Pytest-specific magic

**Files to update**:
- `src/test_runner.py` - Add `__test__ = False`

---

### Option 3: Reorganize Files (Cleanest)

**Current**:
```
src/
├── test_runner.py          # ← File name starts with "test_"
└── comparator.py
```

**New**:
```
src/
├── runner.py               # ✅ Rename file (no 'test_' prefix)
└── comparator.py
```

**Pros**:
- Most semantically correct
- Files in `src/` shouldn't have `test_` prefix
- Better separation of concerns
- More maintainable

**Cons**:
- Need to update all imports
- Slightly more work

**Files to update**:
- Rename `src/test_runner.py` → `src/runner.py`
- Update imports in `tests/test_schemas.py`
- Update any documentation references

---

## Recommended Fix

**Option 3: Reorganize Files**

This is the cleanest solution because:
1. Files in `src/` shouldn't have `test_` prefix (that's for test files)
2. The class name `TestRunner` is actually appropriate (it runs tests)
3. Separates test implementation from test definitions

**Implementation**:

```bash
# Rename file
mv src/test_runner.py src/runner.py

# Update imports in tests
# Change: from test_runner import TestRunner
# To: from runner import TestRunner
```

---

## Migration Impact

**Estimated Effort**: 5 minutes

**Risk**: Very Low
- Only affects imports
- No functionality changes
- Easy to test

**Testing**: Minimal
- Run pytest to verify warning is gone
- Verify all tests still pass

---

## Recommendation

### Priority

**Low Priority** - Cosmetic issue

This can be fixed anytime before v1.0.0 release. It doesn't affect functionality, only test output cleanliness.

### Suggested Timeline

- **Before v1.0.0 release**: Should be fixed for clean release
- **Estimated time**: 5-10 minutes total
  - 2 minutes: Rename file and update imports
  - 3 minutes: Test
  - 2 minutes: Update documentation

---

## Upstream Actions Required

- [ ] Choose fix option (recommend: Option 3)
- [ ] Rename `src/test_runner.py` to `src/runner.py`
- [ ] Update imports in `tests/test_schemas.py`
- [ ] Update any README/documentation references
- [ ] Run tests to verify warning is gone
- [ ] Add to CHANGELOG

---

## Related Issues

None

---

## References

- [Pytest Test Discovery](https://docs.pytest.org/en/stable/goodpractices.html#test-discovery)
- [Pytest Collection](https://docs.pytest.org/en/stable/example/pythoncollection.html)
- [Pytest Warnings](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)

---

**Last Updated**: 2026-02-06
**Reporter**: Weaviate Schema Testing Framework
**Priority**: P3 (Low - Cosmetic)
