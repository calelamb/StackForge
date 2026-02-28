# Pre-Hackathon Setup Prompt: NL Data Pipeline Builder
# Feed this to Claude Code BEFORE the event (Thursday Feb 26 or earlier)

## INSTRUCTIONS

You are setting up a GitHub repository for a hackathon project. You are ONLY doing scaffolding and data preparation. Do NOT write any application code, components, API routes, utility files, prompts, or business logic. All of that will be written during the hackathon.

---

## STEP 1: CREATE THE NEXT.JS PROJECT

```bash
npx create-next-app@latest nl-pipeline-builder --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
cd nl-pipeline-builder
```

Install dependencies:

```bash
npm install openai ai reactflow @reactflow/core @reactflow/controls @reactflow/background @monaco-editor/react react-markdown
npm install -D @types/node
```

Dependency purposes (for reference only — do not build anything yet):
- `openai`: OpenAI SDK for GPT-4 function calling and chat
- `ai`: Vercel AI SDK for streaming responses
- `reactflow` + `@reactflow/core` + `@reactflow/controls` + `@reactflow/background`: Visual node-based pipeline diagrams
- `@monaco-editor/react`: VS Code's editor component for syntax-highlighted code display
- `react-markdown`: Render markdown in the explanation panel

---

## STEP 2: INITIALIZE GIT AND CONNECT TO GITHUB

```bash
git init
git remote add origin https://github.com/[YOUR-TEAM]/nl-pipeline-builder.git
```

Replace `[YOUR-TEAM]` with your actual GitHub org or username. Create the repo on GitHub first if it doesn't exist.

---

## STEP 3: CREATE ENVIRONMENT VARIABLE TEMPLATE

Create `.env.local.example`:

```
# OpenAI — get your key at https://platform.openai.com/api-keys
# Needs GPT-4o access
OPENAI_API_KEY=sk-your-key-here

# AWS (optional — for live S3 browsing in demo)
AWS_ACCESS_KEY_ID=your-key-here
AWS_SECRET_ACCESS_KEY=your-secret-here
AWS_REGION=us-east-1

# Databricks (optional — for simulated deployment)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token-here
```

Verify `.env.local` is in `.gitignore` (Next.js adds this by default, but confirm).

---

## STEP 4: CREATE DATA DIRECTORY AND SAMPLE FILES

Create directory `src/data/`.

### 4a. Create `src/data/sample-sales.csv`

A realistic sample sales dataset with 50 rows. Columns:

```
order_id,order_date,customer_id,product,quantity,unit_price,total,region,sales_rep
```

Requirements:
- `order_id`: Sequential integers starting from 1001
- `order_date`: Dates in MM/DD/YYYY format (intentionally "messy" — this is a common format that needs cleaning in pipelines) spread across Jan-Feb 2026
- `customer_id`: Integers from C100 to C130 (some repeating)
- `product`: Realistic product names (mix of 8-10 products like "Enterprise License", "Pro Subscription", "Consulting Hours", "Training Package", etc.)
- `quantity`: Integers 1-20
- `unit_price`: Realistic prices ($50-$5000 range)
- `total`: quantity * unit_price
- `region`: Mix of "West", "East", "Central", "South"
- `sales_rep`: 6-8 realistic names

### 4b. Create `src/data/sample-customers.csv`

A realistic customer dataset with 30 rows. Columns:

```
customer_id,company_name,industry,account_value,city,state,signup_date,is_enterprise
```

Requirements:
- `customer_id`: C100 to C130 (must overlap with sales data for join demos)
- `company_name`: Realistic company names
- `industry`: Mix of "Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Education"
- `account_value`: Range from $5,000 to $500,000
- `city` and `state`: Realistic US cities
- `signup_date`: YYYY-MM-DD format (contrast with the sales date format to show cleaning value)
- `is_enterprise`: true/false

### 4c. Create `src/data/sample-employees.csv`

A third dataset for more complex pipeline demos. 40 rows. Columns:

```
employee_id,name,department,title,hire_date,salary,manager_id,location
```

Requirements:
- `employee_id`: E001 to E040
- `name`: Realistic names
- `department`: Mix of "Engineering", "Sales", "Marketing", "Finance", "Operations", "HR"
- `title`: Appropriate titles for each department
- `hire_date`: Dates in various formats intentionally (some MM/DD/YYYY, some YYYY-MM-DD — shows the cleaning problem)
- `salary`: Realistic ranges by department ($50K-$250K)
- `manager_id`: References to other employee_ids (some null for top-level)
- `location`: Mix of "HQ", "Remote", "East Office", "West Office"

### 4d. Create `src/data/pipeline-examples.json`

A set of 8 example natural language pipeline descriptions that users can click to try. These should showcase Databricks/AWS workflows. This is UI content, not code logic:

```json
[
  {
    "id": "example_1",
    "label": "S3 → Delta Lake ETL",
    "description": "Load the raw sales CSV from our S3 bucket, clean up the date formats, filter out test orders, deduplicate by order_id, and write to a Delta Lake table in Unity Catalog partitioned by region",
    "difficulty": "medium",
    "stepsPreview": ["Read S3 CSV", "Clean Dates", "Filter", "Deduplicate", "Write Delta"]
  },
  {
    "id": "example_2",
    "label": "Weekly Sales Report",
    "description": "Pull the sales data from S3, clean up the date formats, join with the customer dimension table in Unity Catalog, filter for enterprise accounts over $50K, and summarize revenue by region",
    "difficulty": "medium",
    "stepsPreview": ["Read CSV", "Clean Dates", "Read Unity Catalog", "Join", "Filter", "Aggregate"]
  },
  {
    "id": "example_3",
    "label": "Customer 360 View",
    "description": "Combine the customer data from Unity Catalog with sales transactions from S3, deduplicate customers, calculate lifetime value per customer, flag PII columns for masking, and write unified profiles to a Delta Lake table",
    "difficulty": "hard",
    "stepsPreview": ["Read Unity Catalog", "Read S3", "Deduplicate", "Join", "Aggregate", "Write Delta"]
  },
  {
    "id": "example_4",
    "label": "Data Quality Audit",
    "description": "Scan the sales Delta table for rows with missing values, inconsistent date formats, or duplicate order IDs, and generate a data quality report showing issues per column",
    "difficulty": "medium",
    "stepsPreview": ["Read Delta", "Validate Nulls", "Check Duplicates", "Report"]
  },
  {
    "id": "example_5",
    "label": "Incremental Delta Sync",
    "description": "Read new sales records from the S3 landing zone, merge them into the existing sales Delta table using order_id as the merge key — update existing records and insert new ones",
    "difficulty": "hard",
    "stepsPreview": ["Read S3 CSV", "Read Delta", "Merge/Upsert", "Optimize"]
  },
  {
    "id": "example_6",
    "label": "Customer Segmentation",
    "description": "Load the customer table from Unity Catalog, group customers by industry and account size into segments (small under $25K, medium $25K-$100K, large over $100K), and write segments to the analytics schema",
    "difficulty": "easy",
    "stepsPreview": ["Read Unity Catalog", "Categorize", "Aggregate", "Write Unity Catalog"]
  },
  {
    "id": "example_7",
    "label": "Cross-Source Join",
    "description": "Join employee data from the HR Delta table with sales data from S3, calculate revenue per employee by department, rank departments, and write results to a Redshift reporting table",
    "difficulty": "hard",
    "stepsPreview": ["Read Delta", "Read S3", "Join", "Aggregate", "Rank", "Write Redshift"]
  },
  {
    "id": "example_8",
    "label": "Simple Data Clean",
    "description": "Read the employee CSV, standardize all the date formats to YYYY-MM-DD, remove any rows with missing salary data, and save as a clean Delta table",
    "difficulty": "easy",
    "stepsPreview": ["Read CSV", "Clean Dates", "Filter Nulls", "Write Delta"]
  }
]
```

---

## STEP 5: CREATE README

Create `README.md`:

```markdown
# PipelineGPT — Natural Language Data Pipeline Builder

> **HackUSU 2026** · Data App Factory Track · February 27–28, 2026

## The Problem

Business teams need data pipelines — weekly reports, data cleaning, ETL workflows — but they wait weeks for data engineering to build them. The gap between "I need this data" and "a pipeline is running" is massive.

## Our Solution

A web app where you describe a data workflow in plain English, and get back:

1. **A visual pipeline diagram** showing each step (source → transforms → output)
2. **Production-ready PySpark code** that runs on Databricks
3. **Plain-English explanations** of what each step does, with warnings about potential issues

Type: "Pull sales from S3, clean the dates, join with customers, filter accounts over $50K, and email me a weekly summary."

Get: A visual pipeline, executable Spark code, and a deploy button.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Next.js 14 (App Router, TypeScript) |
| Styling | Tailwind CSS |
| AI | OpenAI GPT-4o (function calling + code generation) |
| Pipeline Viz | React Flow |
| Code Display | Monaco Editor |
| Deployment | Vercel |

## AI Architecture

Three-stage AI pipeline (not a ChatGPT wrapper):

1. **Intent Parsing** — GPT-4 function calling converts natural language → structured pipeline JSON
2. **Code Generation** — GPT-4 converts pipeline JSON → executable PySpark / Databricks notebook code
3. **Validation & Explanation** — GPT-4 reviews generated code, explains each step in plain English, flags warnings

## Getting Started

### Prerequisites
- Node.js 18+
- OpenAI API key (with GPT-4o access)

### Setup
\`\`\`bash
git clone https://github.com/[YOUR-TEAM]/nl-pipeline-builder.git
cd nl-pipeline-builder
npm install
cp .env.local.example .env.local
# Fill in your API keys in .env.local
npm run dev
\`\`\`

Open [http://localhost:3000](http://localhost:3000).

## Sample Data

The `src/data/` directory contains sample CSV datasets for demos:
- `sample-sales.csv` — 50 sales transactions
- `sample-customers.csv` — 30 customer records
- `sample-employees.csv` — 40 employee records

## Team

| Name | Role |
|---|---|
| [Member 1] | AI / Backend Lead |
| [Member 2] | Frontend / UX Lead |
| [Member 3] | Integration / DevOps + Demo |

## Tools & Disclosures

- AI coding assistants were used during development
- All application code was written during the hackathon (Feb 27–28, 2026)
- Third-party APIs: OpenAI
- Static data files (sample CSVs, example prompts) were prepared before the event

## License

MIT
```

---

## STEP 6: VERIFY AND COMMIT

1. Run `npm run build` to verify the default Next.js scaffold builds with no errors
2. Verify `.env.local` is in `.gitignore`
3. Verify all CSV files open correctly and have consistent column counts
4. Verify `pipeline-examples.json` is valid JSON

Then commit and push:

```bash
git add -A
git commit -m "chore: initial scaffold with sample data, example prompts, and README"
git push -u origin main
```

---

## STEP 7: SET UP VERCEL DEPLOYMENT

```bash
npx vercel --yes
```

Or connect the GitHub repo to Vercel via the dashboard. Verify the default Next.js page deploys. Add placeholder environment variables in Vercel's settings.

---

## STEP 8: VERIFY TEAM ACCESS

Confirm:
- [ ] All 3 team members can clone the repo
- [ ] All 3 team members can `npm install && npm run dev` successfully
- [ ] All 3 team members have their own OpenAI API key (or shared key with $20+ credit loaded)
- [ ] Vercel deployment is live

---

## WHAT YOU SHOULD HAVE WHEN DONE

```
nl-pipeline-builder/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Default Next.js page (UNTOUCHED)
│   │   ├── layout.tsx            # Default layout (UNTOUCHED)
│   │   └── globals.css           # Tailwind imports (UNTOUCHED)
│   └── data/
│       ├── sample-sales.csv      # ✅ 50 rows of sales data
│       ├── sample-customers.csv  # ✅ 30 rows of customer data
│       ├── sample-employees.csv  # ✅ 40 rows of employee data
│       └── pipeline-examples.json # ✅ 6-8 example NL prompts
├── .env.local.example            # ✅ Environment variable template
├── .gitignore                    # ✅ Includes .env.local
├── README.md                     # ✅ Project README
├── package.json                  # ✅ All dependencies installed
├── next.config.ts                # Default (UNTOUCHED)
├── tailwind.config.ts            # Default (UNTOUCHED)
└── tsconfig.json                 # Default (UNTOUCHED)
```

NO application code. NO components. NO API routes. NO utility files. NO prompts. NO schemas. Just the scaffold, data, and README.
