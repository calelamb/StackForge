# Build Plan: StackForge — Data App Factory Track (Koch / AWS / Databricks)

**Track:** Data App Factory (Koch Industries, Databricks, AWS)
**Event:** HackUSU 2026 · February 27–28, 2026
**Build window:** 19 hours (6 PM Friday → 1 PM Saturday)
**Team size:** 3

---

## The Idea: StackForge — AI-Powered Interactive Data App Factory

### One-liner
A platform where non-technical business users describe what they want to see in plain English, and the AI generates live, interactive data applications — dashboards with charts, filterable tables, and KPI cards — powered by the Supply Chain dataset from Koch.

### The Problem
Business teams constantly need data visibility — supplier performance dashboards, cost breakdowns, quality monitors, logistics tracking. Today they either wait weeks for engineering to build BI dashboards, learn SQL themselves, or stare at static spreadsheets. The gap between "I need to see this data" and "here's an interactive dashboard" is massive.

### The Solution
A conversational interface where a user types:

> "Show me supplier defect rates by region, highlight anyone above 5%, and let me filter by product category."

The system:
1. **Parses the request** using GPT-5.1 function calling → structured app definition (components, queries, layout, filters)
2. **Generates SQL queries** for each dashboard component
3. **Executes against real data** via DuckDB (embedded analytical database)
4. **Renders interactive Plotly charts**, KPI cards, and data tables
5. **Runs governance checks** — PII detection, access control, audit logging
6. **Enables refinement** — "break that down by quarter" / "add a cost column" / "show only North America"

### Why This Wins With These Judges

Koch, Databricks, and AWS judges will look for:
- **Interactive, not static** — apps that users can drill into, filter, and explore
- **Conversational AI** — back-and-forth chat that refines apps, not a one-shot form
- **Governance** — PII detection, roles, audit trails (explicitly called out as core requirement)
- **Real data** — using the Supply Chain dataset they provided
- **Factory model** — templates that produce different apps, not just one thing
- **Technical transparency** — the "Show Engine" toggle proves you understand what's happening under the hood

---

## Technical Architecture

```
┌──────────────────────────────────────────────────────┐
│                    StackForge UI                       │
│               Streamlit (Python)                      │
│                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ Chat       │  │ Dashboard  │  │ Engine View    │  │
│  │ Interface  │  │ (Plotly)   │  │ (SQL + Gov)    │  │
│  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘  │
└────────┼───────────────┼──────────────────┼───────────┘
         │               │                  │
┌────────┼───────────────┼──────────────────┼───────────┐
│        ▼               ▼                  ▼           │
│                   Engine Layer                         │
│                                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │ Intent     │  │ Executor   │  │ Governance     │   │
│  │ Parser     │  │ (DuckDB)   │  │ (Rules-based)  │   │
│  │ (GPT-5.1)  │  │            │  │                │   │
│  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘   │
└────────┼───────────────┼──────────────────┼───────────┘
         │               │                  │
         ▼               ▼                  ▼
┌──────────────────────────────────────────────────────┐
│                 External Services                     │
│                                                      │
│  ┌────────────┐  ┌────────────────────────────────┐  │
│  │ OpenAI     │  │ DuckDB (Embedded)              │  │
│  │ GPT-5.1    │  │                                │  │
│  │ (function  │  │  • Supply Chain CSV (500 rows)  │  │
│  │  calling)  │  │  • SQL analytics engine         │  │
│  │            │  │  • Millisecond query execution   │  │
│  └────────────┘  └────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## What to Build in 19 Hours

### Priority 1: Core Engine (Hours 0–6)

User types natural language → AI generates app definition → DuckDB executes queries → Plotly renders dashboard. This is the money shot.

| Task | Owner | Time |
|---|---|---|
| Project setup, DuckDB + data loading | Backend Lead | Hours 0–1 |
| Intent parser (GPT-5.1 function calling) | AI Lead | Hours 0–3 |
| SQL executor + query engine | Backend Lead | Hours 1–3 |
| Dashboard renderer (Plotly charts, KPIs, tables) | Frontend Lead | Hours 1–4 |
| Main app assembly + chat interface | Integration | Hours 3–6 |
| Wire it all together, test end-to-end | ALL | Hours 5–6 |

**Milestone (Hour 6):** User types a sentence, sees a live interactive dashboard with charts, KPIs, and a data table.

### Priority 2: Governance + Engine View (Hours 6–10)

| Task | Owner | Time |
|---|---|---|
| Governance engine (PII, access control, audit) | Backend Lead | Hours 6–8 |
| "Show Engine" view (SQL, data flow, audit log) | Frontend Lead | Hours 6–8 |
| Role toggle (admin/analyst/viewer) | Integration | Hours 6–7 |
| Governance panel in sidebar | Frontend Lead | Hours 8–9 |
| Role-based experience differences | AI Lead | Hours 8–10 |
| Template library (6 Supply Chain templates) | Integration | Hours 8–10 |

**Milestone (Hour 10):** Governance checks run on every build. Role switching changes the experience. Show Engine reveals SQL and audit trail.

### Priority 3: Conversational Polish (Hours 10–14)

| Task | Owner | Time |
|---|---|---|
| Follow-up refinement (modify existing apps via chat) | AI Lead | Hours 10–12 |
| Interactive filters in sidebar | Frontend Lead | Hours 10–12 |
| Demo mode (one-click end-to-end flow) | Integration | Hours 10–12 |
| Error handling and edge cases | ALL | Hours 12–14 |
| Loading states, transitions, UX polish | Frontend Lead | Hours 12–14 |

**Milestone (Hour 14):** Full conversational loop works — build, refine, rebuild. Demo button triggers flawless flow.

### Priority 4: Demo Prep (Hours 14–17)

| Task | Owner | Time |
|---|---|---|
| Demo script + rehearsal | ALL | Hours 14–15 |
| README, screenshots, submission | Integration | Hours 15–16 |
| Final testing on demo laptop | ALL | Hours 16–17 |

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **Framework** | Streamlit | Matches spec examples, Python-native, fast prototyping |
| **AI** | OpenAI GPT-5.1 (function calling) | Constrained structured outputs |
| **Database** | DuckDB (embedded) | Millisecond SQL on CSV, zero config |
| **Visualization** | Plotly | Interactive charts, dark theme, hover/zoom |
| **Data** | Pandas + Koch Supply Chain dataset | Real sponsor data |
| **Deployment** | Streamlit Community Cloud or local | One-click deploy |

---

## Demo Script (10 Minutes)

**[0:00–1:00] The Problem**
"Every business team needs data visibility — dashboards, reports, KPI monitors. But building them requires SQL, Python, and weeks of engineering time. What if a business user could just *describe* what they need?"

**[1:00–2:00] The Solution**
"We built StackForge — an AI-powered Data App Factory. Describe what you want to see, and StackForge generates a live, interactive data application — charts, filters, KPIs, tables — all governed with PII detection and role-based access."

**[2:00–5:00] Live Demo — Build**
1. Click "Supplier Performance Dashboard" template
2. Watch the AI parse → execute → render in real-time
3. Show interactive Plotly charts (hover over data points, zoom in)
4. Show KPI cards at the top with key metrics
5. Show filterable data table at the bottom
6. Use sidebar filters to drill down by region

**[5:00–7:00] Live Demo — Refine**
1. Type: "Break down the defect analysis by shipping mode and highlight suppliers above 5% in red"
2. Watch the dashboard update with new chart
3. Type: "Add a cost impact column to the table"
4. Dashboard evolves — demonstrating CONVERSATIONAL refinement

**[7:00–8:30] Show Engine + Governance**
1. Toggle "Show Engine" — reveal generated SQL, data flow DAG, audit log
2. Switch to Admin role — show governance panel, approval button
3. Switch to Viewer role — show restricted access, masked data
4. Show audit trail of every action

**[8:30–10:00] Technical Depth + Impact**
"Five-stage AI engine: intent parsing via function calling, SQL generation, DuckDB execution, Plotly rendering, and governance checks. The Show Engine toggle proves technical transparency — judges can see every query, every check, every decision."

"This turns a two-week BI request into a two-minute conversation. Powered by the Supply Chain dataset from Koch, running DuckDB for Databricks-class analytics, with enterprise governance baked in."

---

## Decision Framework

**Why StackForge wins the Data App Factory track:**
- Directly matches the spec's definition: "framework for enabling business users to create data applications"
- Uses the provided Supply Chain dataset (shows respect for sponsor data)
- Interactive dashboards (spec explicitly warns against static outputs)
- Conversational AI (spec explicitly warns against weak chat interfaces)
- Governance front-and-center (spec says "governance is not optional — it's core")
- Templates show the "factory" concept — one platform produces many apps
- Show Engine proves technical depth without sacrificing business user simplicity
