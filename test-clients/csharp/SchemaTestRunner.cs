using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Weaviate.Client;

namespace WeaviateSchemaTest;

/// <summary>
/// Test runner for importing and exporting Weaviate schemas.
/// </summary>
public class SchemaTestRunner
{
    private readonly WeaviateClient _client;
    private readonly string _weaviateUrl;

    private SchemaTestRunner(WeaviateClient client, string weaviateUrl)
    {
        _client = client;
        _weaviateUrl = weaviateUrl;
    }

    /// <summary>
    /// Create a new SchemaTestRunner connected to local Weaviate.
    /// </summary>
    public static async Task<SchemaTestRunner> CreateAsync(string weaviateUrl = "localhost")
    {
        var client = await Connect.Local();
        return new SchemaTestRunner(client, weaviateUrl);
    }

    /// <summary>
    /// Load a schema from JSON file.
    /// </summary>
    public JObject LoadSchema(string schemaPath)
    {
        Console.WriteLine($"Loading schema from: {schemaPath}");
        var json = File.ReadAllText(schemaPath);
        return JObject.Parse(json);
    }

    /// <summary>
    /// Import a schema into Weaviate by creating a collection.
    /// </summary>
    public async Task<string> ImportSchema(JObject schema)
    {
        var collectionName = schema["name"]?.ToString();

        if (string.IsNullOrEmpty(collectionName))
        {
            throw new ArgumentException("Schema missing 'name' field");
        }

        Console.WriteLine($"Importing collection: {collectionName}");

        // Delete if exists
        try
        {
            var exists = await _client.Collections.Exists(collectionName);
            if (exists)
            {
                Console.WriteLine($"Deleting existing collection: {collectionName}");
                await _client.Collections.Delete(collectionName);
            }
        }
        catch
        {
            // Collection doesn't exist, which is fine
        }

        // Create the collection using JSON
        var jsonString = schema.ToString();
        await _client.Collections.CreateFromJson(jsonString);

        Console.WriteLine($"Successfully imported collection: {collectionName}");
        return collectionName;
    }

    /// <summary>
    /// Export a collection's schema configuration.
    /// </summary>
    public async Task<JObject> ExportSchema(string collectionName)
    {
        Console.WriteLine($"Exporting schema for collection: {collectionName}");

        var exportedConfig = await _client.Collections.Export(collectionName);

        if (exportedConfig == null)
        {
            throw new Exception($"Failed to export collection: {collectionName}");
        }

        // Convert CollectionConfigExport to JSON string then to JObject
        var jsonString = System.Text.Json.JsonSerializer.Serialize(exportedConfig);
        var exported = JObject.Parse(jsonString);

        Console.WriteLine($"Exported schema for collection: {collectionName}");
        return exported;
    }

    /// <summary>
    /// Save schema to JSON file.
    /// </summary>
    public void SaveSchema(JObject schema, string outputPath)
    {
        var directory = Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }

        File.WriteAllText(outputPath, schema.ToString(Formatting.Indented));

        Console.WriteLine($"Saved schema to: {outputPath}");
    }

    /// <summary>
    /// Delete a collection from Weaviate.
    /// </summary>
    public async Task Cleanup(string collectionName)
    {
        try
        {
            var exists = await _client.Collections.Exists(collectionName);
            if (exists)
            {
                await _client.Collections.Delete(collectionName);
                Console.WriteLine($"Cleaned up collection: {collectionName}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to cleanup collection: {ex.Message}");
        }
    }

    /// <summary>
    /// Run a complete import/export test.
    /// </summary>
    public async Task<TestResult> RunTest(string baselinePath, string outputDir, string schemaName)
    {
        var result = new TestResult(schemaName);

        try
        {
            // Load baseline
            var baseline = LoadSchema(baselinePath);

            // Import schema
            var collectionName = await ImportSchema(baseline);

            // Export schema
            var exported = await ExportSchema(collectionName);

            // Save exported schema
            var outputPath = Path.Combine(outputDir, "csharp", schemaName, "config.json");
            SaveSchema(exported, outputPath);

            result.Success = true;
            result.ExportedPath = outputPath;

            // Cleanup
            await Cleanup(collectionName);
        }
        catch (Exception ex)
        {
            result.Success = false;
            result.Error = ex.Message;
            Console.WriteLine($"Test failed for {schemaName}: {ex.Message}");
        }

        return result;
    }
}

/// <summary>
/// Result of a test run.
/// </summary>
public class TestResult
{
    public string SchemaName { get; }
    public bool Success { get; set; }
    public string? Error { get; set; }
    public string? ExportedPath { get; set; }

    public TestResult(string schemaName)
    {
        SchemaName = schemaName;
        Success = false;
    }
}
