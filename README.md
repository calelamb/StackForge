# PipelineGPT — Natural Language Data Pipeline Compiler

> **HackUSU 2026** · Data App Factory Track · February 27–28, 2026

---

## The Problem

Every company with data has the same bottleneck. Business teams — sales ops, finance, marketing — constantly need data moved, cleaned, combined, and summarized. A sales VP needs a weekly report on underperforming reps. A marketing director needs campaign data merged with customer records to calculate conversion rates. Finance needs to reconcile billing numbers with analytics.

Each of these requests follows the same structural pattern: read data from a source, transform it, and write the output somewhere. That's a data pipeline. And right now, every one of those pipelines is hand-coded by an engineer.

A senior data engineer costs $150K–$200K per year. They spent years learning distributed computing, Spark internals, and cloud architecture. And they spend a significant chunk of their week writing mechanical variations of the same pattern — read a CSV, clean some dates, join two tables, filter rows, aggregate, write output. The cognitive effort isn't in the code; it's in understanding what the business person wants. The code itself is plumbing.

And it's slow. A request goes into a Jira backlog, gets picked up next week, requires a 30-minute clarification meeting, an hour of coding, an hour of testing, then deployment. Two weeks from "I need this" to "here's your report" — for what is fundamentally a straightforward data operation.

## Our Solution

PipelineGPT eliminates the translation layer between business intent and executable code.

Instead of: **Business person → describes need → Data engineer → writes Spark code → Pipeline runs**

You get: **Business person → describes need → PipelineGPT → generates Spark code → Pipeline runs**

Type this:

> "Pull the sales data from S3, clean up the date formats, join it with the customer table, filter for enterprise accounts over $50K, and summarize total revenue by region."

Get this:
1. A **visual pipeline diagram** — boxes connected by arrows showing each step
2. **Production-ready PySpark code** — real, executable Databricks notebook code
3. **Plain-English explanations** — what each step does, plus warnings about potential issues

The entire process that used to take two weeks now takes two minutes.

## How It Works — Three-Stage AI Compiler

This is not a ChatGPT wrapper. PipelineGPT is architecturally a **compiler** — but the parser is an LLM and the target language is PySpark.

### Stage 1: Intent Parsing

The user's natural language gets converted into a structured pipeline definition using GPT-4 function calling. The model is constrained to output valid JSON matching a strict schema — source nodes, transform nodes, destination nodes, each with operation-specific configuration and dependency chains.

"Join with customers" becomes `{ operation: "join", config: { joinKey: "customer_id", joinType: "inner" } }`. The model can't hallucinate freeform text — it fills in a formal grammar.

### Stage 2: Code Generation

The structured pipeline JSON is passed to a second GPT-4 call that generates real PySpark code. This is more than string templating — the model understands Spark semantics. It handles schema inference for CSV sources, column collision in joins, type casting in filters, and proper aggregation function selection. A template engine would need hand-coded cases for every combination; the LLM handles the combinatorial explosion naturally.

### Stage 3: Validation & Explanation

A third GPT-4 call reviews the pipeline and generated code, producing plain-English explanations ("Step 3 combines your sales data with the customer database by matching on customer ID") and warnings ("The inner join will drop sales records without a matching customer — consider a left join if you want to keep all records"). These catch issues that even human engineers miss.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Next.js 14 (App Router, TypeScript) |
| Styling | Tailwind CSS |
| AI | OpenAI GPT-4o — function calling (Stages 1 & 3), standard completion (Stage 2) |
| Pipeline Visualization | React Flow |
| Code Display | Monaco Editor (VS Code's editor) |
| Deployment | Vercel |

## AI Architecture

| Stage | Input | AI Technique | Output |
|---|---|---|---|
| 1. Intent Parsing | Natural language | GPT-4 function calling → constrained JSON | Structured pipeline definition |
| 2. Code Generation | Pipeline JSON | GPT-4 completion with PySpark system prompt | Executable PySpark code |
| 3. Validation | Pipeline + Code | GPT-4 function calling → explanations | Plain-English explanations + warnings |

Three distinct AI calls, each with a different job. The technical depth is in the chain, not any individual call.

## Demo

Click the **"Demo"** button to see the full flow in one click — input populates, diagram builds, code generates, explanations appear.

## Getting Started

### Prerequisites
- Node.js 18+
- OpenAI API key (GPT-4o access)

### Setup
```bash
git clone https://github.com/[YOUR-TEAM]/nl-pipeline-builder.git
cd nl-pipeline-builder
npm install
cp .env.local.example .env.local
# Add your OpenAI API key to .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Sample Data

Pre-loaded datasets in `src/data/` for demos:
- `sample-sales.csv` — 50 sales transactions (intentionally messy date formats)
- `sample-customers.csv` — 30 customer records with account values
- `sample-employees.csv` — 40 employee records across departments

## Team

| Name | Role |
|---|---|
| [Member 1] | AI / Backend Lead |
| [Member 2] | Frontend / UX Lead |
| [Member 3] | Integration / DevOps + Demo |

## Disclosures

- AI coding assistants were used during development
- All application code was written during the hackathon (Feb 27–28, 2026)
- Third-party APIs: OpenAI
- Static data files prepared before the event

## Roadmap

- Real Databricks deployment integration (API-based notebook creation)
- AWS S3 browser for source selection
- Support for SQL targets (Snowflake, Redshift, BigQuery)
- Pipeline versioning and diff tracking
- Collaborative editing with team sharing
- Scheduled pipeline monitoring and alerting
- Natural language pipeline *modification* ("change the filter to $100K instead")

## License

MIT
