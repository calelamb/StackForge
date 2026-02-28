# Technical Architecture: StackForge — AI Data App Factory

---

## How It Works (End to End)

```
USER                           STACKFORGE ENGINE                         EXTERNAL
────                           ─────────────────                         ────────

"Show me supplier           ┌─────────────────────┐
 defect rates by            │  STAGE 1: PARSE      │
 region, highlight       ──▶│                      │──▶  OpenAI GPT-5.1
 anything above 5%"         │  Natural Language     │     (function calling)
                            │  → Structured App     │
                            │    Definition (JSON)  │
                            └──────────┬────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │  App Definition JSON  │
                            │                      │
                            │  {                   │
                            │    components: [     │
                            │      {kpi_card},     │
                            │      {bar_chart},    │
                            │      {line_chart},   │
                            │      {table}         │
                            │    ],                │
                            │    filters: [...]    │
                            │  }                   │
                            └──────────┬────────────┘
                                       │
                           ┌───────────┼───────────┐
                           ▼                       ▼
                ┌──────────────────┐   ┌──────────────────┐
                │  STAGE 2:         │   │  STAGE 3:         │
                │  EXECUTE          │   │  VALIDATE          │
                │                   │   │                    │
                │  SQL queries      │   │  Check results,    │
                │  via DuckDB       │   │  explain in plain  │
                │  → DataFrames     │   │  English, flag     │
                │                   │   │  warnings          │
                └─────────┬────────┘   └─────────┬──────────┘
                          │                      │
                          ▼                      ▼
                ┌──────────────────┐   ┌──────────────────┐
                │  RENDER           │   │  EXPLANATION       │
                │                   │   │  PANEL             │
                │  Plotly charts    │   │                    │
                │  KPI cards        │   │  "This chart shows │
                │  Data tables      │   │   defect rates by  │
                │  Interactive      │   │   supplier..."     │
                │  filters          │   │                    │
                └──────────────────┘   └──────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  STAGE 4:         │
                │  GOVERNANCE       │
                │  (deterministic)  │
                │                   │
                │  PII detection    │
                │  Access control   │
                │  Audit logging    │
                │  Role enforcement │
                └──────────────────┘
```

---

## Stage 1: Intent Parsing (Deep Dive)

### What Happens
The user's natural language input gets converted into a structured app definition. This is the most critical AI step — if parsing is wrong, the entire dashboard breaks.

### How It Works
GPT-5.1 function calling constrains the model to output a specific JSON schema describing a complete dashboard application: KPI cards, charts, tables, filters, and their associated SQL queries. The model can't hallucinate freeform text — it fills in a formal grammar.

### The Function Definition

```python
APP_INTENT_FUNCTION = {
    "name": "create_data_app",
    "parameters": {
        "type": "object",
        "properties": {
            "app_title": {"type": "string"},
            "app_description": {"type": "string"},
            "components": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"enum": ["kpi_card", "bar_chart", "line_chart",
                                          "pie_chart", "scatter_plot", "table",
                                          "metric_highlight", "area_chart"]},
                        "title": {"type": "string"},
                        "sql_query": {"type": "string"},
                        "config": {
                            "properties": {
                                "x_column": {"type": "string"},
                                "y_column": {"type": "string"},
                                "color_column": {"type": "string"},
                                "threshold": {"type": "number"},
                                "format": {"enum": ["number", "currency", "percentage"]}
                            }
                        },
                        "width": {"enum": ["full", "half", "third"]}
                    }
                }
            },
            "filters": {
                "type": "array",
                "items": {
                    "properties": {
                        "column": {"type": "string"},
                        "label": {"type": "string"},
                        "filter_type": {"enum": ["select", "multiselect",
                                                  "date_range", "number_range"]}
                    }
                }
            }
        }
    }
}
```

### Example: What GPT-5.1 Returns

**User input:**
> "Show me supplier performance — defect rates by supplier, delivery trends, and flag anyone above 5%."

**GPT-5.1 structured output:**
```json
{
  "app_title": "Supplier Performance Dashboard",
  "components": [
    {
      "id": "comp_1",
      "type": "kpi_card",
      "title": "Average Defect Rate",
      "sql_query": "SELECT ROUND(AVG(defect_rate), 2) FROM supply_chain",
      "config": {"format": "percentage"},
      "width": "third"
    },
    {
      "id": "comp_2",
      "type": "bar_chart",
      "title": "Defect Rate by Supplier",
      "sql_query": "SELECT supplier, ROUND(AVG(defect_rate), 2) as avg_defect FROM supply_chain GROUP BY supplier ORDER BY avg_defect DESC",
      "config": {"x_column": "supplier", "y_column": "avg_defect", "threshold": 5, "threshold_color": "red"},
      "width": "half"
    },
    {
      "id": "comp_3",
      "type": "line_chart",
      "title": "Monthly Delivery Trends",
      "sql_query": "SELECT strftime(order_date, '%Y-%m') as month, AVG(delivery_days) as avg_days FROM supply_chain GROUP BY month ORDER BY month",
      "config": {"x_column": "month", "y_column": "avg_days"},
      "width": "half"
    },
    {
      "id": "comp_4",
      "type": "table",
      "title": "Supplier Detail",
      "sql_query": "SELECT supplier, COUNT(*) as orders, ROUND(AVG(defect_rate),2) as avg_defect, ROUND(AVG(delivery_days),1) as avg_delivery FROM supply_chain GROUP BY supplier ORDER BY avg_defect DESC",
      "config": {"sort_by": "avg_defect", "sort_order": "desc"},
      "width": "full"
    }
  ],
  "filters": [
    {"column": "region", "label": "Region", "filter_type": "multiselect"},
    {"column": "category", "label": "Category", "filter_type": "multiselect"}
  ]
}
```

### Why This Is Technically Impressive
- **Constrained generation** — the model can only output valid app definitions, not freeform text
- **SQL generation** — the model writes DuckDB SQL queries tuned to the actual data schema
- **Layout intelligence** — the model decides which components go where and at what width
- **Conversational refinement** — follow-up prompts modify the existing app definition, not rebuild from scratch

---

## Stage 2: Execution (Deep Dive)

### What Happens
Each component's SQL query is executed against DuckDB, producing DataFrames that feed directly into Plotly visualizations.

### Why DuckDB
- **Blazing fast** — analytical queries on CSV/Parquet in milliseconds
- **Embedded** — no server, no config, runs in-process
- **SQL-native** — GPT-5.1 generates standard SQL, DuckDB executes it
- **Databricks-compatible** — same SQL patterns work in Spark SQL

### Execution Flow
```python
for component in app_definition["components"]:
    df = duckdb.execute(component["sql_query"]).fetchdf()
    # df is now a Pandas DataFrame ready for Plotly
```

Filters are applied dynamically by wrapping the original query:
```sql
SELECT * FROM (
    -- original AI-generated query
    SELECT supplier, AVG(defect_rate) as avg_defect
    FROM supply_chain GROUP BY supplier
) AS subq
WHERE region IN ('North America', 'Europe')  -- user-selected filters
```

---

## Stage 3: Validation & Explanation

### What Happens
After execution, the system reviews results and generates:
1. Plain-English explanations for each component
2. Warnings about potential issues (empty results, high cardinality charts, failed queries)
3. Overall status assessment

This is deterministic — no AI call needed. Pattern matching on query results.

---

## Stage 4: Governance (Deep Dive)

### What Happens
Every generated app gets compliance checks. This is deterministic and fast (<50ms):

1. **PII Detection** — Regex scan of all SQL queries for PII column patterns (email, phone, ssn, salary, address)
2. **Access Control** — Role-based permissions check (admin/analyst/viewer)
3. **Query Complexity** — Component count limits by role
4. **Data Quality** — Flags SELECT * patterns, empty results
5. **Export Control** — Download/export restrictions by role
6. **Audit Trail** — All actions logged with timestamps

### Role Policy Matrix

| Capability | Admin | Analyst | Viewer |
|---|---|---|---|
| View raw data | ✅ | ✅ | ❌ |
| View PII columns | ✅ | ❌ (masked) | ❌ (masked) |
| Deploy apps | ✅ | ❌ | ❌ |
| Export data | ✅ | ✅ | ❌ |
| Max components | Unlimited | 8 | 4 |
| Requires approval | No | Yes | Yes |

---

## The "Show Engine" Toggle

This is StackForge's technical differentiator. A single toggle reveals the full engine behind the dashboard:

```
┌──────────────────────────────────────────────────┐
│  [📊 Dashboard]  [🔧 Engine]        🔧 Show Engine │
├──────────────────────────────────────────────────┤
│                                                    │
│  📝 Generated SQL     │  🔀 Data Flow              │
│  ────────────────     │  ────────────              │
│  SELECT supplier,     │  supply_chain (raw)        │
│    AVG(defect_rate)   │       │                    │
│  FROM supply_chain    │  [Filters: Region, Cat.]   │
│  GROUP BY supplier    │       │                    │
│  ORDER BY avg DESC    │  ├──→ 🎯 KPI: Avg Defect  │
│                       │  ├──→ 📊 Bar: By Supplier  │
│  🛡️ Governance        │  ├──→ 📈 Line: Monthly     │
│  ────────────         │  └──→ 📋 Table: Detail     │
│  ✅ PII Detection     │                            │
│  ✅ Access Control    │  📋 Audit Log              │
│  ⚠️ Query Complexity  │  ────────────              │
│  ✅ Export Control    │  10:42:03 — App generated  │
│  ✅ Audit Trail       │  10:42:04 — Queries run    │
│                       │  10:42:05 — Gov. checks    │
└──────────────────────────────────────────────────┘
```

Business users see: clean dashboard with charts and filters.
Technical reviewers see: generated SQL, data flow, governance compliance, audit trail.
Judges see: **both**.

---

## What You Are NOT Building

| What it sounds like | What you're actually doing |
|---|---|
| "NLP model" | Using GPT-5.1 API with function calling — NOT training a model |
| "Database system" | DuckDB in-memory on CSV — NOT managing infrastructure |
| "Deployment platform" | Streamlit local/cloud — NOT Kubernetes |
| "BI tool from scratch" | AI generates Plotly dashboards — NOT building Tableau |

Your technical contribution is:
1. The **function schema design** — defining what a valid data app looks like as structured JSON
2. The **prompt engineering** — instructing GPT-5.1 to generate correct SQL and layout decisions
3. The **execution engine** — DuckDB + Plotly rendering pipeline
4. The **governance layer** — PII detection, role-based access, audit logging
5. The **transparency view** — the "Show Engine" toggle revealing internals

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Framework** | Streamlit | Matches Databricks spec examples, fast to build, native Python |
| **AI** | OpenAI GPT-5.1 (function calling) | Constrained structured outputs for app definitions |
| **Database** | DuckDB (embedded) | Blazing fast analytical SQL on CSV, zero config |
| **Visualization** | Plotly | Interactive charts (hover, zoom, click), dark theme |
| **Data** | Pandas | DataFrame manipulation, DuckDB integration |
| **Deployment** | Streamlit Community Cloud | One-click deploy, free |

---

## File Structure

```
stackforge/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Dependencies
├── config.py                       # Configuration, templates, roles
├── .env                            # API keys (gitignored)
├── data/
│   ├── supply_chain.csv            # Koch-provided dataset
│   └── sample_data_loader.py       # DuckDB data loading
├── engine/
│   ├── intent_parser.py            # GPT-5.1 function calling → app definition
│   ├── executor.py                 # Execute SQL via DuckDB
│   ├── validator.py                # Validate and explain results
│   └── governance.py               # Deterministic governance checks
├── ui/
│   ├── chat.py                     # Chat interface
│   ├── dashboard.py                # Plotly chart/table/KPI renderer
│   ├── engine_view.py              # "Show Engine" technical view
│   └── styles.py                   # Custom CSS (dark theme)
└── utils/
    └── helpers.py                  # Utility functions
```
