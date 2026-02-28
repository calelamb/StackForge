# Backup Plan: Data App Factory Track (Koch / AWS / Databricks)

**When to switch:** If the Sandbox / Tech Start-Up track rubric feels unfavorable, or if the team wants a more technically impressive project that plays directly to sponsor judges (Koch, AWS, Databricks).

**Track prompt:** Empower business users to deploy data apps via natural language.

---

## The Idea: Natural Language Data Pipeline Builder

### One-liner
A tool where a non-technical business user describes a data workflow in plain English — and the system generates, previews, and deploys a working data pipeline on AWS/Databricks.

### The Problem
Business analysts and ops teams constantly need data pipelines — weekly reports, data cleaning jobs, dashboard feeds, ETL workflows. Today they either wait weeks for engineering, learn SQL/Python themselves, or cobble together fragile spreadsheet macros. The gap between "I need this data transformed" and "a pipeline is running" is massive.

### The Solution
A web interface where a user types something like:

> "Every Monday, pull the sales CSV from our S3 bucket, clean up the date formats, join it with the customer table in Databricks, filter for accounts over $10K, and email me a summary report."

The system:
1. **Parses the request** using GPT-4 function calling → structured pipeline definition (source, transforms, destination, schedule)
2. **Generates a visual pipeline diagram** showing each step so the user can verify before deploying
3. **Produces executable code** — Databricks notebook (PySpark) or AWS Glue job definition
4. **Lets the user preview results** on sample data before committing
5. **Deploys with one click** (or simulates deployment for the demo)

### Why This Wins With These Judges

Koch, AWS, and Databricks judges will look for:
- Actual use of their platforms (not just name-dropping)
- Technical depth — generating real, executable pipeline code is hard and impressive
- Business value — this directly solves the "data engineering bottleneck" every company has
- AI that's structural, not cosmetic — the model isn't just chatting, it's producing executable infrastructure

---

## Technical Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Frontend                           │
│               Next.js (React)                        │
│                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ NL Input   │  │ Pipeline   │  │ Code Preview   │  │
│  │ Interface  │  │ Visualizer │  │ + Deploy Panel │  │
│  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘  │
└────────┼───────────────┼──────────────────┼───────────┘
         │               │                  │
┌────────┼───────────────┼──────────────────┼───────────┐
│        ▼               ▼                  ▼           │
│               Next.js API Routes                      │
│                                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │ /api/      │  │ /api/      │  │ /api/          │   │
│  │ parse-     │  │ generate-  │  │ preview-       │   │
│  │ intent     │  │ pipeline   │  │ deploy         │   │
│  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘   │
└────────┼───────────────┼──────────────────┼───────────┘
         │               │                  │
         ▼               ▼                  ▼
┌──────────────────────────────────────────────────────┐
│                 External Services                     │
│                                                      │
│  ┌────────────┐  ┌────────────────────────────────┐  │
│  │ OpenAI     │  │ AWS / Databricks               │  │
│  │ GPT-4      │  │                                │  │
│  │ (function  │  │  • S3 (data source/dest)       │  │
│  │  calling)  │  │  • Databricks (notebooks,      │  │
│  │            │  │    Spark jobs)                  │  │
│  │            │  │  • AWS Glue (optional)          │  │
│  │            │  │  • CloudWatch/EventBridge       │  │
│  │            │  │    (scheduling)                 │  │
│  └────────────┘  └────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  Static Assets                                 │  │
│  │  • Pipeline templates (JSON)                   │  │
│  │  • Sample datasets for preview                 │  │
│  │  • Code generation templates (Jinja2-style)    │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## AI Integration (3 Layers Deep)

This is where it gets nerdy. The AI isn't just interpreting text — it's generating executable infrastructure.

### Layer 1: Intent Parsing (GPT-4 Function Calling)

User input → structured pipeline definition. The function schema:

```json
{
  "pipeline_name": "weekly_sales_report",
  "schedule": "cron(0 9 ? * MON *)",
  "steps": [
    {
      "type": "source",
      "connector": "s3",
      "config": {
        "bucket": "company-data",
        "path": "sales/",
        "format": "csv"
      }
    },
    {
      "type": "transform",
      "operation": "clean_dates",
      "config": {
        "column": "order_date",
        "input_format": "MM/DD/YYYY",
        "output_format": "YYYY-MM-DD"
      }
    },
    {
      "type": "transform",
      "operation": "join",
      "config": {
        "right_source": "databricks://catalog.schema.customers",
        "join_key": "customer_id",
        "join_type": "inner"
      }
    },
    {
      "type": "transform",
      "operation": "filter",
      "config": {
        "condition": "account_value > 10000"
      }
    },
    {
      "type": "destination",
      "connector": "email_report",
      "config": {
        "recipient": "user@company.com",
        "format": "summary_table"
      }
    }
  ]
}
```

### Layer 2: Code Generation (GPT-4 with Template Context)

Takes the structured pipeline definition and generates actual PySpark / Databricks notebook code:

```python
# Auto-generated Databricks Notebook
# Pipeline: weekly_sales_report
# Generated by [Your Tool Name]

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date

# Step 1: Read source data from S3
df_sales = (spark.read
    .format("csv")
    .option("header", "true")
    .load("s3://company-data/sales/"))

# Step 2: Clean date formats
df_sales = df_sales.withColumn(
    "order_date",
    to_date(col("order_date"), "MM/dd/yyyy")
)

# Step 3: Join with customer table
df_customers = spark.table("catalog.schema.customers")
df_joined = df_sales.join(df_customers, "customer_id", "inner")

# Step 4: Filter high-value accounts
df_filtered = df_joined.filter(col("account_value") > 10000)

# Step 5: Generate summary
df_filtered.createOrReplaceTempView("report_output")
```

The AI generates this by receiving the pipeline JSON + a code generation system prompt with PySpark best practices. This is NOT just string templating — the model understands Spark semantics and handles edge cases (schema inference, type casting, null handling).

### Layer 3: Validation & Explanation

Before deployment, the AI:
- Reviews the generated code for logical errors
- Explains each step in plain English back to the user ("Step 3 will combine your sales data with the customer database using customer_id as the matching key")
- Flags potential issues ("Warning: the CSV doesn't specify a schema — column types will be inferred, which may cause issues with numeric fields")

---

## What to Build in 19 Hours

### Priority 1: The Core Loop (Hours 0–8)
User types natural language → AI parses to structured pipeline → generates visual diagram → generates PySpark code. This is the money shot for the demo.

| Task | Owner | Time |
|---|---|---|
| NL input interface | Frontend Lead | Hours 0–3 |
| `/api/parse-intent` — GPT-4 function calling to pipeline JSON | AI/Backend Lead | Hours 0–4 |
| Pipeline visualizer (React Flow or custom SVG) | Frontend Lead | Hours 3–6 |
| `/api/generate-pipeline` — JSON → PySpark code generation | AI/Backend Lead | Hours 4–8 |
| Wire it all together | Integration Lead | Hours 6–8 |

**Milestone (Hour 8):** User types a sentence, sees a pipeline diagram, clicks "Generate Code", sees real PySpark.

### Priority 2: Preview & Polish (Hours 8–14)
Sample data preview, code syntax highlighting, multiple pipeline templates, error handling.

| Task | Owner | Time |
|---|---|---|
| Code preview panel with syntax highlighting | Frontend Lead | Hours 8–10 |
| Sample data preview ("run on sample") | AI/Backend Lead | Hours 8–11 |
| Pipeline templates (ETL, report, aggregation) | Integration Lead | Hours 8–10 |
| AI explanation panel ("here's what each step does") | AI/Backend Lead | Hours 11–14 |

### Priority 3: AWS/Databricks Integration (Hours 14–17)
This is where you earn bonus points with sponsor judges. Even a simulated deployment flow shows you understand the ecosystem.

| Task | Owner | Time |
|---|---|---|
| "Deploy to Databricks" button (simulated or real) | AI/Backend Lead | Hours 14–16 |
| S3 source browser (list buckets/files) | Integration Lead | Hours 14–16 |
| Schedule configuration UI (cron builder) | Frontend Lead | Hours 14–16 |
| AWS architecture diagram in presentation | Integration Lead | Hour 17 |

### Priority 4: Demo Prep (Hours 17–19)
| Task | Owner | Time |
|---|---|---|
| README, screenshots, Devpost submission | Integration Lead | Hours 17–18 |
| Demo script + rehearsal | ALL | Hours 18–19 |

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **Framework** | Next.js 14 (App Router) | Single codebase |
| **Language** | TypeScript | Type safety for complex pipeline schemas |
| **Styling** | Tailwind CSS | Fast |
| **Pipeline Visualizer** | React Flow | Purpose-built for node/edge diagrams — perfect for pipeline visualization |
| **Code Display** | Monaco Editor (VS Code's editor) or Prism.js | Syntax highlighting, feels professional |
| **AI** | OpenAI GPT-4 (function calling) | Structured outputs for pipeline definitions |
| **AWS** | AWS SDK for JS (S3 at minimum) | Show real AWS integration |
| **Databricks** | Databricks REST API (or simulated) | Generate real notebook JSON |
| **Deploy** | Vercel | Frontend + API routes |

---

## Demo Script (5 Minutes)

**[0:00–0:45] The Problem**
"Every company has a data engineering bottleneck. Business teams need pipelines — weekly reports, data cleaning, ETL jobs — but they wait weeks for engineering to build them. What if they could describe what they need in plain English?"

**[0:45–1:15] The Solution**
"We built [Name] — a natural language data pipeline builder. Describe your workflow, and we'll generate production-ready PySpark code that runs on Databricks."

**[1:15–3:30] Live Demo**
1. Type: "Pull the sales data from S3, clean the date formats, join with customers in Databricks, filter for accounts over $10K, and generate a weekly summary"
2. Show the pipeline diagram being generated (visual node graph)
3. Click into each node — show the AI's plain-English explanation
4. Click "Generate Code" — show real PySpark code with syntax highlighting
5. Click "Preview" — show sample data flowing through the pipeline
6. Show the "Deploy to Databricks" flow

**[3:30–4:30] Technical Depth**
"Three layers of AI: intent parsing via function calling, code generation with PySpark understanding, and validation with plain-English explanations. This isn't string templating — the model understands Spark semantics."

**[4:30–5:00] Impact**
"This turns a 2-week engineering ticket into a 2-minute conversation. Roadmap: support for more connectors, version control for pipelines, and collaborative editing."

---

## Why This is the "Nerdier" Choice

| Dimension | International Student Platform | Data Pipeline Builder |
|---|---|---|
| **AI depth** | Chat + matching (high-level API calls) | Code generation + infrastructure (low-level, structured) |
| **Technical impression** | "They used GPT well" | "They're generating executable Spark code from English" |
| **Sponsor appeal** | General | Directly relevant to Koch, AWS, Databricks |
| **Visual wow factor** | Dashboard + chat | Pipeline diagram + live code generation |
| **Difficulty** | Medium | Hard (but very impressive if pulled off) |
| **Risk** | Lower | Higher (more complex integration) |

---

## Decision Framework: Which Plan to Go With

**Choose the International Student Platform (Sandbox track) if:**
- You want lower risk and higher certainty of a working demo
- The team is more comfortable with standard web app patterns
- The Sandbox track rubric (when revealed) favors market viability and user impact

**Choose the Data Pipeline Builder (Data App Factory track) if:**
- You want to maximize technical impressiveness
- Someone on the team has AWS/Databricks experience (even basic)
- You want to play directly to sponsor judges who live and breathe data infrastructure
- You're comfortable with higher risk / higher reward

**You can also hedge:** Start with the Pipeline Builder (harder), and if by Hour 6 (midnight Friday) you don't have the core loop working, pivot to the Student Platform — you'll still have 13 hours and a clear build plan.

---

## Pre-Hackathon Setup (If Going With This Plan)

- [ ] AWS free tier account with S3 access (or use an existing one)
- [ ] Databricks Community Edition account (free, takes 5 min to set up)
- [ ] Upload 2–3 sample CSV datasets to S3 for demo
- [ ] OpenAI API key with GPT-4 access
- [ ] `npm install reactflow` — test that the pipeline visualizer renders
- [ ] Have a Databricks notebook open so you can show the generated code running during demo
