# Technical Architecture: Natural Language Data Pipeline Builder

---

## How It Works (End to End)

```
USER                           YOUR SYSTEM                              EXTERNAL
────                           ───────────                              ────────

"Pull sales from S3,      ┌─────────────────────┐
 clean dates, join with    │  STAGE 1: PARSE      │
 customers, filter for  ──▶│                      │──▶  OpenAI GPT-4
 accounts > $10K"          │  Natural Language     │     (function calling)
                           │  → Structured JSON    │
                           └──────────┬────────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │  Pipeline JSON       │
                           │                      │
                           │  {                   │
                           │    steps: [          │
                           │      {source: S3},   │
                           │      {transform:     │
                           │        clean_dates}, │
                           │      {transform:     │
                           │        join},        │
                           │      {transform:     │
                           │        filter},      │
                           │      {dest: report}  │
                           │    ]                 │
                           │  }                   │
                           └──────────┬────────────┘
                                      │
                          ┌───────────┼───────────┐
                          ▼                       ▼
               ┌──────────────────┐   ┌──────────────────┐
               │  VISUAL RENDER    │   │  STAGE 2:         │
               │                   │   │  CODE GENERATION   │
               │  React Flow       │   │                    │──▶ OpenAI GPT-4
               │  pipeline diagram │   │  Pipeline JSON     │    (code gen prompt)
               │  (nodes + edges)  │   │  → PySpark code    │
               └──────────────────┘   └─────────┬──────────┘
                                                │
                          ┌─────────────────────┤
                          ▼                     ▼
               ┌──────────────────┐   ┌──────────────────┐
               │  CODE PREVIEW     │   │  STAGE 3:         │
               │                   │   │  VALIDATE          │
               │  Monaco Editor    │   │                    │──▶ OpenAI GPT-4
               │  (syntax-         │   │  Check for errors, │    (validation prompt)
               │   highlighted     │   │  explain each step │
               │   PySpark)        │   │  in plain English  │
               └──────────────────┘   └─────────┬──────────┘
                                                │
                                                ▼
                                     ┌──────────────────┐
                                     │  EXPLANATION       │
                                     │  PANEL             │
                                     │                    │
                                     │  "Step 1: Reads    │
                                     │   CSV files from   │
                                     │   your S3 bucket"  │
                                     │                    │
                                     │  "Step 3: Joins    │
                                     │   using customer_  │
                                     │   id as the key"   │
                                     │                    │
                                     │  "⚠ Warning: CSV   │
                                     │   has no schema —  │
                                     │   types will be    │
                                     │   inferred"        │
                                     └──────────────────┘
                                                │
                                                ▼
                                     ┌──────────────────┐
                                     │  DEPLOY            │
                                     │                    │
                                     │  → Databricks      │──▶ Databricks REST API
                                     │    Notebook        │
                                     │  → S3 output       │──▶ AWS S3
                                     │  → Scheduled job   │──▶ EventBridge / cron
                                     └──────────────────┘
```

---

## Stage 1: Intent Parsing (Deep Dive)

### What Happens
The user's natural language input gets converted into a structured pipeline definition. This is the most critical AI step — if parsing is wrong, everything downstream breaks.

### How It Works
You use **OpenAI function calling** (also called "tool use"). This means you define a JSON schema that describes what a valid pipeline looks like, and GPT-4 fills it in based on the user's input. The model is constrained to output data that matches your schema — no hallucinated formats, no freeform text.

### The Function Definition You Send to OpenAI

```javascript
// This is what you register as a "function" with the OpenAI API
const parsePipelineFunction = {
  name: "create_pipeline",
  description: "Parse a natural language data pipeline request into a structured definition",
  parameters: {
    type: "object",
    properties: {
      pipeline_name: {
        type: "string",
        description: "A short, descriptive name for this pipeline"
      },
      schedule: {
        type: "object",
        properties: {
          frequency: {
            type: "string",
            enum: ["once", "hourly", "daily", "weekly", "monthly"],
            description: "How often the pipeline should run"
          },
          day_of_week: {
            type: "string",
            description: "Day of week if weekly (e.g., 'monday')"
          },
          time: {
            type: "string",
            description: "Time of day in HH:MM format"
          }
        }
      },
      steps: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id: {
              type: "string",
              description: "Unique step identifier (e.g., 'step_1')"
            },
            type: {
              type: "string",
              enum: ["source", "transform", "destination"]
            },
            operation: {
              type: "string",
              enum: [
                "read_csv", "read_json", "read_parquet", "read_database",
                "filter", "join", "aggregate", "sort", "rename_columns",
                "cast_types", "clean_dates", "deduplicate", "fill_nulls",
                "write_csv", "write_parquet", "write_table", "email_report"
              ]
            },
            config: {
              type: "object",
              description: "Operation-specific configuration",
              properties: {
                // Source configs
                bucket: { type: "string" },
                path: { type: "string" },
                format: { type: "string" },
                table_name: { type: "string" },

                // Transform configs
                column: { type: "string" },
                condition: { type: "string" },
                join_key: { type: "string" },
                join_type: {
                  type: "string",
                  enum: ["inner", "left", "right", "outer"]
                },
                right_source: { type: "string" },
                group_by: { type: "array", items: { type: "string" } },
                aggregations: { type: "array", items: { type: "string" } },

                // Destination configs
                output_path: { type: "string" },
                recipient: { type: "string" }
              }
            },
            depends_on: {
              type: "array",
              items: { type: "string" },
              description: "IDs of steps this step depends on"
            }
          },
          required: ["id", "type", "operation", "config"]
        }
      }
    },
    required: ["pipeline_name", "steps"]
  }
};
```

### Example: What GPT-4 Returns

**User input:**
> "Every Monday, pull the sales CSV from our S3 bucket, clean up the date formats, join it with the customer table in Databricks, filter for accounts over $10K, and email me a summary."

**GPT-4 structured output:**

```json
{
  "pipeline_name": "weekly_high_value_sales_report",
  "schedule": {
    "frequency": "weekly",
    "day_of_week": "monday",
    "time": "09:00"
  },
  "steps": [
    {
      "id": "step_1",
      "type": "source",
      "operation": "read_csv",
      "config": {
        "bucket": "company-data",
        "path": "sales/",
        "format": "csv"
      },
      "depends_on": []
    },
    {
      "id": "step_2",
      "type": "transform",
      "operation": "clean_dates",
      "config": {
        "column": "order_date",
        "input_format": "MM/dd/yyyy",
        "output_format": "yyyy-MM-dd"
      },
      "depends_on": ["step_1"]
    },
    {
      "id": "step_3",
      "type": "transform",
      "operation": "join",
      "config": {
        "right_source": "databricks://default.customers",
        "join_key": "customer_id",
        "join_type": "inner"
      },
      "depends_on": ["step_2"]
    },
    {
      "id": "step_4",
      "type": "transform",
      "operation": "filter",
      "config": {
        "condition": "account_value > 10000"
      },
      "depends_on": ["step_3"]
    },
    {
      "id": "step_5",
      "type": "destination",
      "operation": "email_report",
      "config": {
        "recipient": "user@company.com",
        "format": "summary_table"
      },
      "depends_on": ["step_4"]
    }
  ]
}
```

### Why This Is Technically Impressive
- **Constrained generation** — the model can only output valid pipeline definitions, not freeform text
- **Dependency graph** — each step knows what it depends on, enabling parallel execution and correct ordering
- **Extensible** — adding a new operation (like "pivot" or "window function") is just adding an enum value and config schema

---

## Stage 2: Code Generation (Deep Dive)

### What Happens
The structured pipeline JSON gets converted into real, executable PySpark code.

### How It Works
A second GPT-4 call with a different system prompt. This prompt says: "You are a PySpark code generator. Given a pipeline definition, produce a complete Databricks notebook. Follow Spark best practices."

### The System Prompt (Simplified)

```
You are a PySpark code generation engine for Databricks notebooks.

Given a pipeline definition in JSON, generate a complete, executable PySpark script.

Rules:
- Use PySpark DataFrame API (not RDD)
- Import only what's needed
- Add clear comments for each step
- Handle schema inference for CSV sources
- Use proper column types (don't leave everything as string)
- Use `col()` for column references in filters and joins
- Name intermediate DataFrames descriptively
- End with a display() or write operation

Output ONLY the Python code. No markdown, no explanation.
```

### Example Generated Code

```python
# ============================================
# Pipeline: weekly_high_value_sales_report
# Schedule: Every Monday at 09:00
# Generated by [Your Tool Name]
# ============================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, sum as _sum, count

# Initialize Spark session
spark = SparkSession.builder.appName("weekly_high_value_sales_report").getOrCreate()

# ── Step 1: Read sales data from S3 ──────────────────────
df_sales = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("inferSchema", "true")
    .load("s3://company-data/sales/")
)

# ── Step 2: Clean date formats ───────────────────────────
df_sales = df_sales.withColumn(
    "order_date",
    to_date(col("order_date"), "MM/dd/yyyy")
)

# ── Step 3: Join with customer table ─────────────────────
df_customers = spark.table("default.customers")

df_joined = df_sales.join(
    df_customers,
    on="customer_id",
    how="inner"
)

# ── Step 4: Filter high-value accounts ───────────────────
df_high_value = df_joined.filter(col("account_value") > 10000)

# ── Step 5: Generate summary report ─────────────────────
df_summary = (
    df_high_value
    .groupBy("sales_rep", "region")
    .agg(
        _sum("order_total").alias("total_revenue"),
        count("order_id").alias("num_orders")
    )
    .orderBy(col("total_revenue").desc())
)

# Display results (Databricks notebook output)
display(df_summary)
```

### What Makes This More Than Just String Templating
The model adapts the code based on context:
- If the source is CSV, it adds `inferSchema` and `header` options
- If there's a join, it picks the right join type and handles the key correctly
- If there's a filter with a string condition, it wraps it in `expr()` instead of `col()`
- It names variables descriptively based on what they contain
- It adds appropriate aggregation functions based on the destination type

A template engine can't do this — it would need a case for every combination. The LLM handles the combinatorial explosion naturally.

---

## Stage 3: Validation & Explanation (Deep Dive)

### What Happens
Before the user deploys, the AI reviews the generated code and:
1. Checks for logical errors or missing steps
2. Generates a plain-English explanation of each step
3. Flags warnings and suggestions

### Example Output

```json
{
  "validation": {
    "status": "pass",
    "warnings": [
      {
        "step": "step_1",
        "message": "CSV source uses schema inference. If column types are inconsistent across files, this may cause runtime errors. Consider specifying an explicit schema.",
        "severity": "medium"
      },
      {
        "step": "step_3",
        "message": "Inner join will drop sales records that don't have a matching customer. If you want to keep all sales records, consider using a left join instead.",
        "severity": "low"
      }
    ]
  },
  "explanations": [
    {
      "step": "step_1",
      "plain_english": "Reads all CSV files from your S3 bucket at 'company-data/sales/'. Column types are automatically detected."
    },
    {
      "step": "step_2",
      "plain_english": "Converts the 'order_date' column from MM/DD/YYYY format to the standard YYYY-MM-DD format that Spark handles best."
    },
    {
      "step": "step_3",
      "plain_english": "Combines your sales data with the customer database by matching on 'customer_id'. Only records that exist in both tables are kept."
    },
    {
      "step": "step_4",
      "plain_english": "Keeps only records where the account value exceeds $10,000."
    },
    {
      "step": "step_5",
      "plain_english": "Groups results by sales rep and region, calculates total revenue and order count, then sends a summary report to your email."
    }
  ]
}
```

---

## The Visual Pipeline (What the User Sees)

Built with **React Flow** — a library specifically designed for node-based diagrams.

```
┌──────────────────────────────────────────────────────────┐
│  Pipeline: weekly_high_value_sales_report                │
│  Schedule: Every Monday at 9:00 AM                       │
│                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐              │
│  │   S3    │    │  Clean  │    │  Join   │              │
│  │  CSV    │───▶│  Dates  │───▶│  with   │              │
│  │  Source │    │         │    │Customers│              │
│  └─────────┘    └─────────┘    └────┬────┘              │
│                                     │                    │
│                                     ▼                    │
│                               ┌─────────┐               │
│                               │ Filter  │               │
│                               │  > $10K │               │
│                               └────┬────┘               │
│                                    │                     │
│                                    ▼                     │
│                               ┌─────────┐               │
│                               │  Email  │               │
│                               │ Report  │               │
│                               └─────────┘               │
│                                                          │
│  [Generate Code]  [Preview on Sample Data]  [Deploy]     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

Each node is clickable — when you click it, the explanation panel shows what that step does in plain English, plus any warnings.

---

## What You Are NOT Building

To be absolutely clear for the team:

| What it sounds like | What you're actually doing |
|---|---|
| "NLP model architecture" | Using GPT-4 API with function calling — NOT training a model |
| "ML pipeline" | Chaining API calls with structured I/O — NOT building a training pipeline |
| "Custom model" | Engineering prompts + schemas — NOT fine-tuning |
| "Data pipeline" | Generating pipeline CODE — NOT running data pipelines yourself |

Your technical contribution is:
1. The **function schema design** (how you define what a valid pipeline looks like)
2. The **prompt engineering** (how you instruct GPT-4 to generate correct PySpark)
3. The **chained architecture** (parse → generate → validate, each a distinct AI call)
4. The **visual interface** (React Flow diagram + Monaco code editor)

This is a legitimate, technically deep project. You're building a compiler, essentially — but the "parser" is an LLM and the "target language" is PySpark.

---

## API Call Flow (Sequence Diagram)

```
User          Frontend        API Routes       OpenAI         AWS/Databricks
 │               │               │               │               │
 │  Types NL     │               │               │               │
 │  request      │               │               │               │
 │──────────────▶│               │               │               │
 │               │  POST /api/   │               │               │
 │               │  parse-intent │               │               │
 │               │──────────────▶│               │               │
 │               │               │  function     │               │
 │               │               │  calling      │               │
 │               │               │──────────────▶│               │
 │               │               │  pipeline JSON│               │
 │               │               │◀──────────────│               │
 │               │  pipeline JSON│               │               │
 │               │◀──────────────│               │               │
 │  Sees diagram │               │               │               │
 │◀──────────────│               │               │               │
 │               │               │               │               │
 │  Clicks       │               │               │               │
 │  "Generate"   │               │               │               │
 │──────────────▶│               │               │               │
 │               │  POST /api/   │               │               │
 │               │  generate     │               │               │
 │               │──────────────▶│               │               │
 │               │               │  code gen     │               │
 │               │               │  prompt       │               │
 │               │               │──────────────▶│               │
 │               │               │  PySpark code │               │
 │               │               │◀──────────────│               │
 │               │               │               │               │
 │               │               │  validate     │               │
 │               │               │──────────────▶│               │
 │               │               │  explanations │               │
 │               │               │◀──────────────│               │
 │               │  code +       │               │               │
 │               │  explanations │               │               │
 │               │◀──────────────│               │               │
 │  Sees code +  │               │               │               │
 │  explanations │               │               │               │
 │◀──────────────│               │               │               │
 │               │               │               │               │
 │  Clicks       │               │               │               │
 │  "Deploy"     │               │               │               │
 │──────────────▶│               │               │               │
 │               │  POST /api/   │               │               │
 │               │  deploy       │               │               │
 │               │──────────────▶│               │               │
 │               │               │  Create notebook / upload     │
 │               │               │──────────────────────────────▶│
 │               │               │  Success                      │
 │               │               │◀──────────────────────────────│
 │               │  Deploy       │               │               │
 │               │  confirmed    │               │               │
 │               │◀──────────────│               │               │
 │  "Pipeline    │               │               │               │
 │   deployed!"  │               │               │               │
 │◀──────────────│               │               │               │
```

---

## File Structure

```
├── app/
│   ├── page.tsx                    # Main page: NL input + pipeline view
│   ├── api/
│   │   ├── parse-intent/
│   │   │   └── route.ts           # Stage 1: NL → pipeline JSON
│   │   ├── generate-pipeline/
│   │   │   └── route.ts           # Stage 2: JSON → PySpark code
│   │   ├── validate/
│   │   │   └── route.ts           # Stage 3: Code → explanations + warnings
│   │   └── deploy/
│   │       └── route.ts           # Deploy to Databricks (real or simulated)
│   └── layout.tsx
├── components/
│   ├── NLInput.tsx                 # Text input + example prompts
│   ├── PipelineDiagram.tsx         # React Flow visual pipeline
│   ├── PipelineNode.tsx            # Custom node component
│   ├── CodePreview.tsx             # Monaco editor with PySpark
│   ├── ExplanationPanel.tsx        # Plain-English step explanations
│   ├── WarningBanner.tsx           # Validation warnings
│   └── DeployButton.tsx            # Deploy flow UI
├── lib/
│   ├── openai.ts                   # OpenAI client config
│   ├── functions.ts                # Function calling schema definitions
│   ├── prompts.ts                  # System prompts for each stage
│   ├── pipeline-to-nodes.ts        # Convert pipeline JSON → React Flow nodes
│   └── databricks.ts               # Databricks API client (or mock)
├── data/
│   ├── sample-sales.csv            # Demo dataset
│   └── sample-customers.csv        # Demo dataset
├── .env.local
├── package.json
└── README.md
```
