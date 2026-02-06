using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Linq;

namespace WeaviateSchemaTest;

/// <summary>
/// Schema comparison engine for validating import/export consistency.
/// </summary>
public class SchemaComparator
{
    // Fields to ignore during comparison (timestamps, internal IDs, etc.)
    private static readonly HashSet<string> IgnoreFields = new()
    {
        "creationTimeUnix",
        "lastUpdateTimeUnix"
    };

    /// <summary>
    /// Normalize a schema by removing internal fields and applying defaults.
    /// </summary>
    public JObject NormalizeSchema(JObject schema)
    {
        var normalized = (JObject)schema.DeepClone();

        // Remove timestamp fields
        foreach (var field in IgnoreFields)
        {
            normalized.Remove(field);
        }

        // Sort properties by name for consistent comparison
        if (normalized["properties"] is JArray properties)
        {
            var sortedProps = properties
                .OrderBy(p => p["name"]?.ToString() ?? "")
                .ToList();

            normalized["properties"] = new JArray(sortedProps);
        }

        // Sort vectorConfig keys if present
        if (normalized["vectorConfig"] is JObject vectorConfig)
        {
            var sortedVectorConfig = new JObject(
                vectorConfig.Properties()
                    .OrderBy(p => p.Name)
                    .Select(p => new JProperty(p.Name, p.Value))
            );

            normalized["vectorConfig"] = sortedVectorConfig;
        }

        return normalized;
    }

    /// <summary>
    /// Compare two schemas and report differences.
    /// </summary>
    /// <param name="baseline">Baseline schema (source of truth)</param>
    /// <param name="exported">Exported schema to compare</param>
    /// <param name="schemaName">Name of schema for reporting</param>
    /// <returns>ComparisonResult containing match status and differences</returns>
    public ComparisonResult CompareSchemas(JObject baseline, JObject exported, string schemaName)
    {
        Console.WriteLine($"Comparing schemas for: {schemaName}");

        // Normalize both schemas
        var normBaseline = NormalizeSchema(baseline);
        var normExported = NormalizeSchema(exported);

        // Check for equality
        if (JToken.DeepEquals(normBaseline, normExported))
        {
            Console.WriteLine($"✓ Schemas match perfectly: {schemaName}");
            return new ComparisonResult(true, new Dictionary<string, object>());
        }

        // Find differences
        var differences = FindDifferences(normBaseline, normExported, "root");

        Console.WriteLine($"✗ Schemas differ: {schemaName}");
        Console.WriteLine($"Differences: {differences.Count}");

        return new ComparisonResult(false, differences);
    }

    /// <summary>
    /// Find differences between two JSON tokens.
    /// </summary>
    private Dictionary<string, object> FindDifferences(JToken obj1, JToken obj2, string path)
    {
        var differences = new Dictionary<string, object>();

        if (obj1.Type != obj2.Type)
        {
            differences[path] = new Dictionary<string, object>
            {
                ["type"] = "type_mismatch",
                ["value1"] = obj1.Type.ToString(),
                ["value2"] = obj2.Type.ToString()
            };
            return differences;
        }

        if (obj1 is JObject jobj1 && obj2 is JObject jobj2)
        {
            var allKeys = new HashSet<string>(jobj1.Properties().Select(p => p.Name));
            allKeys.UnionWith(jobj2.Properties().Select(p => p.Name));

            foreach (var key in allKeys)
            {
                if (!jobj1.ContainsKey(key))
                {
                    differences[$"{path}.{key}"] = new Dictionary<string, object>
                    {
                        ["type"] = "missing_in_first",
                        ["value2"] = jobj2[key]
                    };
                }
                else if (!jobj2.ContainsKey(key))
                {
                    differences[$"{path}.{key}"] = new Dictionary<string, object>
                    {
                        ["type"] = "missing_in_second",
                        ["value1"] = jobj1[key]
                    };
                }
                else
                {
                    var childDiffs = FindDifferences(jobj1[key]!, jobj2[key]!, $"{path}.{key}");
                    foreach (var diff in childDiffs)
                    {
                        differences[diff.Key] = diff.Value;
                    }
                }
            }
        }
        else if (obj1 is JArray jarr1 && obj2 is JArray jarr2)
        {
            if (jarr1.Count != jarr2.Count)
            {
                differences[path] = new Dictionary<string, object>
                {
                    ["type"] = "array_length_mismatch",
                    ["length1"] = jarr1.Count,
                    ["length2"] = jarr2.Count
                };
            }

            int maxLen = Math.Max(jarr1.Count, jarr2.Count);
            for (int i = 0; i < maxLen; i++)
            {
                if (i < jarr1.Count && i < jarr2.Count)
                {
                    var childDiffs = FindDifferences(jarr1[i], jarr2[i], $"{path}[{i}]");
                    foreach (var diff in childDiffs)
                    {
                        differences[diff.Key] = diff.Value;
                    }
                }
            }
        }
        else
        {
            if (!JToken.DeepEquals(obj1, obj2))
            {
                differences[path] = new Dictionary<string, object>
                {
                    ["type"] = "value_mismatch",
                    ["value1"] = obj1,
                    ["value2"] = obj2
                };
            }
        }

        return differences;
    }
}

/// <summary>
/// Result of a schema comparison.
/// </summary>
public class ComparisonResult
{
    public bool IsMatch { get; }
    public Dictionary<string, object> Differences { get; }

    public ComparisonResult(bool match, Dictionary<string, object> differences)
    {
        IsMatch = match;
        Differences = differences;
    }
}
