/**
 * Schema comparison engine for validating import/export consistency.
 */

export interface ComparisonResult {
  match: boolean;
  differences: any;
}

export class SchemaComparator {
  /**
   * Normalize a schema by removing internal fields and applying defaults.
   */
  normalizeSchema(schema: any): any {
    // Deep clone
    const normalized = JSON.parse(JSON.stringify(schema));

    // Remove timestamp fields
    delete normalized.creationTimeUnix;
    delete normalized.lastUpdateTimeUnix;

    // Sort properties by name for consistent comparison
    if (normalized.properties) {
      normalized.properties = normalized.properties.sort((a: any, b: any) =>
        (a.name || '').localeCompare(b.name || '')
      );
    }

    // Sort vectorConfig keys if present
    if (normalized.vectorConfig) {
      const sorted: any = {};
      Object.keys(normalized.vectorConfig)
        .sort()
        .forEach((key) => {
          sorted[key] = normalized.vectorConfig[key];
        });
      normalized.vectorConfig = sorted;
    }

    return normalized;
  }

  /**
   * Deep equality check for objects.
   */
  private deepEqual(obj1: any, obj2: any): boolean {
    return JSON.stringify(obj1) === JSON.stringify(obj2);
  }

  /**
   * Find differences between two objects.
   */
  private findDifferences(obj1: any, obj2: any, path: string = 'root'): any[] {
    const differences: any[] = [];

    if (typeof obj1 !== typeof obj2) {
      differences.push({
        path,
        type: 'type_mismatch',
        value1: typeof obj1,
        value2: typeof obj2,
      });
      return differences;
    }

    if (obj1 === null || obj2 === null) {
      if (obj1 !== obj2) {
        differences.push({
          path,
          type: 'value_mismatch',
          value1: obj1,
          value2: obj2,
        });
      }
      return differences;
    }

    if (typeof obj1 !== 'object') {
      if (obj1 !== obj2) {
        differences.push({
          path,
          type: 'value_mismatch',
          value1: obj1,
          value2: obj2,
        });
      }
      return differences;
    }

    // Handle arrays
    if (Array.isArray(obj1) && Array.isArray(obj2)) {
      if (obj1.length !== obj2.length) {
        differences.push({
          path,
          type: 'array_length_mismatch',
          length1: obj1.length,
          length2: obj2.length,
        });
      }

      const maxLen = Math.max(obj1.length, obj2.length);
      for (let i = 0; i < maxLen; i++) {
        const itemDiffs = this.findDifferences(
          obj1[i],
          obj2[i],
          `${path}[${i}]`
        );
        differences.push(...itemDiffs);
      }

      return differences;
    }

    // Handle objects
    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);
    const allKeys = new Set([...keys1, ...keys2]);

    for (const key of allKeys) {
      if (!(key in obj1)) {
        differences.push({
          path: `${path}.${key}`,
          type: 'missing_in_first',
          value2: obj2[key],
        });
      } else if (!(key in obj2)) {
        differences.push({
          path: `${path}.${key}`,
          type: 'missing_in_second',
          value1: obj1[key],
        });
      } else {
        const itemDiffs = this.findDifferences(
          obj1[key],
          obj2[key],
          `${path}.${key}`
        );
        differences.push(...itemDiffs);
      }
    }

    return differences;
  }

  /**
   * Compare two schemas and report differences.
   */
  compareSchemas(
    baseline: any,
    exported: any,
    schemaName: string = 'schema'
  ): ComparisonResult {
    console.log(`Comparing schemas for: ${schemaName}`);

    // Normalize both schemas
    const normBaseline = this.normalizeSchema(baseline);
    const normExported = this.normalizeSchema(exported);

    // Check for equality
    if (this.deepEqual(normBaseline, normExported)) {
      console.log(`✓ Schemas match perfectly: ${schemaName}`);
      return { match: true, differences: {} };
    }

    // Find differences
    const differences = this.findDifferences(normBaseline, normExported);

    console.warn(`✗ Schemas differ: ${schemaName}`);
    console.debug(`Differences:`, differences);

    return {
      match: false,
      differences: { items: differences, count: differences.length },
    };
  }

  /**
   * Compare two schema JSON files.
   */
  async compareFiles(
    baselinePath: string,
    exportedPath: string,
    schemaName?: string
  ): Promise<ComparisonResult> {
    const fs = await import('fs/promises');

    const baseline = JSON.parse(await fs.readFile(baselinePath, 'utf-8'));
    const exported = JSON.parse(await fs.readFile(exportedPath, 'utf-8'));

    return this.compareSchemas(baseline, exported, schemaName);
  }
}
