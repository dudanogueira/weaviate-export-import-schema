/**
 * Test runner for importing and exporting Weaviate schemas.
 */

import weaviate, { WeaviateClient } from 'weaviate-client';
import { promises as fs } from 'fs';
import path from 'path';

export interface TestResult {
  schema_name: string;
  success: boolean;
  error?: string;
  exported_path?: string;
}

export class TestRunner {
  private client: WeaviateClient | null = null;
  private weaviateUrl: string;

  constructor(weaviateUrl: string = 'http://localhost:8080') {
    this.weaviateUrl = weaviateUrl;
  }

  /**
   * Connect to Weaviate instance.
   */
  async connect(): Promise<void> {
    try {
      this.client = await weaviate.connectToLocal({
        host: 'localhost',
        port: 8080,
      });
      console.log(`Connected to Weaviate at ${this.weaviateUrl}`);
    } catch (error) {
      console.error(`Failed to connect to Weaviate:`, error);
      throw error;
    }
  }

  /**
   * Disconnect from Weaviate instance.
   */
  async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.close();
      console.log('Disconnected from Weaviate');
    }
  }

  /**
   * Load a schema from JSON file.
   */
  async loadSchema(schemaPath: string): Promise<any> {
    const content = await fs.readFile(schemaPath, 'utf-8');
    const schema = JSON.parse(content);
    console.log(`Loaded schema from: ${schemaPath}`);
    return schema;
  }

  /**
   * Import a schema into Weaviate by creating a collection.
   */
  async importSchema(schema: any): Promise<string> {
    if (!this.client) {
      throw new Error('Not connected to Weaviate. Call connect() first.');
    }

    // Support both 'name' (v4) and 'class' (v3/legacy) for backward compatibility
    const collectionName = schema.name || schema.class;
    if (!collectionName) {
      throw new Error('Schema missing "name" or "class" field');
    }

    // Delete if exists
    if (await this.client.collections.exists(collectionName)) {
      console.log(`Deleting existing collection: ${collectionName}`);
      await this.client.collections.delete(collectionName);
    }

    console.log(`Importing collection: ${collectionName}`);

    // Build properties
    const properties = schema.properties?.map((prop: any) => ({
      name: prop.name,
      dataType: prop.dataType,
      description: prop.description,
    })) || [];

    // Handle vector configuration
    let vectorConfig: any = undefined;

    if (schema.vectorConfig) {
      // Multi-named vectors or single named vector
      const vectors: any = {};

      for (const [vectorName, vectorDef] of Object.entries(schema.vectorConfig)) {
        const vDef = vectorDef as any;
        const distance = vDef.vectorIndexConfig?.distance || 'cosine';

        vectors[vectorName] = weaviate.configure.vectorIndex.hnsw({
          distanceMetric: distance,
        });
      }

      vectorConfig = vectors;
    }

    // Create collection
    try {
      const collectionConfig: any = {
        name: collectionName,
        description: schema.description,
        properties,
      };

      if (vectorConfig) {
        collectionConfig.vectorizers = weaviate.configure.vectorizer.none(vectorConfig);
      } else {
        collectionConfig.vectorizers = weaviate.configure.vectorizer.none();
      }

      // Add replication config
      if (schema.replicationConfig) {
        collectionConfig.replication = weaviate.configure.replication({
          factor: schema.replicationConfig.factor || 1,
        });
      }

      // Add inverted index config
      if (schema.invertedIndexConfig) {
        collectionConfig.invertedIndex = weaviate.configure.invertedIndex({
          indexNullState: schema.invertedIndexConfig.indexNullState ?? false,
          indexPropertyLength: schema.invertedIndexConfig.indexPropertyLength ?? false,
          indexTimestamps: schema.invertedIndexConfig.indexTimestamps ?? false,
        });
      }

      await this.client.collections.create(collectionConfig);

      console.log(`Successfully imported collection: ${collectionName}`);
      return collectionName;
    } catch (error) {
      console.error(`Failed to import collection:`, error);
      throw error;
    }
  }

  /**
   * Export a collection's schema configuration.
   */
  async exportSchema(collectionName: string): Promise<any> {
    if (!this.client) {
      throw new Error('Not connected to Weaviate. Call connect() first.');
    }

    try {
      const collection = this.client.collections.get(collectionName);
      const config = await collection.config.get();

      console.log(`Exported schema for collection: ${collectionName}`);
      return config;
    } catch (error) {
      console.error(`Failed to export schema:`, error);
      throw error;
    }
  }

  /**
   * Save schema to JSON file.
   */
  async saveSchema(schema: any, outputPath: string): Promise<void> {
    const dir = path.dirname(outputPath);
    await fs.mkdir(dir, { recursive: true });

    await fs.writeFile(outputPath, JSON.stringify(schema, null, 2));

    console.log(`Saved schema to: ${outputPath}`);
  }

  /**
   * Delete a collection from Weaviate.
   */
  async cleanup(collectionName: string): Promise<void> {
    if (!this.client) {
      return;
    }

    try {
      if (await this.client.collections.exists(collectionName)) {
        await this.client.collections.delete(collectionName);
        console.log(`Cleaned up collection: ${collectionName}`);
      }
    } catch (error) {
      console.warn(`Failed to cleanup collection:`, error);
    }
  }

  /**
   * Run a complete import/export test.
   */
  async runTest(
    baselinePath: string,
    outputDir: string,
    schemaName: string
  ): Promise<TestResult> {
    const result: TestResult = {
      schema_name: schemaName,
      success: false,
    };

    try {
      // Load baseline
      const baseline = await this.loadSchema(baselinePath);

      // Import schema
      const collectionName = await this.importSchema(baseline);

      // Export schema
      const exported = await this.exportSchema(collectionName);

      // Save exported schema
      const outputPath = path.join(
        outputDir,
        'typescript',
        schemaName,
        'config.json'
      );
      await this.saveSchema(exported, outputPath);

      result.success = true;
      result.exported_path = outputPath;

      // Cleanup
      await this.cleanup(collectionName);
    } catch (error) {
      result.error = error instanceof Error ? error.message : String(error);
      console.error(`Test failed for ${schemaName}:`, error);
    }

    return result;
  }
}
