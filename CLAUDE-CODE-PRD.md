# Claude Code PRD: PipelineGPT — Data App Factory

## INSTRUCTIONS FOR CLAUDE CODE

You are building a full-stack web application for HackUSU 2026's "Data App Factory" track (sponsored by Koch Industries, Databricks, and AWS). This is a 19-hour build window. This document is your complete specification. Build the entire application step by step. Commit after each major milestone. Do not skip steps.

The project has already been scaffolded with Next.js 14, TypeScript, and Tailwind. Dependencies are installed. Sample data files exist in `src/data/`. You are writing ALL application code from scratch.

---

## PROJECT OVERVIEW

**Track requirement:** Build a "Data App Factory" — a governed framework that empowers non-technical business users (citizen developers) to create their own data applications, while IT/admins maintain governance guardrails. Think of it as a platform that PRODUCES data apps, not just a single app.

**What we're building:** PipelineGPT — a governed, AI-powered platform where business users describe data workflows through a conversational chat interface, and the system generates visual pipeline diagrams, production-ready PySpark code for Databricks notebooks, plain-English explanations, and governance compliance checks. IT admins configure templates, data access policies, and guardrails. Business users build pipelines within those guardrails.

**Core loop:** Conversational chat → Structured pipeline JSON → Visual DAG diagram + Generated PySpark/Databricks code + Explanations + Governance checks → Deploy to Databricks

**Key differentiators (what judges care about):**
1. **Governance is baked in** — not bolted on. Every pipeline gets access control checks, PII detection, data quality rules, and audit logging.
2. **Factory model** — reusable templates that IT admins configure, business users customize via natural language.
3. **Conversational AI** — not a static form. The chat refines and clarifies, asks follow-up questions, suggests improvements.
4. **Deep Databricks/AWS integration** — Unity Catalog, Delta Lake, S3, DBFS, Jobs API, IAM roles throughout.

**Tech stack (already installed):**
- Framework: Next.js 14 (App Router, TypeScript)
- Styling: Tailwind CSS
- AI: OpenAI GPT-4o with function calling
- Pipeline visualization: React Flow
- Code display: Monaco Editor
- Streaming: Vercel AI SDK
- Deployment: Vercel

---

## STEP 1: SHARED TYPES

Create `src/types/index.ts`:

```typescript
// ── Pipeline Definition Types ──────────────────────────

export type StepType = "source" | "transform" | "destination";

export type SourceOperation =
  | "read_csv"
  | "read_json"
  | "read_parquet"
  | "read_delta"
  | "read_database_table"
  | "read_unity_catalog"
  | "read_redshift"
  | "read_glue_catalog";

export type TransformOperation =
  | "filter"
  | "join"
  | "aggregate"
  | "sort"
  | "rename_columns"
  | "cast_types"
  | "clean_dates"
  | "deduplicate"
  | "fill_nulls"
  | "add_column"
  | "pivot"
  | "window_function"
  | "categorize";

export type DestinationOperation =
  | "write_csv"
  | "write_parquet"
  | "write_delta"
  | "write_database_table"
  | "write_unity_catalog"
  | "write_redshift"
  | "write_s3"
  | "email_report"
  | "display_output";

export type PipelineOperation = SourceOperation | TransformOperation | DestinationOperation;

export interface PipelineStepConfig {
  // Source configs
  bucket?: string;
  path?: string;
  format?: string;
  tableName?: string;
  hasHeader?: boolean;
  inferSchema?: boolean;

  // Transform configs
  column?: string;
  columns?: string[];
  condition?: string;
  joinKey?: string;
  joinType?: "inner" | "left" | "right" | "outer";
  rightSource?: string;
  rightSourceStepId?: string;
  groupBy?: string[];
  aggregations?: { column: string; function: string; alias: string }[];
  sortBy?: string[];
  sortOrder?: "asc" | "desc";
  newColumnName?: string;
  newColumnExpression?: string;
  dateColumn?: string;
  inputFormat?: string;
  outputFormat?: string;
  categories?: { name: string; condition: string }[];

  // Databricks / AWS configs
  catalog?: string;         // Unity Catalog catalog name
  schema?: string;          // Unity Catalog schema name
  deltaPath?: string;       // DBFS or S3 path for Delta tables
  s3Bucket?: string;        // AWS S3 bucket
  s3Prefix?: string;        // AWS S3 key prefix
  redshiftTable?: string;   // Redshift table name
  redshiftSchema?: string;  // Redshift schema
  glueDatabase?: string;    // AWS Glue Data Catalog database
  glueTable?: string;       // AWS Glue Data Catalog table
  partitionBy?: string[];   // Delta/Parquet partition columns
  mergeCondition?: string;  // Delta MERGE condition for upserts
  zOrderBy?: string[];      // Delta Z-ORDER optimization columns

  // Destination configs
  outputPath?: string;
  outputTable?: string;
  recipient?: string;
  mode?: "overwrite" | "append" | "merge";
}

export interface PipelineStep {
  id: string;
  type: StepType;
  operation: PipelineOperation;
  label: string; // Human-readable label for the visual node (e.g., "Read Sales CSV")
  config: PipelineStepConfig;
  dependsOn: string[]; // IDs of upstream steps
}

export interface PipelineSchedule {
  frequency: "once" | "hourly" | "daily" | "weekly" | "monthly";
  dayOfWeek?: string;
  time?: string;
  cronExpression?: string;
}

export interface PipelineDefinition {
  pipelineName: string;
  description: string;
  schedule: PipelineSchedule | null;
  steps: PipelineStep[];
}

// ── Validation & Explanation Types ─────────────────────

export interface StepExplanation {
  stepId: string;
  plainEnglish: string;
}

export interface StepWarning {
  stepId: string;
  message: string;
  severity: "low" | "medium" | "high";
}

export interface ValidationResult {
  status: "pass" | "warning" | "error";
  explanations: StepExplanation[];
  warnings: StepWarning[];
}

// ── Governance Types ──────────────────────────────────

export type UserRole = "admin" | "analyst" | "viewer";

export interface GovernancePolicy {
  allowedSources: string[];         // e.g., ["read_csv", "read_delta", "read_unity_catalog"]
  blockedSources: string[];         // sources this role cannot use
  allowedDestinations: string[];
  maxSteps: number;                 // max pipeline complexity for this role
  requireApproval: boolean;         // must an admin approve before deploy?
  piiColumns: string[];             // columns flagged as PII (auto-detected)
  dataMaskingEnabled: boolean;
  allowedCatalogs: string[];        // Unity Catalog catalogs this user can access
  allowedSchemas: string[];         // Unity Catalog schemas this user can access
}

export interface GovernanceCheck {
  rule: string;                     // e.g., "PII Detection", "Access Control", "Data Quality"
  status: "pass" | "warning" | "fail";
  message: string;
  details?: string;
}

export interface AuditLogEntry {
  timestamp: string;
  user: string;
  action: string;                   // e.g., "pipeline_created", "pipeline_deployed", "template_used"
  pipelineName: string;
  details: string;
}

export interface PipelineTemplate {
  id: string;
  name: string;                     // e.g., "Sales ETL", "Customer 360", "Data Quality Audit"
  description: string;
  category: "etl" | "analytics" | "quality" | "reporting";
  icon: string;
  defaultPrompt: string;            // pre-filled NL prompt
  requiredSources: string[];
  governanceLevel: "low" | "medium" | "high";
  steps: number;                    // expected number of steps
}

// ── Chat Types ────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  pipeline?: PipelineDefinition;    // attached when assistant generates a pipeline
  isRefining?: boolean;             // true when this is a follow-up refinement
}

// ── UI State Types ─────────────────────────────────────

export interface AppState {
  // Chat state
  chatMessages: ChatMessage[];
  userInput: string;
  // Pipeline state
  pipeline: PipelineDefinition | null;
  generatedCode: string | null;
  validation: ValidationResult | null;
  governanceChecks: GovernanceCheck[];
  // Loading states
  isParsingIntent: boolean;
  isGeneratingCode: boolean;
  isValidating: boolean;
  isCheckingGovernance: boolean;
  // UI state
  error: string | null;
  selectedStepId: string | null;
  currentRole: UserRole;           // admin or analyst view toggle
  showTemplates: boolean;
  activeTemplate: PipelineTemplate | null;
}

// ── React Flow Node Types ──────────────────────────────

export interface PipelineNodeData {
  label: string;
  stepType: StepType;
  operation: PipelineOperation;
  explanation?: string;
  warning?: StepWarning;
  isSelected?: boolean;
}

// ── Example Prompt Type ────────────────────────────────

export interface ExamplePrompt {
  id: string;
  label: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  stepsPreview: string[];
}
```

**Commit: "feat: add shared TypeScript type definitions"**

---

## STEP 2: OPENAI CLIENT, PROMPTS, AND FUNCTION SCHEMAS

### 2a. Create `src/lib/openai.ts`

```typescript
import OpenAI from "openai";

export const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});
```

### 2b. Create `src/lib/prompts.ts`

```typescript
export const INTENT_PARSE_PROMPT = `You are a data pipeline architect. Your job is to convert a natural language description of a data workflow into a structured pipeline definition.

The user is a non-technical business person. They will describe what they want in plain English. You must:

1. Identify all data sources mentioned (CSV files, database tables, S3 paths)
2. Identify all transformation steps (cleaning, joining, filtering, aggregating, sorting, etc.)
3. Identify the output destination (file, table, report, display)
4. Determine the correct order of operations and dependencies
5. Infer reasonable defaults for anything not specified

Rules:
- Every pipeline must start with at least one source step
- Every pipeline must end with at least one destination step
- Each step must have a unique ID (step_1, step_2, etc.)
- Dependencies must form a valid DAG (directed acyclic graph — no circular dependencies)
- If the user mentions two data sources that need to be combined, create separate source steps and a join step
- If the user mentions scheduling (e.g., "every Monday"), include a schedule
- If no schedule is mentioned, set schedule to null
- Labels should be short and descriptive (e.g., "Read Sales CSV", "Filter High-Value", "Join with Customers")
- For date cleaning, infer the likely input format from context (e.g., US dates are typically MM/DD/YYYY)
- For aggregations, infer the appropriate function (sum for revenue, count for orders, avg for ratings, etc.)

Databricks & AWS context:
- When the user mentions "table" or "catalog", prefer Unity Catalog sources (read_unity_catalog) with catalog.schema.table format
- When the user mentions S3, use read_csv/read_parquet/read_delta with an s3:// path in the config
- When the user mentions "data lake" or "lakehouse", default to Delta format
- For destinations, prefer Delta Lake writes (write_delta) over CSV/Parquet when the user wants persistent, queryable output
- If the user mentions "Redshift" or "data warehouse", use read_redshift/write_redshift
- If the user mentions "Glue" or "data catalog", use read_glue_catalog
- When writing Delta, suggest partitionBy for large datasets and zOrderBy for frequently filtered columns
- For upserts/updates, use mode "merge" with a mergeCondition

Available data sources for demos (user may reference these):
- sample-sales.csv: Columns: order_id, order_date, customer_id, product, quantity, unit_price, total, region, sales_rep
- sample-customers.csv: Columns: customer_id, company_name, industry, account_value, city, state, signup_date, is_enterprise
- sample-employees.csv: Columns: employee_id, name, department, title, hire_date, salary, manager_id, location
- Unity Catalog examples: main.default.sales_transactions, main.default.customer_dim, main.analytics.revenue_summary
- S3 examples: s3://company-data-lake/raw/sales/, s3://company-data-lake/curated/customers/`;

export const CODE_GENERATION_PROMPT = `You are a PySpark code generation engine optimized for Databricks notebooks running on AWS.

Given a structured pipeline definition in JSON, generate a complete, executable PySpark script that would run in a Databricks notebook environment on AWS infrastructure.

Rules:
- Use PySpark DataFrame API (never RDD API)
- Import all necessary modules at the top, including: pyspark.sql.functions as F, pyspark.sql.types, delta.tables (when using Delta)
- Add a clear header comment block with pipeline name, description, and generation timestamp
- Add "# Databricks notebook source" as the very first line (Databricks convention)
- Add a section comment before each step (e.g., "# ── Step 1: Read Sales CSV ──────")
- Use descriptive variable names based on what the DataFrame contains (e.g., df_sales, df_customers, df_high_value)

Databricks-specific patterns:
- Use spark.read for all file sources (Databricks runtime provides the SparkSession)
- For CSV sources: spark.read.option("header", "true").option("inferSchema", "true").csv(path)
- For Delta sources: spark.read.format("delta").load(path) or spark.table("catalog.schema.table")
- For Unity Catalog tables: use three-level namespace (catalog.schema.table)
- For S3 paths: use s3:// or s3a:// paths directly (Databricks handles AWS auth via instance profiles)
- For Delta writes: df.write.format("delta").mode("overwrite").save(path) — always prefer Delta over Parquet
- For Delta MERGE/upserts: use DeltaTable.forPath(spark, path).alias("target").merge(source.alias("source"), condition)
- For partitioned writes: .partitionBy("column") before .save()
- For Z-ORDER optimization: add a comment "# OPTIMIZE delta.\`path\` ZORDER BY (col)" after Delta writes
- Use display() for Databricks notebook output (not .show())
- Use dbutils.widgets for parameterized notebooks (add a comment showing how)
- Use dbutils.fs.ls() references when listing directories
- End with display() for interactive output, or a write operation if saving to Delta/S3

AWS-specific patterns:
- S3 paths: s3://bucket-name/prefix/path/
- For Redshift: spark.read.format("redshift").option("url", jdbc_url).option("dbtable", table).load()
- For Glue Catalog: spark.read.table("glue_database.table_name") via Glue Data Catalog integration
- Assume IAM roles / instance profiles handle all AWS authentication (never hardcode credentials)

General code quality:
- Use col() or F.col() for all column references in expressions
- For date operations, use to_date() or date_format() with explicit format strings
- For aggregations, import and use pyspark.sql.functions (sum as _sum, count, avg, min, max, etc.)
- For joins, always specify the join type explicitly
- For filters with string conditions that reference columns, use F.expr() for complex expressions or F.col() for simple comparisons
- For local/demo CSV files, use DBFS paths: /dbfs/FileStore/data/ or dbfs:/FileStore/data/
- Add empty lines between steps for readability
- NEVER include markdown formatting or code fences — output ONLY raw Python code

Output ONLY the Python code. No explanations, no markdown.`;

export const VALIDATION_PROMPT = `You are a data pipeline quality reviewer. Given a pipeline definition and the generated PySpark code, you must:

1. Review each step and provide a clear, plain-English explanation that a non-technical business user would understand.
2. Identify any potential issues, edge cases, or warnings.

For explanations:
- Use simple language (no technical jargon like "DataFrame" or "schema inference")
- Describe what happens to the data at each step from the user's perspective
- Mention specific column names and values when relevant
- Be concise — 1-2 sentences per step

For warnings, flag:
- CSV files without explicit schemas (data type issues)
- Inner joins that might drop records
- Filters that might return empty results
- Date format assumptions that might be wrong
- Missing null handling
- Large aggregations that might be slow
- Any step where the user's intent might be ambiguous

Severity levels:
- "low": Nice to know, not a problem for most cases
- "medium": Could cause unexpected results in some cases
- "high": Likely to cause errors or data loss

Return a JSON object with "explanations" and "warnings" arrays.`;
```

### 2c. Create `src/lib/functions.ts`

Define the complete OpenAI function calling schema for intent parsing:

```typescript
import { PipelineDefinition } from "@/types";

export const parsePipelineFunction = {
  name: "create_pipeline_definition",
  description: "Convert a natural language data pipeline description into a structured pipeline definition with sources, transforms, and destinations.",
  parameters: {
    type: "object" as const,
    properties: {
      pipelineName: {
        type: "string",
        description: "Short, descriptive snake_case name for the pipeline (e.g., weekly_sales_report)",
      },
      description: {
        type: "string",
        description: "One-sentence description of what this pipeline does",
      },
      schedule: {
        type: "object",
        description: "Execution schedule, or null if one-time",
        properties: {
          frequency: {
            type: "string",
            enum: ["once", "hourly", "daily", "weekly", "monthly"],
          },
          dayOfWeek: {
            type: "string",
            description: "Day of week if weekly (e.g., 'monday')",
          },
          time: {
            type: "string",
            description: "Time in HH:MM 24-hour format",
          },
          cronExpression: {
            type: "string",
            description: "Equivalent cron expression",
          },
        },
        required: ["frequency"],
      },
      steps: {
        type: "array",
        description: "Ordered list of pipeline steps forming a DAG",
        items: {
          type: "object",
          properties: {
            id: {
              type: "string",
              description: "Unique step ID (step_1, step_2, ...)",
            },
            type: {
              type: "string",
              enum: ["source", "transform", "destination"],
            },
            operation: {
              type: "string",
              enum: [
                "read_csv",
                "read_json",
                "read_parquet",
                "read_delta",
                "read_database_table",
                "read_unity_catalog",
                "read_redshift",
                "read_glue_catalog",
                "filter",
                "join",
                "aggregate",
                "sort",
                "rename_columns",
                "cast_types",
                "clean_dates",
                "deduplicate",
                "fill_nulls",
                "add_column",
                "pivot",
                "window_function",
                "categorize",
                "write_csv",
                "write_parquet",
                "write_delta",
                "write_database_table",
                "write_unity_catalog",
                "write_redshift",
                "write_s3",
                "email_report",
                "display_output",
              ],
            },
            label: {
              type: "string",
              description: "Short human-readable label for the visual node (e.g., 'Read Sales CSV', 'Filter > $50K')",
            },
            config: {
              type: "object",
              description: "Operation-specific configuration",
              properties: {
                bucket: { type: "string", description: "S3 bucket name" },
                path: { type: "string", description: "File or directory path" },
                format: { type: "string", description: "File format (csv, json, parquet)" },
                tableName: { type: "string", description: "Database table name" },
                hasHeader: { type: "boolean", description: "Whether CSV has a header row" },
                inferSchema: { type: "boolean", description: "Whether to auto-detect column types" },
                column: { type: "string", description: "Target column name" },
                columns: { type: "array", items: { type: "string" }, description: "List of column names" },
                condition: { type: "string", description: "Filter condition as a SQL expression" },
                joinKey: { type: "string", description: "Column to join on" },
                joinType: { type: "string", enum: ["inner", "left", "right", "outer"] },
                rightSource: { type: "string", description: "Description of the right side data source" },
                rightSourceStepId: { type: "string", description: "Step ID of the right side source" },
                groupBy: { type: "array", items: { type: "string" }, description: "Columns to group by" },
                aggregations: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      column: { type: "string" },
                      function: { type: "string", description: "Aggregation function: sum, count, avg, min, max" },
                      alias: { type: "string", description: "Output column name" },
                    },
                    required: ["column", "function", "alias"],
                  },
                },
                sortBy: { type: "array", items: { type: "string" } },
                sortOrder: { type: "string", enum: ["asc", "desc"] },
                newColumnName: { type: "string" },
                newColumnExpression: { type: "string" },
                dateColumn: { type: "string" },
                inputFormat: { type: "string", description: "Input date format (e.g., MM/dd/yyyy)" },
                outputFormat: { type: "string", description: "Output date format (e.g., yyyy-MM-dd)" },
                categories: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      name: { type: "string" },
                      condition: { type: "string" },
                    },
                    required: ["name", "condition"],
                  },
                },
                catalog: { type: "string", description: "Unity Catalog catalog name (e.g., 'main')" },
                schema: { type: "string", description: "Unity Catalog schema name (e.g., 'default')" },
                deltaPath: { type: "string", description: "DBFS or S3 path for Delta Lake table" },
                s3Bucket: { type: "string", description: "AWS S3 bucket name" },
                s3Prefix: { type: "string", description: "AWS S3 key prefix/path" },
                redshiftTable: { type: "string", description: "Redshift table name" },
                redshiftSchema: { type: "string", description: "Redshift schema name" },
                glueDatabase: { type: "string", description: "AWS Glue Data Catalog database" },
                glueTable: { type: "string", description: "AWS Glue Data Catalog table" },
                partitionBy: { type: "array", items: { type: "string" }, description: "Columns to partition Delta/Parquet writes by" },
                mergeCondition: { type: "string", description: "SQL condition for Delta MERGE upserts (e.g., 'target.id = source.id')" },
                zOrderBy: { type: "array", items: { type: "string" }, description: "Columns to Z-ORDER Delta table by for query optimization" },
                outputPath: { type: "string" },
                outputTable: { type: "string" },
                recipient: { type: "string" },
                mode: { type: "string", enum: ["overwrite", "append", "merge"] },
              },
            },
            dependsOn: {
              type: "array",
              items: { type: "string" },
              description: "IDs of steps this step depends on (upstream steps)",
            },
          },
          required: ["id", "type", "operation", "label", "config", "dependsOn"],
        },
      },
    },
    required: ["pipelineName", "description", "steps"],
  },
};

export const validatePipelineFunction = {
  name: "validate_pipeline",
  description: "Review a pipeline definition and generated code, providing plain-English explanations and warnings.",
  parameters: {
    type: "object" as const,
    properties: {
      explanations: {
        type: "array",
        items: {
          type: "object",
          properties: {
            stepId: { type: "string" },
            plainEnglish: { type: "string", description: "1-2 sentence explanation for a non-technical user" },
          },
          required: ["stepId", "plainEnglish"],
        },
      },
      warnings: {
        type: "array",
        items: {
          type: "object",
          properties: {
            stepId: { type: "string" },
            message: { type: "string" },
            severity: { type: "string", enum: ["low", "medium", "high"] },
          },
          required: ["stepId", "message", "severity"],
        },
      },
    },
    required: ["explanations", "warnings"],
  },
};
```

### 2d. Create `src/lib/pipeline-to-nodes.ts`

A utility that converts a `PipelineDefinition` into React Flow nodes and edges:

```typescript
import { Node, Edge } from "reactflow";
import { PipelineDefinition, PipelineNodeData, StepType } from "@/types";

// Color mapping by step type
const STEP_COLORS: Record<StepType, { bg: string; border: string; text: string }> = {
  source: { bg: "bg-blue-50", border: "border-blue-400", text: "text-blue-700" },
  transform: { bg: "bg-amber-50", border: "border-amber-400", text: "text-amber-700" },
  destination: { bg: "bg-green-50", border: "border-green-400", text: "text-green-700" },
};

// Icon mapping by step type
const STEP_ICONS: Record<StepType, string> = {
  source: "📥",
  transform: "⚙️",
  destination: "📤",
};

export function pipelineToNodesAndEdges(pipeline: PipelineDefinition): {
  nodes: Node<PipelineNodeData>[];
  edges: Edge[];
} {
  // Calculate layout positions
  // Arrange nodes in a left-to-right flow, with vertical stacking for parallel steps
  // Steps with no dependencies go on the left
  // Each subsequent dependency layer moves right

  const nodes: Node<PipelineNodeData>[] = [];
  const edges: Edge[] = [];

  // Calculate depth of each step (longest path from a root)
  const depthMap = new Map<string, number>();

  function getDepth(stepId: string): number {
    if (depthMap.has(stepId)) return depthMap.get(stepId)!;
    const step = pipeline.steps.find((s) => s.id === stepId);
    if (!step || step.dependsOn.length === 0) {
      depthMap.set(stepId, 0);
      return 0;
    }
    const maxParentDepth = Math.max(...step.dependsOn.map(getDepth));
    const depth = maxParentDepth + 1;
    depthMap.set(stepId, depth);
    return depth;
  }

  pipeline.steps.forEach((step) => getDepth(step.id));

  // Group steps by depth for vertical positioning
  const depthGroups = new Map<number, string[]>();
  pipeline.steps.forEach((step) => {
    const depth = depthMap.get(step.id) || 0;
    if (!depthGroups.has(depth)) depthGroups.set(depth, []);
    depthGroups.get(depth)!.push(step.id);
  });

  // Position constants
  const X_SPACING = 280;
  const Y_SPACING = 120;
  const Y_START = 50;
  const X_START = 50;

  // Create nodes
  pipeline.steps.forEach((step) => {
    const depth = depthMap.get(step.id) || 0;
    const stepsAtDepth = depthGroups.get(depth) || [];
    const indexAtDepth = stepsAtDepth.indexOf(step.id);
    const totalAtDepth = stepsAtDepth.length;

    // Center vertically if multiple nodes at same depth
    const yOffset = totalAtDepth > 1 ? (indexAtDepth - (totalAtDepth - 1) / 2) * Y_SPACING : 0;

    nodes.push({
      id: step.id,
      type: "pipelineNode",
      position: {
        x: X_START + depth * X_SPACING,
        y: Y_START + 200 + yOffset,
      },
      data: {
        label: step.label,
        stepType: step.type,
        operation: step.operation,
      },
    });

    // Create edges from dependencies
    step.dependsOn.forEach((depId) => {
      edges.push({
        id: `${depId}-${step.id}`,
        source: depId,
        target: step.id,
        animated: true,
        style: { stroke: "#94a3b8", strokeWidth: 2 },
      });
    });
  });

  return { nodes, edges };
}
```

**Commit: "feat: add OpenAI client, prompts, function schemas, and pipeline-to-nodes utility"**

---

## STEP 3: API ROUTES

### 3a. Create `src/app/api/parse-intent/route.ts`

This route handles Stage 1 — Intent Parsing:
1. Accepts POST with `{ input: string }` (the user's natural language description)
2. Calls OpenAI GPT-4o with:
   - System message: `INTENT_PARSE_PROMPT`
   - User message: the input string
   - Tools: `[{ type: "function", function: parsePipelineFunction }]`
   - Tool choice: `{ type: "function", function: { name: "create_pipeline_definition" } }`
3. Parses the function call result from `response.choices[0].message.tool_calls[0].function.arguments`
4. Validates that the result has at least one source and one destination step
5. Returns the `PipelineDefinition` as JSON
6. On error, returns 500 with `{ error: "message" }`

### 3b. Create `src/app/api/generate-code/route.ts`

This route handles Stage 2 — Code Generation:
1. Accepts POST with `{ pipeline: PipelineDefinition }`
2. Calls OpenAI GPT-4o with:
   - System message: `CODE_GENERATION_PROMPT`
   - User message: the pipeline definition as formatted JSON
   - NO function calling — this is a standard completion that returns raw PySpark code
   - Set `temperature: 0.2` for consistent code generation
3. Extracts the text content from `response.choices[0].message.content`
4. Strips any markdown code fences if the model accidentally includes them (regex replace `` ```python\n `` and `` ``` ``)
5. Returns `{ code: string }`
6. On error, returns 500 with `{ error: "message" }`

### 3c. Create `src/app/api/validate/route.ts`

This route handles Stage 3 — Validation & Explanation:
1. Accepts POST with `{ pipeline: PipelineDefinition, code: string }`
2. Calls OpenAI GPT-4o with:
   - System message: `VALIDATION_PROMPT`
   - User message: both the pipeline JSON and the generated code
   - Tools: `[{ type: "function", function: validatePipelineFunction }]`
   - Tool choice: `{ type: "function", function: { name: "validate_pipeline" } }`
3. Parses the function call result
4. Returns the `ValidationResult` as JSON
5. On error, returns 500 with `{ error: "message" }`

### 3d. Create `src/app/api/governance-check/route.ts`

This route handles Stage 4 — Governance & Compliance:
1. Accepts POST with `{ pipeline: PipelineDefinition, role: UserRole }`
2. Runs a series of deterministic governance checks (NOT an AI call — this is fast, rule-based logic):
   - **PII Detection**: Scan all column names in pipeline configs for common PII patterns (email, phone, ssn, name, address, dob, salary). Flag any matches as warnings.
   - **Access Control**: Check the user's role against a hardcoded governance policy. Analysts cannot use `write_redshift` or `write_unity_catalog` to production catalogs. Viewers cannot deploy at all.
   - **Data Quality**: Warn if any CSV source doesn't have schema inference enabled. Warn if joins don't specify a join type. Warn if there's no deduplication step after a join.
   - **Complexity Check**: If pipeline has >10 steps, flag as "high complexity — requires admin approval."
   - **Catalog Access**: Check if the Unity Catalog catalogs/schemas referenced are in the user's `allowedCatalogs` / `allowedSchemas` list.
   - **Data Masking**: If PII columns are detected and `dataMaskingEnabled` is true for the role, add a governance check noting which columns will be masked.
3. Returns `{ checks: GovernanceCheck[], requiresApproval: boolean }`
4. This should be FAST (no AI call) — return results in <100ms

### 3e. Create `src/app/api/refine-pipeline/route.ts`

This route handles conversational follow-up refinements:
1. Accepts POST with `{ existingPipeline: PipelineDefinition, refinement: string }`
2. Calls OpenAI GPT-4o with:
   - System message: `INTENT_PARSE_PROMPT` + an additional instruction: "You are refining an EXISTING pipeline. The user wants to modify it. Here is the current pipeline definition: [JSON]. Apply the user's requested changes while preserving the rest of the pipeline structure. Return the complete updated pipeline."
   - User message: the refinement request string
   - Tools: same `parsePipelineFunction`
   - Tool choice: same forced function call
3. Returns the updated `PipelineDefinition`
4. The frontend will re-trigger code generation and validation with the new pipeline

### 3f. Create `src/lib/governance-rules.ts`

Hardcoded governance policies and PII detection logic:

```typescript
import { GovernancePolicy, GovernanceCheck, PipelineDefinition, UserRole } from "@/types";

// Default governance policies by role
export const GOVERNANCE_POLICIES: Record<UserRole, GovernancePolicy> = {
  admin: {
    allowedSources: ["*"],
    blockedSources: [],
    allowedDestinations: ["*"],
    maxSteps: 50,
    requireApproval: false,
    piiColumns: [],
    dataMaskingEnabled: false,
    allowedCatalogs: ["*"],
    allowedSchemas: ["*"],
  },
  analyst: {
    allowedSources: ["read_csv", "read_delta", "read_unity_catalog", "read_parquet", "read_json", "read_glue_catalog"],
    blockedSources: ["read_redshift"],
    allowedDestinations: ["write_delta", "write_csv", "write_parquet", "write_s3", "display_output"],
    maxSteps: 15,
    requireApproval: true,
    piiColumns: [],
    dataMaskingEnabled: true,
    allowedCatalogs: ["main", "analytics"],
    allowedSchemas: ["default", "reporting", "staging"],
  },
  viewer: {
    allowedSources: ["read_unity_catalog", "read_delta"],
    blockedSources: ["read_csv", "read_redshift", "read_glue_catalog"],
    allowedDestinations: ["display_output"],
    maxSteps: 5,
    requireApproval: true,
    piiColumns: [],
    dataMaskingEnabled: true,
    allowedCatalogs: ["main"],
    allowedSchemas: ["reporting"],
  },
};

// PII column name patterns
const PII_PATTERNS = [
  /email/i, /phone/i, /ssn/i, /social.?security/i, /birth.?date/i, /dob/i,
  /salary/i, /address/i, /zip.?code/i, /credit.?card/i, /passport/i,
  /driver.?license/i, /first.?name/i, /last.?name/i, /full.?name/i,
];

export function runGovernanceChecks(pipeline: PipelineDefinition, role: UserRole): GovernanceCheck[] {
  const checks: GovernanceCheck[] = [];
  const policy = GOVERNANCE_POLICIES[role];

  // 1. PII Detection — scan all column references in configs
  // 2. Access Control — check operations against role's allowed/blocked lists
  // 3. Catalog Access — check Unity Catalog references against allowed catalogs/schemas
  // 4. Complexity — check step count against maxSteps
  // 5. Data Quality — check for missing schema inference, untyped joins, etc.
  // 6. Data Masking — flag columns that will be auto-masked

  // Implementation: iterate over pipeline.steps, check each step's operation
  // and config against the policy, and push GovernanceCheck objects to the array.
  // Return the array.

  return checks;
}
```

**Commit: "feat: add API routes for intent parsing, code generation, validation, governance, and refinement"**

---

## STEP 4: FRONTEND COMPONENTS

### Design System

Color palette and Tailwind conventions for all components:
- Background: `bg-slate-950` (dark mode — this makes the pipeline diagram and code pop visually)
- Surface/cards: `bg-slate-900 border border-slate-800`
- Input fields: `bg-slate-800 border-slate-700 text-white placeholder-slate-500`
- Primary accent: `indigo-500` / `indigo-600` for buttons and highlights
- Source nodes: `bg-blue-500/10 border-blue-500 text-blue-400`
- Transform nodes: `bg-amber-500/10 border-amber-500 text-amber-400`
- Destination nodes: `bg-green-500/10 border-green-500 text-green-400`
- Warning badges: yellow for low, orange for medium, red for high
- Text: `text-white` for headings, `text-slate-400` for secondary
- Rounded corners: `rounded-xl` for cards/panels, `rounded-lg` for buttons and inputs
- Subtle glow effects on the active/selected nodes: `ring-2 ring-indigo-500/50`

The overall look should feel like a premium developer tool — think Linear, Vercel Dashboard, or Raycast. Dark, clean, information-dense.

### 4a. Create `src/components/PipelineNode.tsx`

A custom React Flow node component:
- Renders as a rounded card with colored left border based on step type (blue for source, amber for transform, green for destination)
- Shows an icon (📥 source, ⚙️ transform, 📤 destination) and the step label
- Shows the operation name in smaller text below the label
- When selected, adds a glow ring (`ring-2 ring-indigo-500/50`)
- When there's a warning, shows a small warning dot (yellow/orange/red) in the top-right corner
- Handles: one input handle on the left (except for source nodes), one output handle on the right (except for destination nodes)
- On click, it should be selectable (pass selection handler via node data)

Register this as a custom node type for React Flow.

### 4b. Create `src/components/PipelineDiagram.tsx`

The visual pipeline diagram panel:
- Uses React Flow to render the pipeline as a node graph
- Props: `pipeline: PipelineDefinition | null`, `validation: ValidationResult | null`, `selectedStepId: string | null`, `onSelectStep: (stepId: string | null) => void`
- When pipeline is null, show an empty state with a subtle "Your pipeline will appear here" message
- When pipeline exists, convert it to nodes/edges using `pipelineToNodesAndEdges` and render
- Pass validation data (explanations, warnings) into the node data so PipelineNode can display warning indicators
- Use `@reactflow/controls` for zoom controls
- Use `@reactflow/background` with a subtle dot grid
- Background should be `bg-slate-900`
- Disable node dragging (the auto-layout positions are fine)
- On node click, call `onSelectStep` with the step ID
- On background click, call `onSelectStep(null)` to deselect

### 4c. Create `src/components/ChatInterface.tsx`

A conversational chat interface (NOT a static textarea form). This is critical — the Databricks spec explicitly warns against "weak conversational interfaces." This must feel like talking to an AI assistant.

- Props: `messages: ChatMessage[]`, `onSendMessage: (message: string) => void`, `isProcessing: boolean`, `templates: PipelineTemplate[]`, `onSelectTemplate: (template: PipelineTemplate) => void`
- Layout: a scrollable chat window with messages, plus an input bar at the bottom
- **Chat message rendering:**
  - User messages: right-aligned, indigo bubble, white text
  - Assistant messages: left-aligned, slate-800 bubble, white text with a small "◆ PipelineGPT" label
  - When an assistant message contains a pipeline (message.pipeline is set), show a compact inline preview: pipeline name, step count, and a "View Pipeline →" link that scrolls to the diagram
  - Assistant messages support markdown rendering (bold, lists, code snippets) for rich responses
- **Input bar:**
  - Single-line text input (expands to multi-line on focus/long input) with placeholder: "Describe what you want to do with your data..."
  - Send button (indigo arrow icon) — disabled while processing
  - Keyboard: Enter to send, Shift+Enter for newline
  - While processing, show a typing indicator (three animated dots) in the chat area
- **Template pills (shown when chat is empty):**
  - A "Start from a template" section above the input when there are no messages yet
  - Row of template cards (not just pills — small cards with icon, name, description, governance level badge)
  - On template click, auto-populate the input with the template's `defaultPrompt` AND auto-send it
- **Follow-up refinement:**
  - After a pipeline is generated, the user can type follow-up messages like "add a filter for orders over $500" or "change the output to Delta Lake"
  - The system sends the existing pipeline + the refinement request to the intent parser
  - This creates a back-and-forth conversational flow, not a one-shot form
- **Example pills (shown below templates when chat is empty):**
  - Smaller chips for quick examples: "Weekly Sales Report", "S3 → Delta Lake ETL", "Unity Catalog Sync", "Customer Data Quality Audit"
  - On pill click, populate input and auto-send
- On error, display the error message as an assistant message with red styling

### 4d. Create `src/components/CodePreview.tsx`

The generated PySpark code display:
- Uses Monaco Editor (`@monaco-editor/react`) in read-only mode
- Language: "python"
- Theme: "vs-dark" (matches the dark UI)
- Props: `code: string | null`, `isLoading: boolean`
- When code is null, show empty state "Generated code will appear here"
- When loading, show a pulsing skeleton
- Include a "Copy Code" button in the top-right corner that copies to clipboard
- Include a "Download as .py" button next to it
- Panel header: "Generated PySpark — Databricks Notebook" with a ◆ Databricks icon and ⚡ spark emoji

### 4e. Create `src/components/ExplanationPanel.tsx`

The validation/explanation side panel:
- Props: `validation: ValidationResult | null`, `selectedStepId: string | null`, `pipeline: PipelineDefinition | null`
- When no step is selected: show ALL explanations in order, as a scrollable list
- When a step is selected: highlight that step's explanation at the top, show its warnings prominently
- Each explanation shows:
  - Step label (bold)
  - Step type badge (colored: blue/amber/green)
  - Plain-English explanation text
  - Any warnings for that step (with severity-colored icon and message)
- Warning severity styling:
  - Low: yellow left border, 💡 icon
  - Medium: orange left border, ⚠️ icon
  - High: red left border, 🚨 icon
- When validation is null / loading, show a skeleton or "Analyzing pipeline..." message
- Panel should be scrollable with a max-height

### 4f. Create `src/components/DeployPanel.tsx`

A simulated deployment UI that mirrors real Databricks/AWS deployment workflows:
- Props: `pipeline: PipelineDefinition | null`, `code: string | null`
- Shows deployment configuration in a card-based layout:
  - **Databricks Workspace section:**
    - Target: "Databricks Workspace" with ◆ Databricks logo/icon
    - Notebook path: auto-generated from pipeline name (e.g., `/Workspace/Pipelines/weekly_sales_report`)
    - Cluster: dropdown with options: "Default Compute (i3.xlarge)", "High Memory (r5.2xlarge)", "GPU (g4dn.xlarge)" — just visual options for demo
    - Databricks Runtime: "14.3 LTS (Spark 3.5.0, Scala 2.12)"
  - **AWS Infrastructure section:**
    - S3 Output Bucket: auto-filled (e.g., `s3://company-data-lake/pipelines/weekly_sales_report/`)
    - IAM Role: "arn:aws:iam::role/databricks-pipeline-role" (prefilled)
    - Region: "us-west-2" (dropdown)
  - **Schedule section:**
    - If pipeline has a schedule, show it as a human-readable string ("Every Monday at 9:00 AM") and the cron expression
    - If no schedule: show "On-demand (manual trigger)"
    - Show "Managed via Databricks Jobs API" subtitle
  - **Delta Lake Output section (if applicable):**
    - Delta table path or Unity Catalog table name
    - Partition columns (if specified)
    - Z-ORDER columns (if specified)
    - "OPTIMIZE after write" toggle (default on)
- A large "Deploy to Databricks" button (with ◆ icon)
- On click, simulate a multi-step deployment:
  - Step 1: "Creating Databricks notebook..." (0.5s)
  - Step 2: "Configuring AWS IAM permissions..." (0.5s)
  - Step 3: "Registering job with Databricks Jobs API..." (0.5s)
  - Step 4: "Setting up Delta Lake output tables..." (0.5s)
  - Step 5: "Scheduling pipeline..." (0.5s)
  - Then show a success confirmation with:
    - Green checkmark
    - "Pipeline deployed successfully!"
    - Databricks Job ID: `job-12847` (fake)
    - Notebook path
    - S3 output location
    - Delta table location (if applicable)
    - Next scheduled run (if applicable)
    - A fake "Open in Databricks ↗" link
- This is NOT a real deployment — it's simulated for the hackathon demo, but it should LOOK real and demonstrate knowledge of the actual Databricks/AWS deployment workflow

### 4g. Create `src/components/GovernancePanel.tsx`

The governance & compliance panel — this is the KEY DIFFERENTIATOR for judges:
- Props: `checks: GovernanceCheck[]`, `isChecking: boolean`, `role: UserRole`, `pipeline: PipelineDefinition | null`
- **Header:** "Governance & Compliance" with a 🛡️ shield icon and an overall status badge:
  - All pass: Green "Compliant" badge
  - Has warnings: Yellow "Review Required" badge
  - Has failures: Red "Non-Compliant" badge
- **Check list:** Each governance check rendered as a row with:
  - Status icon: ✅ pass, ⚠️ warning, ❌ fail
  - Rule name (bold): "PII Detection", "Access Control", "Data Quality", "Catalog Access", "Complexity", "Data Masking"
  - Message describing the result
  - Expandable details section (click to expand)
- **PII Detection section (prominent):**
  - If PII columns are found, show a highlighted box listing them with masking status
  - Show which columns will be auto-masked in analyst/viewer mode
  - Example: "⚠️ Detected PII: email, phone_number, salary — columns will be masked for analyst role"
- **Access Control section:**
  - Shows which operations the current role can/cannot perform
  - If any pipeline step violates the role's permissions, show a red fail with the specific step and operation
- **Approval flow (when `requiresApproval` is true):**
  - Show "Requires Admin Approval" banner at bottom
  - In admin view: show "Approve Pipeline" button
  - In analyst view: show "Submit for Approval" button (simulated)
- **Audit Log (collapsible):**
  - Show a mini audit trail of actions taken (pipeline created, governance checked, etc.) with timestamps
  - This is simulated but shows judges we understand audit requirements
- When `isChecking` is true, show skeleton loading
- When no pipeline exists, show empty state: "Governance checks will appear when you build a pipeline"

### 4h. Create `src/components/TemplateLibrary.tsx`

The template/blueprint library — shows the "factory" concept:
- Props: `templates: PipelineTemplate[]`, `onSelectTemplate: (template: PipelineTemplate) => void`, `isVisible: boolean`
- Renders as a modal overlay or a slide-out panel from the left
- **Header:** "Pipeline Templates" with subtitle "Pre-configured blueprints with built-in governance"
- **Template categories** as horizontal tabs: "All", "ETL", "Analytics", "Quality", "Reporting"
- **Template cards** in a grid (2 columns):
  - Each card shows:
    - Category icon (📥 ETL, 📊 Analytics, 🔍 Quality, 📈 Reporting)
    - Template name (bold)
    - Description (1-2 sentences)
    - Governance level badge: "Low" (green), "Medium" (yellow), "High" (red)
    - Expected step count: "~5 steps"
    - "Use Template →" button
  - On click, close the template library, populate the chat with the template's defaultPrompt, and auto-send
- **Hardcoded templates (create in `src/data/templates.ts`):**
  1. **S3 to Delta Lake ETL** — "Load raw CSV/JSON data from S3 buckets, clean and transform, write to Delta Lake tables in Unity Catalog" (ETL, Medium governance)
  2. **Customer 360 View** — "Combine customer data from multiple sources, deduplicate, enrich with transaction history, write unified profile to Delta Lake" (Analytics, High governance — PII involved)
  3. **Data Quality Audit** — "Read a Delta table, run data quality checks (nulls, duplicates, outliers), generate a quality report with statistics" (Quality, Low governance)
  4. **Weekly Sales Report** — "Aggregate sales data by region and rep, calculate KPIs, write summary to Unity Catalog reporting schema" (Reporting, Medium governance)
  5. **Incremental Data Sync** — "Read new records from S3, merge into existing Delta Lake table using MERGE/upsert pattern" (ETL, High governance)
  6. **Cross-Source Join** — "Join data from Unity Catalog with CSV uploads from S3, filter and aggregate, write results to Redshift" (Analytics, High governance)

### 4i. Create `src/components/RoleToggle.tsx`

An admin/analyst view toggle for the header:
- Props: `currentRole: UserRole`, `onRoleChange: (role: UserRole) => void`
- Renders as a segmented control / toggle in the header bar: "👤 Analyst" | "🔧 Admin"
- **Analyst view (default):**
  - Shows governance restrictions in the GovernancePanel
  - Chat interface shows guardrails ("You can access: Delta Lake, Unity Catalog, CSV, S3...")
  - Deploy button says "Submit for Approval" instead of "Deploy"
  - Template library shows only templates the analyst role can use
  - PII columns are masked in code preview (show as `[MASKED]` in display() output)
- **Admin view:**
  - All restrictions lifted in governance panel — shows "Full Access"
  - Can approve pipelines in the GovernancePanel
  - Deploy button says "Deploy to Databricks"
  - Template library shows all templates + an "Edit Templates" button (visual only)
  - Governance panel shows the full policy configuration (what each role can/cannot do)
  - Shows audit log prominently
- Switching roles triggers a re-run of governance checks with the new role
- Visual indicator: Admin view has a subtle purple border on the main container, Analyst view has a blue border

### 4j. Create `src/components/LoadingSkeleton.tsx`

A reusable loading skeleton component for the pipeline diagram, code panel, explanation panel, and governance panel. Use animated Tailwind pulse: `animate-pulse bg-slate-800 rounded`.

**Commit: "feat: add all frontend components including governance, templates, chat, and role toggle"**

---

## STEP 5: MAIN PAGE ASSEMBLY

### Create `src/app/page.tsx`

The main (and only) page of the application. This assembles all components and manages application state.

**Layout:** A two-column layout with chat on the left and results on the right:

```
┌──────────────────────────────────────────────────────────────┐
│  Header: "PipelineGPT" + tagline    [👤 Analyst | 🔧 Admin]  │
│          "Powered by Databricks ◆ + AWS ☁"  [📋 Templates]  │
├────────────────────┬─────────────────────────────────────────┤
│                    │  ┌─────────────────────────────────┐    │
│  Chat Interface    │  │  Pipeline Diagram (React Flow)  │    │
│  (conversational)  │  └─────────────────────────────────┘    │
│                    │  ┌────────────────┬────────────────┐    │
│  [user bubble]     │  │ Code Preview   │  Explanation   │    │
│  [assistant reply] │  │ (Monaco)       │  Panel         │    │
│  [user refinement] │  ├────────────────┴────────────────┤    │
│  [assistant reply] │  │ Governance & Compliance Panel   │    │
│                    │  │ 🛡️ PII | Access | Quality       │    │
│  ─────────────     │  ├─────────────────────────────────┤    │
│  [input bar]       │  │ Deploy Panel (collapsible)      │    │
├────────────────────┴─────────────────────────────────────────┤
│  Footer: "Built at HackUSU 2026 • Data App Factory Track"   │
└──────────────────────────────────────────────────────────────┘
```

The left column (chat) takes ~35% width. The right column (results) takes ~65%. This is a standard AI assistant layout (like ChatGPT with artifacts, or Cursor).

**State management:** Use React useState for all app state:

```typescript
// Chat state
const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
const [userInput, setUserInput] = useState("");
// Pipeline state
const [pipeline, setPipeline] = useState<PipelineDefinition | null>(null);
const [generatedCode, setGeneratedCode] = useState<string | null>(null);
const [validation, setValidation] = useState<ValidationResult | null>(null);
const [governanceChecks, setGovernanceChecks] = useState<GovernanceCheck[]>([]);
// Loading states
const [isParsingIntent, setIsParsingIntent] = useState(false);
const [isGeneratingCode, setIsGeneratingCode] = useState(false);
const [isValidating, setIsValidating] = useState(false);
const [isCheckingGovernance, setIsCheckingGovernance] = useState(false);
// UI state
const [error, setError] = useState<string | null>(null);
const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
const [currentRole, setCurrentRole] = useState<UserRole>("analyst");
const [showDeploy, setShowDeploy] = useState(false);
const [showTemplates, setShowTemplates] = useState(false);
const [activeTemplate, setActiveTemplate] = useState<PipelineTemplate | null>(null);
```

**Flow when user sends a chat message:**

1. Add user message to `chatMessages`
2. Set `isParsingIntent = true`
3. If this is a NEW pipeline (no existing pipeline): call `POST /api/parse-intent` with the message
4. If this is a REFINEMENT (pipeline already exists): call `POST /api/refine-pipeline` with the existing pipeline + the message
5. On success: set `pipeline`, add assistant message to chat ("I've built a pipeline with X steps: [step list]..."), set `isParsingIntent = false`
6. Immediately set `isGeneratingCode = true`
7. Call `POST /api/generate-code` with the pipeline
8. On success: set `generatedCode`, set `isGeneratingCode = false`
9. Immediately set `isValidating = true` AND `isCheckingGovernance = true`
10. Call `POST /api/validate` AND `POST /api/governance-check` IN PARALLEL
11. On success: set `validation` and `governanceChecks`, set loading states to false
12. Add assistant message summarizing: "Pipeline is ready! [X governance checks passed, Y warnings]. You can refine it or deploy."
13. On any error: set `error`, add error as assistant message in chat

This creates a cascading effect where the user sees: diagram appears → code appears → explanations + governance checks appear. Each stage fills in progressively. The chat maintains conversation history so the user can keep refining.

**Responsive design:**
- On screens >= 1280px: two-column layout (chat | results)
- On screens < 1280px: tabbed layout — "Chat" tab and "Results" tab with a toggle
- The chat should always be accessible

**Header:** Clean header bar with:
- Left: "PipelineGPT" logo with tagline "Natural Language → Databricks Pipelines" and "Powered by Databricks ◆ + AWS ☁"
- Center: "📋 Templates" button that opens the TemplateLibrary
- Right: RoleToggle component (👤 Analyst | 🔧 Admin), Demo button, Reset button, "Built at HackUSU 2026"

### Create `src/app/layout.tsx`

Update the root layout:
- Set the HTML lang to "en"
- Set background to `bg-slate-950`
- Set text color to `text-white`
- Use a clean system font stack
- Meta title: "PipelineGPT — Natural Language to Databricks Pipelines"
- Meta description: "Build Databricks data pipelines by describing them in plain English. Generates visual DAG diagrams, production-ready PySpark code, and deploys to Databricks on AWS."

**Commit: "feat: assemble main page with chat + results layout, governance, and role switching"**

---

## STEP 6: POLISH AND UX

1. **Loading states:** Each panel should show a distinct skeleton while its API call is in progress. The pipeline diagram skeleton should show faint placeholder nodes. The governance panel should show a scanning animation.

2. **Error handling:** If any API call fails, show the error as an assistant message in the chat (red styling). Include a "Try Again" suggestion in the message. Don't crash the whole UI.

3. **Transitions:** Add subtle fade-in transitions when panels populate (use Tailwind `transition-opacity duration-300`).

4. **Template & example interaction:** When a user clicks a template card or example pill, it should auto-populate the chat input AND auto-send (immediately trigger the build flow). This is critical for the demo — one click to see the whole thing.

5. **Node selection:** When a user clicks a node in the pipeline diagram, scroll the explanation panel to that step's explanation and highlight it. Scroll the code to the relevant section if possible (or highlight the step comment). Also highlight the corresponding governance check if one exists for that step.

6. **Code copy feedback:** When "Copy Code" is clicked, briefly show "Copied!" in green.

7. **Chat auto-scroll:** Chat should auto-scroll to the latest message. When the assistant is "typing" (processing), show animated dots.

8. **Deploy panel:** Make it collapsible. Show a "Deploy" button in the header area that reveals the deploy panel when clicked. Default to hidden.

9. **Empty state:** When the app first loads, the right-side panels should show a welcoming empty state. The pipeline diagram: "Your pipeline will appear here." The code panel: "Your PySpark Databricks notebook will appear here." The explanation panel: "Step-by-step explanations will appear here." The governance panel: "Governance checks will run when you build a pipeline." The chat should show the template cards and example pills as the initial state.

10. **Keyboard shortcut:** Enter to send chat message, Shift+Enter for newline.

**Commit: "feat: add polish — loading states, transitions, error handling, keyboard shortcuts"**

---

## STEP 7: DEMO MODE

Add a "Demo" button in the header that:
1. Auto-sends "Take the sample sales CSV from S3, clean the dates, filter for orders over $100, join with customer data from Unity Catalog, aggregate revenue by region, and write the results to a Delta Lake table partitioned by region" as a chat message
2. Automatically triggers the full build flow (intent parse → code gen → validation → governance)
3. In one click, the judges see: chat message appears → assistant responds → diagram builds → code generates → explanations appear → governance checks show all passing with one PII warning
4. After a 2-second pause, auto-send a follow-up refinement: "Also add a deduplication step before the join, and mask the customer email column"
5. The pipeline updates, governance panel shows the masking applied — demonstrating the CONVERSATIONAL and GOVERNANCE features in one seamless demo

This is the single most important UX feature for the hackathon demo. It must work flawlessly.

Also add:
- A "Reset" button that clears all state (chat history, pipeline, code, governance) and returns to the empty state
- When Demo mode runs, switch to Analyst view first, then after the full flow completes, briefly switch to Admin view to show the "Approve Pipeline" and full audit log — demonstrating both roles

**Commit: "feat: add demo mode with conversational refinement and role switching"**

---

## STEP 8: FINAL VERIFICATION

Before declaring done, verify ALL of the following:

**Core functionality:**
- [ ] `npm run build` succeeds with zero errors
- [ ] The "Demo" button triggers the full flow end-to-end including refinement
- [ ] All 6 templates produce valid pipeline diagrams when selected
- [ ] Pipeline diagrams render with correct node colors and edge connections
- [ ] Generated PySpark code is syntactically valid (no code fences, proper imports)
- [ ] Generated code starts with "# Databricks notebook source" and uses Delta Lake / Unity Catalog conventions
- [ ] Explanations are plain-English and reference actual column/table names
- [ ] Warnings appear with correct severity styling

**Chat & conversational features:**
- [ ] Chat interface renders user and assistant messages correctly
- [ ] Follow-up refinement works (modify existing pipeline via chat)
- [ ] Template selection auto-populates chat and triggers build
- [ ] Chat auto-scrolls to latest message
- [ ] Typing indicator shows during processing

**Governance features:**
- [ ] Governance panel runs checks after every pipeline build
- [ ] PII detection identifies columns like email, phone, salary
- [ ] Access control checks reflect the current role (analyst vs admin)
- [ ] Switching roles triggers governance re-check
- [ ] Admin view shows "Approve Pipeline" button
- [ ] Analyst view shows "Submit for Approval" button
- [ ] Audit log shows timestamped entries

**UI & polish:**
- [ ] Role toggle switches between Analyst and Admin views
- [ ] Template library opens as modal/panel with 6 templates
- [ ] Code "Copy" button works and shows feedback
- [ ] Node clicking highlights the corresponding explanation and governance check
- [ ] Deploy panel shows simulated multi-step Databricks deployment
- [ ] Error states display correctly in chat (test by temporarily breaking the API key)
- [ ] The UI looks polished on a 1440px-wide screen (typical laptop)
- [ ] No console errors in the browser
- [ ] All environment variables are in `.env.local` (no hardcoded keys)
- [ ] The app loads fast (no unnecessary re-renders or waterfalls)

**Final commit: "feat: complete Data App Factory MVP — ready for demo"**

---

## API CALL REFERENCE

### OpenAI — Function Calling (Stages 1 & 3)

```typescript
const response = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [
    { role: "system", content: systemPrompt },
    { role: "user", content: userMessage },
  ],
  tools: [
    {
      type: "function",
      function: functionDefinition,
    },
  ],
  tool_choice: {
    type: "function",
    function: { name: "function_name" },
  },
  temperature: 0.3,
});

const result = JSON.parse(
  response.choices[0].message.tool_calls![0].function.arguments
);
```

### OpenAI — Standard Completion (Stage 2)

```typescript
const response = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [
    { role: "system", content: CODE_GENERATION_PROMPT },
    { role: "user", content: JSON.stringify(pipeline, null, 2) },
  ],
  temperature: 0.2,
});

const code = response.choices[0].message.content;
```

---

## FILE STRUCTURE (FINAL)

```
src/
├── app/
│   ├── page.tsx                     # Main page — two-column layout with chat + results
│   ├── layout.tsx                   # Root layout (dark theme)
│   ├── globals.css                  # Tailwind imports + custom styles
│   └── api/
│       ├── parse-intent/
│       │   └── route.ts             # Stage 1: NL → pipeline JSON
│       ├── generate-code/
│       │   └── route.ts             # Stage 2: pipeline JSON → PySpark
│       ├── validate/
│       │   └── route.ts             # Stage 3: code → explanations + warnings
│       ├── governance-check/
│       │   └── route.ts             # Stage 4: governance & compliance checks
│       └── refine-pipeline/
│           └── route.ts             # Conversational refinement of existing pipeline
├── components/
│   ├── PipelineNode.tsx             # Custom React Flow node
│   ├── PipelineDiagram.tsx          # React Flow pipeline visualization
│   ├── ChatInterface.tsx            # Conversational chat (replaces NLInput)
│   ├── CodePreview.tsx              # Monaco Editor code display
│   ├── ExplanationPanel.tsx         # Plain-English explanations + warnings
│   ├── GovernancePanel.tsx          # Governance checks, PII, access control, audit log
│   ├── DeployPanel.tsx              # Simulated Databricks/AWS deployment
│   ├── TemplateLibrary.tsx          # Pipeline template/blueprint selector
│   ├── RoleToggle.tsx               # Admin/Analyst view switcher
│   └── LoadingSkeleton.tsx          # Reusable loading skeletons
├── lib/
│   ├── openai.ts                    # OpenAI client
│   ├── prompts.ts                   # All system prompts
│   ├── functions.ts                 # Function calling schemas
│   ├── governance-rules.ts          # Hardcoded governance policies & PII detection
│   └── pipeline-to-nodes.ts         # Pipeline JSON → React Flow conversion
├── types/
│   └── index.ts                     # All TypeScript types (including governance, chat, templates)
├── data/
│   ├── templates.ts                 # 6 pre-built pipeline templates
│   ├── sample-sales.csv             # (pre-loaded)
│   ├── sample-customers.csv         # (pre-loaded)
│   ├── sample-employees.csv         # (pre-loaded)
    └── pipeline-examples.json       # (pre-loaded)
```

---

## IMPORTANT CONSTRAINTS

**Don'ts:**
- Do NOT add real authentication. Roles (admin/analyst) are a UI toggle, not real auth.
- Do NOT use a database. All state in React useState. Chat history, pipelines, governance checks — all in-memory.
- Do NOT attempt real AWS/Databricks API integration. Simulate deployment — but make it LOOK authentic with real Databricks Job IDs, S3 paths, Unity Catalog references, and IAM role ARNs.
- Do NOT spend time on mobile responsiveness. Optimize for laptop screens (1280-1440px).
- Do NOT over-engineer the governance checks. They are deterministic rule-based checks (no AI call needed). Fast and simple.

**Do's — these win the competition:**
- DO frame everything as a "Data App Factory" — a platform that produces data apps, not just one tool. The template library, role system, and governance are what make it a factory.
- DO make the chat interface feel conversational — follow-ups, refinements, back-and-forth. NOT a static form. This is explicitly called out in the Databricks spec as a judging criterion.
- DO make governance prominent and visible. The Databricks spec says "governance is not optional — it's core." PII detection, access controls, data quality checks, audit logs — these MUST be front and center, not hidden.
- DO make the "Demo" button trigger the full flow including a conversational refinement. Judges need to see the chat + governance in action.
- DO use function calling (not raw completions) for Stages 1 and 3. This is the technical differentiator.
- DO commit after each step with descriptive messages. Judges check commit history.
- DO strip markdown code fences from generated code. GPT-4 sometimes wraps output in ``` even when told not to.
- DO lean heavily into Databricks/AWS terminology and branding throughout the UI. This is a Koch-sponsored track with Databricks and AWS as partners — the more native it feels to their ecosystem, the better it scores.
- DO generate code that starts with "# Databricks notebook source" and uses Delta Lake, Unity Catalog, DBFS, display(), and dbutils conventions.
- DO include 6 templates that showcase Databricks/AWS workflows (S3→Delta ETL, Customer 360, Data Quality, Sales Report, Incremental Sync, Cross-Source Join).
- DO make the UI look premium (dark theme, clean spacing, subtle animations). Visual impression matters enormously at hackathons.
- DO make the role toggle (Admin/Analyst) change the entire experience — different governance results, different deploy options, different template access. This shows judges you understand enterprise access control.
