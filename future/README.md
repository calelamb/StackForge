# StackForge → PipelineGPT: Production Roadmap

> From hackathon prototype to production-grade AI pipeline IDE

---

## Vision

StackForge proved the concept at HackUSU 2026: describe data in plain English, get a live interactive dashboard with enterprise governance. **PipelineGPT** is the unconstrained vision — a desktop IDE and CLI tool where teams build, visualize, and deploy full data pipelines through conversation.

The production build transforms StackForge's Streamlit-based dashboard generator into a **Tauri desktop application** with React Flow visual pipeline diagrams, Monaco Editor for PySpark code preview, real Databricks/AWS deployment, and a standalone CLI for CI/CD integration.

---

## Architecture Evolution

```
HACKATHON (StackForge)              PRODUCTION (PipelineGPT)
─────────────────────               ─────────────────────────
Streamlit UI                   →    Tauri + React + TypeScript
DuckDB in-memory               →    Databricks SQL / Snowflake / Postgres
Plotly charts                  →    React Flow DAGs + Monaco Editor
Simple role toggle             →    SSO + real RBAC + team workspaces
CSV upload                     →    Unity Catalog + S3 + Delta Lake
Session state                  →    Persistent DB + version control
pip install                    →    CLI (`stackforge build`) + desktop app
```

---

## Phase Overview

| Phase | Name | Description | Key Deliverables |
|-------|------|-------------|-----------------|
| **0** | Engine Extraction | Decouple AI engine from Streamlit into standalone Python package | `stackforge` PyPI package, clean API surface |
| **1** | CLI Tool | Command-line interface for pipeline generation and governance | `stackforge build`, `stackforge validate`, `stackforge audit` |
| **2** | REST API / SDK | HTTP API exposing the engine for integrations | FastAPI server, Python SDK, WebSocket streaming |
| **3** | Desktop IDE | Tauri + React + TypeScript shell with Monaco Editor | Dark-theme IDE, chat panel, code preview |
| **4** | Visual Pipeline Builder | React Flow DAG editor with drag-and-drop | Interactive node graph, live preview, step inspector |
| **5** | Databricks/AWS Integration | Real cloud connectors and deployment | Unity Catalog, S3, Delta Lake, job scheduling |
| **6** | Enterprise Features | Team collaboration, versioning, and security | SSO, workspaces, git-style versioning, scheduled pipelines |

---

## Design Language

PipelineGPT follows the **Linear/Vercel aesthetic** — dark theme, clean typography, purposeful animation:

- **Background:** `slate-950` base, `slate-900` cards, `slate-800` inputs
- **Accent:** `indigo-500` primary, contextual colors for pipeline node types
- **Typography:** Inter for UI, JetBrains Mono for code
- **Pipeline nodes:** Blue (source), Amber (transform), Green (destination)
- **Layout:** 35% chat panel / 65% results panel (split-pane, resizable)

---

## Tech Stack (Production)

| Layer | Technology |
|-------|-----------|
| Desktop Shell | Tauri 2.x (Rust backend, web frontend) |
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Pipeline Visualization | React Flow |
| Code Editor | Monaco Editor |
| AI Engine | Python (`stackforge` package) — OpenAI GPT-5.1 function calling |
| CLI | Click / Typer (Python) |
| API | FastAPI + WebSocket |
| Database | PostgreSQL (metadata) + SQLite (local cache) |
| Cloud Integration | Databricks SDK, AWS SDK (boto3), Snowflake connector |
| Auth | OAuth 2.0 / SAML SSO |
| Distribution | PyPI (CLI), GitHub Releases (desktop), Docker (API) |

---

## Getting Started

Each phase PRD contains detailed requirements, acceptance criteria, and architecture decisions. Read them in order — each phase builds on the previous one.

1. [Phase 0: Engine Extraction](./phase-0-engine-extraction.md)
2. [Phase 1: CLI Tool](./phase-1-cli.md)
3. [Phase 2: REST API / SDK](./phase-2-api-sdk.md)
4. [Phase 3: Desktop IDE](./phase-3-desktop-ide.md)
5. [Phase 4: Visual Pipeline Builder](./phase-4-visual-pipeline-builder.md)
6. [Phase 5: Databricks/AWS Integration](./phase-5-databricks-aws.md)
7. [Phase 6: Enterprise Features](./phase-6-enterprise.md)
