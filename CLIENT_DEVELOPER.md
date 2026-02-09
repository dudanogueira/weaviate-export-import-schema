# Client Developer Guide

This guide shows how to add local Weaviate client folders as dependencies to this project, enabling you to:
- Edit client library code directly
- Test changes against the framework's test suite
- Debug client-specific issues
- Develop client features alongside validation tests

## Overview

When developing or debugging Weaviate client libraries, you often need to:
1. Make changes to the client code
2. Test those changes against real-world scenarios
3. Iterate quickly without publishing packages

This framework can use **local, editable client installations** instead of published packages from PyPI or npm.

### Schema Compatibility (v3 vs v4)

The framework supports both **v3 (legacy)** and **v4** schema formats:
- **v3 format**: Uses `"class"` field for collection name
- **v4 format**: Uses `"name"` field for collection name

The test runners and comparators automatically handle both formats, allowing you to:
- Test backward compatibility scenarios
- Migrate schemas from v3 to v4 format
- Import/export schemas regardless of which field name is used

## Prerequisites

- Client repository cloned locally (e.g., `weaviate-python` or `weaviate-typescript-client`)
- Basic understanding of your package manager (pip, npm)
- Docker running (for Weaviate instance)

---

## Python Client Setup

### Step 1: Clone the Python Client

```bash
# Clone to a location of your choice
cd ~/dev/weaviate  # or wherever you keep your projects
git clone https://github.com/weaviate/weaviate-python.git weaviate-python-client
cd weaviate-python-client

# Checkout the branch you want to work on
git checkout main  # or your feature branch
```

**Note:** The repository is `weaviate-python` but we're cloning it as `weaviate-python-client` for consistency.

### Step 2: Install Client as Editable Dependency

Navigate to your test client directory and install the local client:

```bash
cd /path/to/weaviate-export-import-schema/test-clients/python

# Activate virtual environment
source .venv/bin/activate

# Install your local client in editable mode
# IMPORTANT: Use absolute path - pip doesn't always expand ~ correctly
pip install -e $HOME/dev/weaviate/weaviate-python-client

# Or use the full absolute path:
pip install -e /Users/yourusername/dev/weaviate/weaviate-python-client
```

**What this does:**
- `-e` flag installs the package in "editable" mode
- Changes to the client code are immediately available without reinstalling
- The installed package points to your local directory

**⚠️ Path Tips:**
- Use `$HOME` instead of `~` for better compatibility
- Or use absolute paths: `/Users/yourusername/...`
- The tilde (`~`) expansion doesn't always work reliably with pip

### Step 3: Verify Installation

```bash
# Check that weaviate-client points to your local directory
pip show weaviate-client

# You should see something like:
# Location: /Users/yourusername/dev/weaviate/weaviate-python-client
# or: Editable project location: /Users/yourusername/dev/weaviate/weaviate-python-client
```

### Step 4: Run Tests

```bash
# Run all Python tests
pytest -v

# Run specific test
pytest -v tests/test_schemas.py::test_schema_import_export[P0-basic-text-only]

# Run with detailed output
pytest -vv --tb=long
```

### Step 5: Make Changes and Test

1. Edit files in `$HOME/dev/weaviate/weaviate-python-client/weaviate/...`
2. Run tests immediately - changes are live!
3. No need to reinstall

```bash
# Example workflow
# 1. Edit client code
vim $HOME/dev/weaviate/weaviate-python-client/weaviate/collections/classes/config.py

# 2. Run tests immediately (from test-clients/python directory)
cd /path/to/weaviate-export-import-schema/test-clients/python
pytest -v tests/test_schemas.py

# 3. Iterate!
```

### Step 6: Revert to Published Package

When you're done developing:

```bash
# Uninstall the editable version
pip uninstall weaviate-client

# Reinstall from PyPI
pip install -r requirements.txt
```

---

## TypeScript/Node.js Client Setup

### Step 1: Clone the TypeScript Client

```bash
# Clone to a location of your choice
cd ~/dev/weaviate
git clone https://github.com/weaviate/typescript-client.git
cd typescript-client

# Checkout the branch you want to work on
git checkout main  # or your feature branch
```

### Step 2: Build the Client

The TypeScript client needs to be built before use:

```bash
cd ~/dev/weaviate/typescript-client

# Install dependencies
npm install

# Build the client
npm run build
```

### Step 3: Link the Local Client

You have two options:

#### Option A: npm link (Recommended)

```bash
# 1. Create a global link from the client
cd ~/dev/weaviate/typescript-client
npm link

# 2. Use the link in test-clients
cd /path/to/weaviate-export-import-schema/test-clients/typescript
npm link weaviate-client
```

#### Option B: Direct Path in package.json

Edit `test-clients/typescript/package.json`:

```json
{
  "dependencies": {
    "weaviate-client": "file:~/dev/weaviate/typescript-client"
  }
}
```

Then run:

```bash
cd /path/to/weaviate-export-import-schema/test-clients/typescript
npm install
```

### Step 4: Verify Installation

```bash
# Check that weaviate-client points to your local directory
npm ls weaviate-client

# You should see a symlink or file: reference to your local directory
```

### Step 5: Run Tests

```bash
# Run all TypeScript tests
npm test

# Run tests in watch mode (auto-rerun on changes)
npm run test:watch

# Run specific test file
npx vitest run tests/schemas.test.ts
```

### Step 6: Make Changes and Test

**Important:** TypeScript needs to be recompiled after changes!

```bash
# Terminal 1: Watch mode in client directory
cd ~/dev/weaviate/typescript-client
npm run build:watch  # or npm run dev if available

# Terminal 2: Test runner in watch mode
cd /path/to/weaviate-export-import-schema/test-clients/typescript
npm run test:watch
```

**Workflow:**
1. Edit TypeScript files in `~/dev/weaviate/typescript-client/src/...`
2. Build process automatically recompiles (if using watch mode)
3. Tests automatically re-run (if using test watch mode)

**Manual workflow** (if not using watch mode):
```bash
# 1. Edit client code
vim ~/dev/weaviate/typescript-client/src/collections/configure/types/index.ts

# 2. Rebuild client
cd ~/dev/weaviate/typescript-client && npm run build

# 3. Run tests
cd /path/to/weaviate-export-import-schema/test-clients/typescript && npm test
```

### Step 7: Revert to Published Package

#### If using npm link:

```bash
cd /path/to/weaviate-export-import-schema/test-clients/typescript

# Unlink
npm unlink weaviate-client

# Reinstall from npm registry
npm install weaviate-client@^3.2.0
```

#### If using file: path:

```bash
# Edit package.json back to version number
# Change:  "weaviate-client": "file:~/dev/weaviate/typescript-client"
# To:      "weaviate-client": "^3.2.0"

# Reinstall
npm install
```

---

## Java Client Setup

### Step 1: Clone the Java Client

```bash
cd ~/dev/weaviate
git clone https://github.com/weaviate/java-client.git
cd java-client
```

### Step 2: Build and Install to Local Maven Repository

```bash
cd ~/dev/weaviate/java-client

# Build and install to local Maven cache
mvn clean install -DskipTests
```

### Step 3: Update pom.xml in test-clients/java

Edit `test-clients/java/pom.xml` to use your local snapshot:

```xml
<dependencies>
    <dependency>
        <groupId>io.weaviate</groupId>
        <artifactId>client</artifactId>
        <!-- Use SNAPSHOT version from local Maven repo -->
        <version>4.9.0-SNAPSHOT</version>
    </dependency>
</dependencies>
```

### Step 4: Run Tests

```bash
cd /path/to/weaviate-export-import-schema/test-clients/java

# Run tests
mvn test

# Run specific test
mvn test -Dtest=SchemaImportExportTest
```

### Step 5: Make Changes and Test

```bash
# 1. Edit Java client code
vim ~/dev/weaviate/java-client/src/main/java/io/weaviate/client/...

# 2. Rebuild and install
cd ~/dev/weaviate/java-client
mvn clean install -DskipTests

# 3. Run tests
cd /path/to/weaviate-export-import-schema/test-clients/java
mvn test
```

### Step 6: Revert to Published Package

Edit `test-clients/java/pom.xml` back to the release version:

```xml
<version>4.8.1</version>  <!-- or whatever release version -->
```

---

## C# Client Setup

### Step 1: Clone the C# Client

```bash
cd ~/dev/weaviate
git clone https://github.com/weaviate/weaviate-dotnet-client.git
cd weaviate-dotnet-client
```

### Step 2: Build the Client

```bash
cd ~/dev/weaviate/weaviate-dotnet-client
dotnet build
```

### Step 3: Reference Local Project

Edit `test-clients/csharp/WeaviateSchemaTests.csproj`:

```xml
<ItemGroup>
    <!-- Comment out or remove the PackageReference -->
    <!-- <PackageReference Include="Weaviate.Client" Version="1.0.0" /> -->

    <!-- Add ProjectReference to local client -->
    <ProjectReference Include="~/dev/weaviate/weaviate-dotnet-client/src/Weaviate.Client/Weaviate.Client.csproj" />
</ItemGroup>
```

### Step 4: Restore and Run Tests

```bash
cd /path/to/weaviate-export-import-schema/test-clients/csharp

# Restore dependencies
dotnet restore

# Run tests
dotnet test
```

### Step 5: Make Changes and Test

```bash
# 1. Edit C# client code
vim ~/dev/weaviate/weaviate-dotnet-client/src/Weaviate.Client/...

# 2. Run tests (will automatically rebuild dependencies)
cd /path/to/weaviate-export-import-schema/test-clients/csharp
dotnet test
```

### Step 6: Revert to Published Package

Edit `test-clients/csharp/WeaviateSchemaTests.csproj`:

```xml
<ItemGroup>
    <!-- Restore PackageReference -->
    <PackageReference Include="Weaviate.Client" Version="1.0.0" />

    <!-- Remove ProjectReference -->
    <!-- <ProjectReference Include="..." /> -->
</ItemGroup>
```

---

## Running Framework Tests with Local Clients

### All Tests with Local Clients

Assuming you have set up local clients as described above:

```bash
# Start Weaviate
docker-compose -f docker/docker-compose.yml up -d

# Wait for Weaviate to be ready
curl http://localhost:8080/v1/.well-known/ready

# Run all client tests
./scripts/run_all_tests.sh
```

### Individual Client Tests

```bash
# Python
cd test-clients/python
source .venv/bin/activate
pytest -v

# TypeScript
cd test-clients/typescript
npm test

# Java
cd test-clients/java
mvn test

# C#
cd test-clients/csharp
dotnet test
```

---

## Debugging Tips

### Python Client

**Using pdb debugger:**

```python
# Add to test or client code
import pdb; pdb.set_trace()
```

**Using VS Code:**

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Pytest",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "tests/test_schemas.py"],
      "cwd": "${workspaceFolder}/test-clients/python",
      "console": "integratedTerminal"
    }
  ]
}
```

### TypeScript Client

**Using VS Code:**

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "TypeScript: Vitest",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "test"],
      "cwd": "${workspaceFolder}/test-clients/typescript",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Common Issues and Solutions

### Python: "Module not found" after installing editable package

**Solution:**
```bash
# Ensure you're in the right virtual environment
which python  # Should point to .venv/bin/python

# Reinstall in editable mode with absolute path
pip install -e $HOME/dev/weaviate/weaviate-python-client
```

### Python: "Not a valid editable requirement" error

**Problem:** Error like `ERROR: /path is not a valid editable requirement`

**Solutions:**
```bash
# 1. Don't use ~ (tilde), use $HOME instead
pip install -e $HOME/dev/weaviate/weaviate-python-client

# 2. Or use absolute path
pip install -e /Users/yourusername/dev/weaviate/weaviate-python-client

# 3. Check the directory exists and has setup.py or pyproject.toml
ls -la $HOME/dev/weaviate/weaviate-python-client/
```

### TypeScript: "Cannot find module 'weaviate-client'"

**Solution:**
```bash
# Verify link
npm ls weaviate-client

# If link is broken, recreate it
npm unlink weaviate-client
cd ~/dev/weaviate/typescript-client && npm link
cd /path/to/test-clients/typescript && npm link weaviate-client
```

### TypeScript: Changes not reflected after editing client

**Solution:**
```bash
# Make sure to rebuild the TypeScript client after changes
cd ~/dev/weaviate/typescript-client
npm run build

# Better: use watch mode
npm run build:watch
```

### Java: "Package does not exist" after local install

**Solution:**
```bash
# Ensure local build succeeded
cd ~/dev/weaviate/java-client
mvn clean install -DskipTests

# Check local Maven repository
ls ~/.m2/repository/io/weaviate/client/

# Force update in test project
cd test-clients/java
mvn clean
mvn dependency:resolve
```

### C#: "Project reference not found"

**Solution:**
```bash
# Use absolute path in .csproj
<ProjectReference Include="/absolute/path/to/weaviate-dotnet-client/src/Weaviate.Client/Weaviate.Client.csproj" />

# Or use relative path
<ProjectReference Include="../../../../weaviate-dotnet-client/src/Weaviate.Client/Weaviate.Client.csproj" />
```

---

## Multi-Client Development Workflow

When working on issues that span multiple clients:

### 1. Set up all local clients

```bash
# Python
cd test-clients/python
source .venv/bin/activate
pip install -e $HOME/dev/weaviate/weaviate-python-client

# TypeScript
cd test-clients/typescript
npm link weaviate-client

# Java (if needed)
cd $HOME/dev/weaviate/java-client
mvn install -DskipTests

# C# (if needed)
# Edit .csproj to reference local project
```

### 2. Run tests to reproduce the issue

```bash
# Run all tests
./scripts/run_all_tests.sh

# Or run specific client tests
cd test-clients/python && pytest -v
cd test-clients/typescript && npm test
```

### 3. Make changes to client(s)

```bash
# Python: Edit and test immediately
vim $HOME/dev/weaviate/weaviate-python-client/weaviate/collections/...
cd test-clients/python && pytest -v

# TypeScript: Edit, build, test
vim $HOME/dev/weaviate/typescript-client/src/collections/...
cd $HOME/dev/weaviate/typescript-client && npm run build
cd test-clients/typescript && npm test
```

### 4. Compare results

```bash
python scripts/compare_results.py
cat test-results/comparisons/report.md
```

---

## VSCode Multi-Root Workspace Setup

For an optimal development experience, create a multi-root workspace:

Create `weaviate-dev.code-workspace`:

```json
{
  "folders": [
    {
      "name": "Test Framework",
      "path": "."
    },
    {
      "name": "Python Client",
      "path": "../weaviate-python"
    },
    {
      "name": "TypeScript Client",
      "path": "../typescript-client"
    }
  ],
  "settings": {
    "files.exclude": {
      "**/.venv": false,
      "**/node_modules": false
    }
  }
}
```

**Benefits:**
- Edit client code and tests in the same window
- Use "Go to Definition" across projects
- Unified search across all codebases
- Single debug configuration file

---

## Best Practices

### 1. Branch Management

Keep client branches in sync with test framework needs:

```bash
# Create feature branches in both repos
cd $HOME/dev/weaviate/weaviate-python-client
git checkout -b fix-export-bug

cd $HOME/dev/weaviate/weaviate-export-import-schema
git checkout -b fix-export-bug
```

### 2. Version Tracking

Document which client versions you're testing:

```bash
# Add to your commit messages
git commit -m "Test fix with weaviate-python@fix-export-bug"
```

### 3. Clean State

Reset to clean state between major changes:

```bash
# Python
pip uninstall weaviate-client
pip install -r requirements.txt

# TypeScript
npm unlink weaviate-client
rm -rf node_modules package-lock.json
npm install

# Start fresh
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

### 4. Test Isolation

Run tests in isolation when debugging:

```bash
# Python: Single test
pytest -v tests/test_schemas.py::test_schema_import_export[P0-basic-text-only]

# TypeScript: Single test
npx vitest run tests/schemas.test.ts -t "P0-basic-text-only"
```

---

## CI/CD Considerations

**Note:** GitHub Actions workflows use published packages, not local editable installations.

To test local client changes in CI:

1. Fork the client repository
2. Push your changes to your fork
3. Update test client dependencies to point to your fork:

```json
// TypeScript example in package.json
{
  "dependencies": {
    "weaviate-client": "github:your-username/typescript-client#your-branch"
  }
}
```

```txt
# Python example in requirements.txt
git+https://github.com/your-username/weaviate-python@your-branch
```

### ⚠️ IMPORTANT: TypeScript GitHub Installations Require Build

**Critical for TypeScript Client Developers:**

When installing a TypeScript client from GitHub (not npm registry), npm **does not automatically run build scripts**. This means the client code won't be compiled and tests will fail with module resolution errors.

**Problem:**
```bash
npm install github:username/typescript-client#branch-name
npm test
# Error: Failed to resolve entry for package "weaviate-client"
# The package may have incorrect main/module/exports specified
```

**Solution:**

Your forked TypeScript client repository **MUST** include a `prepare` script in `package.json` to auto-build on installation:

```json
{
  "name": "weaviate-client",
  "scripts": {
    "prepare": "npm run build",
    "prepack": "npm run build",
    "build": "npm run build:node",
    "build:node": "npm run lint && npm run build:cjs && npm run build:esm && prettier --write --no-error-on-unmatched-pattern '**/dist/**/*.{ts,js}'"
  }
}
```

**Key Points:**

1. **`prepare` script**: Runs automatically after `npm install` from GitHub
2. **`prepack` script**: Runs before creating a package (for npm publish)
3. **Both are needed**: `prepare` for GitHub installs, `prepack` for npm publish

**Why This Matters:**

- ✅ Local file installations (`file:/path/to/client`) work because you manually built
- ❌ GitHub installations (`github:user/repo#branch`) fail without `prepare`
- ✅ npm registry installations work because they include pre-built `dist/` files

**Verification:**

After adding the `prepare` script to your fork:

```bash
# Test that GitHub installation works
cd test-clients/typescript
npm install
npm test  # Should now work without manual build!
```

**Alternative (Not Recommended):**

If you cannot modify the client repository, you can commit built files (`dist/`) to your branch, but this is not recommended because:
- Bloats the repository with generated files
- Creates merge conflicts
- Goes against TypeScript best practices

---

## Summary

You now know how to:
- ✅ Install local client libraries as editable dependencies
- ✅ Run framework tests against local client code
- ✅ Iterate quickly on client changes
- ✅ Debug issues across client implementations
- ✅ Set up an efficient development environment

**Quick Reference:**

| Client     | Install Command                                          | Test Command |
|------------|----------------------------------------------------------|--------------|
| Python     | `pip install -e $HOME/dev/weaviate/weaviate-python-client` | `pytest -v`  |
| TypeScript | `npm link weaviate-client`                               | `npm test`   |
| Java       | `mvn install -DskipTests` (in client repo)               | `mvn test`   |
| C#         | Edit `.csproj` with `ProjectReference`                   | `dotnet test`|

Happy developing! 🚀
