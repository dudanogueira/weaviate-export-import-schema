using Newtonsoft.Json.Linq;
using System;
using System.IO;
using System.Threading.Tasks;
using Xunit;
using Xunit.Abstractions;

namespace WeaviateSchemaTest;

/// <summary>
/// xUnit tests for Weaviate schema import/export validation.
/// Tests all P0 schemas across the C# client.
/// </summary>
public class SchemaTests : IAsyncLifetime
{
    private readonly ITestOutputHelper _output;
    private SchemaTestRunner? _testRunner;
    private readonly SchemaComparator _comparator;
    private readonly string _weaviateUrl;
    private readonly string _baselineDir;
    private readonly string _outputDir;

    public SchemaTests(ITestOutputHelper output)
    {
        _output = output;
        _weaviateUrl = Environment.GetEnvironmentVariable("WEAVIATE_URL") ?? "localhost";

        // Get paths relative to project root, not bin directory
        var projectRoot = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../../"));
        _baselineDir = Path.Combine(projectRoot, "schemas");
        _outputDir = Path.Combine(projectRoot, "test-results/exported-schemas");

        _comparator = new SchemaComparator();

        _output.WriteLine("Setting up C# test environment");
        _output.WriteLine($"Weaviate URL: {_weaviateUrl}");
        _output.WriteLine($"Baseline dir: {_baselineDir}");

        // Create output directory
        Directory.CreateDirectory(Path.Combine(_outputDir, "csharp"));
    }

    public async Task InitializeAsync()
    {
        _testRunner = await SchemaTestRunner.CreateAsync(_weaviateUrl);
        _output.WriteLine("SchemaTestRunner initialized");
    }

    public Task DisposeAsync()
    {
        _output.WriteLine("C# test teardown complete");
        return Task.CompletedTask;
    }

    [Theory]
    [InlineData("P0-basic-text-only")]
    [InlineData("P0-single-named-vector")]
    [InlineData("P0-multi-named-vectors")]
    public async Task TestSchemaImportExport(string schemaName)
    {
        Assert.NotNull(_testRunner);

        _output.WriteLine("");
        _output.WriteLine("========================================");
        _output.WriteLine($"Testing schema: {schemaName}");
        _output.WriteLine("========================================");

        // 1. Load baseline schema
        var baselinePath = Path.Combine(_baselineDir, schemaName, "config.json");
        var baseline = _testRunner.LoadSchema(baselinePath);
        _output.WriteLine($"Loaded baseline schema from: {baselinePath}");

        // 2. Import schema to Weaviate
        var className = await _testRunner.ImportSchema(baseline);
        _output.WriteLine($"Imported schema with class: {className}");

        // 3. Export schema from Weaviate
        var exported = await _testRunner.ExportSchema(className);
        _output.WriteLine("Exported schema from Weaviate");

        // 4. Save exported schema
        var outputPath = Path.Combine(_outputDir, "csharp", schemaName, "config.json");
        _testRunner.SaveSchema(exported, outputPath);
        _output.WriteLine($"Saved exported schema to: {outputPath}");

        // 5. Compare baseline vs exported
        var result = _comparator.CompareSchemas(baseline, exported, schemaName);

        // 6. Cleanup
        await _testRunner.Cleanup(className);
        _output.WriteLine($"Cleaned up class: {className}");

        // 7. Assert schemas match
        if (!result.IsMatch)
        {
            _output.WriteLine("Schema mismatch detected!");
            _output.WriteLine($"Differences: {JObject.FromObject(result.Differences).ToString()}");

            Assert.Fail($"Schema mismatch for {schemaName}. Differences: {result.Differences.Count}");
        }

        _output.WriteLine($"✓ Schema {schemaName} passed validation");
    }

    [Theory]
    [InlineData("P0-basic-text-only")]
    [InlineData("P0-single-named-vector")]
    [InlineData("P0-multi-named-vectors")]
    public async Task TestFullWorkflow(string schemaName)
    {
        Assert.NotNull(_testRunner);

        _output.WriteLine("");
        _output.WriteLine("========================================");
        _output.WriteLine($"Testing full workflow for: {schemaName}");
        _output.WriteLine("========================================");

        var baselinePath = Path.Combine(_baselineDir, schemaName, "config.json");

        var result = await _testRunner.RunTest(baselinePath, _outputDir, schemaName);

        if (!result.Success)
        {
            _output.WriteLine($"Test failed for {schemaName}: {result.Error}");
            Assert.Fail($"Test failed for {schemaName}: {result.Error}");
        }

        _output.WriteLine($"✓ Full workflow for {schemaName} completed successfully");
        _output.WriteLine($"Exported to: {result.ExportedPath}");
    }

    [Fact]
    public void TestSchemaNormalization()
    {
        _output.WriteLine("Testing schema normalization");

        var testSchema = @"{
            ""name"": ""Test"",
            ""properties"": [
                {""name"": ""z_prop""},
                {""name"": ""a_prop""}
            ],
            ""creationTimeUnix"": 123456789,
            ""lastUpdateTimeUnix"": 987654321
        }";

        var schema = JObject.Parse(testSchema);
        var normalized = _comparator.NormalizeSchema(schema);

        // Verify timestamps removed
        Assert.False(normalized.ContainsKey("creationTimeUnix"), "creationTimeUnix should be removed");
        Assert.False(normalized.ContainsKey("lastUpdateTimeUnix"), "lastUpdateTimeUnix should be removed");

        // Verify properties sorted (a_prop should come before z_prop)
        if (normalized["properties"] is JArray properties && properties.Count >= 2)
        {
            var firstName = properties[0]["name"]?.ToString();
            Assert.Equal("a_prop", firstName);
        }

        _output.WriteLine("✓ Schema normalization test passed");
    }

    [Fact]
    public void TestComparatorIdenticalSchemas()
    {
        _output.WriteLine("Testing comparator with identical schemas");

        var schema1 = JObject.Parse(@"{""name"":""Test"",""description"":""A test schema""}");
        var schema2 = JObject.Parse(@"{""name"":""Test"",""description"":""A test schema""}");

        var result = _comparator.CompareSchemas(schema1, schema2, "test");

        Assert.True(result.IsMatch, "Identical schemas should match");
        Assert.Empty(result.Differences);

        _output.WriteLine("✓ Comparator identical schemas test passed");
    }

    [Fact]
    public void TestComparatorDifferentSchemas()
    {
        _output.WriteLine("Testing comparator with different schemas");

        var schema1 = JObject.Parse(@"{""name"":""Test1"",""description"":""Schema one""}");
        var schema2 = JObject.Parse(@"{""name"":""Test2"",""description"":""Schema two""}");

        var result = _comparator.CompareSchemas(schema1, schema2, "test");

        Assert.False(result.IsMatch, "Different schemas should not match");
        Assert.NotEmpty(result.Differences);

        _output.WriteLine("✓ Comparator different schemas test passed");
        _output.WriteLine($"Differences found: {result.Differences.Count}");
    }
}
