/**
 * Vitest tests for schema import/export validation.
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { TestRunner } from '../src/testRunner';
import { SchemaComparator } from '../src/comparator';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get current directory in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Get project root
const PROJECT_ROOT = path.resolve(__dirname, '../../..');
const SCHEMAS_DIR = path.join(PROJECT_ROOT, 'schemas');
const RESULTS_DIR = path.join(PROJECT_ROOT, 'test-results');

// P0 schema names
const P0_SCHEMAS = [
  'P0-basic-text-only',
  'P0-single-named-vector',
  'P0-multi-named-vectors',
];

// Test runner instance
let testRunner: TestRunner;

beforeAll(async () => {
  testRunner = new TestRunner();
  await testRunner.connect();
});

afterAll(async () => {
  await testRunner.disconnect();
});

describe('Schema Import/Export Tests', () => {
  P0_SCHEMAS.forEach((schemaName) => {
    it(`should import and re-export ${schemaName} identically`, async () => {
      // Paths
      const baselinePath = path.join(SCHEMAS_DIR, schemaName, 'config.json');
      const outputDir = path.join(RESULTS_DIR, 'exported-schemas');

      // Run test
      const result = await testRunner.runTest(
        baselinePath,
        outputDir,
        schemaName
      );

      // Verify test succeeded
      expect(result.success).toBe(true);
      expect(result.error).toBeUndefined();
      expect(result.exported_path).toBeDefined();

      // Compare schemas
      const comparator = new SchemaComparator();
      const comparison = await comparator.compareFiles(
        baselinePath,
        result.exported_path!,
        schemaName
      );

      // Assert schemas match
      expect(comparison.match).toBe(true);
      if (!comparison.match) {
        console.error(
          `Schema mismatch for ${schemaName}:`,
          JSON.stringify(comparison.differences, null, 2)
        );
      }
    }, 30000); // 30 second timeout per test
  });

  it('should have all P0 baseline schemas', async () => {
    const fs = await import('fs/promises');
    const missing: string[] = [];

    for (const schemaName of P0_SCHEMAS) {
      const schemaPath = path.join(SCHEMAS_DIR, schemaName, 'config.json');
      try {
        await fs.access(schemaPath);
      } catch {
        missing.push(schemaName);
      }
    }

    expect(missing).toEqual([]);
  });
});
