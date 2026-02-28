# Phase 2: REST API & Python SDK

> Expose the engine as HTTP endpoints for integrations and the desktop IDE

**Depends on:** Phase 0 (Engine Extraction)

---

## Goal

Build a FastAPI server that exposes the StackForge engine as REST endpoints with WebSocket streaming. This API serves two purposes: it's the backend for the Tauri desktop IDE (Phase 3+), and it's a standalone integration point for custom workflows, Slack bots, Jupyter notebooks, and other tools.

Ship a thin Python SDK alongside the API for programmatic access.

---

## Architecture

```
                    ┌─────────────────────┐
                    │   Tauri Desktop IDE  │ (Phase 3)
                    │   (React frontend)   │
                    └──────────┬──────────┘
                               │ HTTP / WebSocket
                    ┌──────────▼──────────┐
                    │   FastAPI Server     │
                    │   ┌───────────────┐  │
                    │   │ REST Routes   │  │  POST /api/build, /api/refine, etc.
                    │   │ WS Streaming  │  │  ws://  for real-time stage updates
                    │   │ Auth Middleware│  │  API key / JWT validation
                    │   └───────┬───────┘  │
                    │           │           │
                    │   ┌───────▼───────┐  │
                    │   │  StackForge   │  │  Python engine (Phase 0 package)
                    │   │  Engine       │  │
                    │   └───────────────┘  │
                    └──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐   ┌──────────┐    ┌──────────────┐
        │  DuckDB  │   │ Postgres │    │  Databricks  │ (Phase 5)
        │  (local) │   │ (meta)   │    │  (cloud)     │
        └──────────┘   └──────────┘    └──────────────┘
```

---

## API Endpoints

### Pipeline Generation

```
POST   /api/build              Generate a pipeline from natural language
POST   /api/refine             Refine an existing pipeline with follow-up
POST   /api/validate           Run governance checks without executing
GET    /api/pipeline/:id       Retrieve a saved pipeline
DELETE /api/pipeline/:id       Delete a pipeline
GET    /api/pipelines          List all pipelines (paginated)
```

### Data Sources

```
POST   /api/connect            Register a data source connection
GET    /api/tables             List available tables
GET    /api/schema/:table      Get table schema
POST   /api/upload             Upload a CSV file
DELETE /api/source/:id         Remove a data source
```

### Governance & Audit

```
POST   /api/governance/check   Run governance checks on a pipeline definition
GET    /api/audit              Get audit trail (paginated, filterable)
GET    /api/audit/export       Export audit trail as JSONL
```

### Templates

```
GET    /api/templates          List available templates
POST   /api/templates          Create a custom template
GET    /api/templates/:id      Get template details
```

### WebSocket (Streaming)

```
WS     /ws/build               Stream pipeline generation progress stage-by-stage
WS     /ws/refine              Stream refinement progress
```

---

## Requirements

### R2.1: Pipeline Build Endpoint

**User Story:** As a developer, I want to POST a natural language description and receive a complete pipeline result, so I can integrate pipeline generation into any application.

**Acceptance Criteria:**
- WHEN a POST request is sent to `/api/build` with `{ "prompt": "...", "role": "analyst", "data_source": "..." }` THE SYSTEM SHALL run the full five-stage pipeline and return the result
- WHEN the request succeeds THE SYSTEM SHALL return `200` with: pipeline definition, component results, governance status, narration, and audit entries
- WHEN governance checks fail THE SYSTEM SHALL return `200` with `governance.status: "blocked"` and the list of failures (not a 4xx — the request itself succeeded)
- WHEN the prompt is empty THE SYSTEM SHALL return `400`
- WHEN the API key is invalid THE SYSTEM SHALL return `401`
- WHEN the OpenAI API call fails THE SYSTEM SHALL return `502` with the upstream error

**Response shape:**
```json
{
  "id": "pipe_abc123",
  "pipeline": { "name": "...", "components": [...] },
  "governance": { "status": "passed", "checks": [...] },
  "narration": { "summary": "...", "components": [...] },
  "audit": [ { "timestamp": "...", "action": "...", "status": "..." } ],
  "metadata": { "duration_ms": 3200, "model": "gpt-5.1", "stages_completed": 5 }
}
```

### R2.2: WebSocket Streaming

**User Story:** As a frontend developer, I want real-time updates as each pipeline stage completes, so I can show a progressive loading experience in the IDE.

**Acceptance Criteria:**
- WHEN a client connects to `/ws/build` and sends a build request THE SYSTEM SHALL stream stage-by-stage progress events
- THE SYSTEM SHALL emit events for: `stage_start`, `stage_complete`, `stage_error`, `pipeline_complete`
- EACH event SHALL include: `stage` (name), `status`, `duration_ms`, and `data` (partial result for that stage)
- WHEN all stages complete THE SYSTEM SHALL send a `pipeline_complete` event with the full result
- WHEN any stage fails THE SYSTEM SHALL send a `stage_error` event and close the connection

**Event stream:**
```json
{"event": "stage_start", "stage": "intent_parsing", "timestamp": "..."}
{"event": "stage_complete", "stage": "intent_parsing", "duration_ms": 1200, "data": {"components": 4}}
{"event": "stage_start", "stage": "governance", "timestamp": "..."}
{"event": "stage_complete", "stage": "governance", "duration_ms": 12, "data": {"status": "passed", "checks": 6}}
{"event": "stage_start", "stage": "execution", "timestamp": "..."}
{"event": "stage_complete", "stage": "execution", "duration_ms": 45, "data": {"rows_processed": 500}}
{"event": "stage_start", "stage": "validation", "timestamp": "..."}
{"event": "stage_complete", "stage": "validation", "duration_ms": 8, "data": {"valid_components": 4}}
{"event": "stage_start", "stage": "narration", "timestamp": "..."}
{"event": "stage_complete", "stage": "narration", "duration_ms": 1800, "data": {"summary": "..."}}
{"event": "pipeline_complete", "data": { ... full result ... }}
```

### R2.3: Authentication & Authorization

**User Story:** As an admin, I want API access to be authenticated and role-aware, so I can control who generates pipelines and what data they can access.

**Acceptance Criteria:**
- WHEN a request lacks an API key header (`X-StackForge-Key`) THE SYSTEM SHALL return `401`
- WHEN the API key is valid THE SYSTEM SHALL resolve the associated role and pass it to the engine
- THE SYSTEM SHALL support API key authentication (for CI/CD and programmatic access)
- THE SYSTEM SHALL support JWT tokens (for the desktop IDE, issued after login)
- WHEN a role is explicitly passed in the request body THE SYSTEM SHALL use it only if the authenticated user has permission to assume that role (admins can assume any role)

### R2.4: Session Management

**User Story:** As a developer, I want pipeline context to persist across requests in a session, so I can build iteratively via the API just like in the chat interface.

**Acceptance Criteria:**
- WHEN a build request includes `session_id` THE SYSTEM SHALL maintain conversation context for that session
- WHEN a refine request is sent THE SYSTEM SHALL use the session's previous pipeline as the base
- WHEN a session is idle for 30 minutes THE SYSTEM SHALL expire it
- WHEN `/api/sessions` is called THE SYSTEM SHALL list active sessions with metadata

### R2.5: Python SDK

**User Story:** As a Python developer, I want a thin SDK that wraps the API, so I can interact with a remote StackForge server from notebooks or scripts.

**Acceptance Criteria:**

```python
from stackforge.sdk import StackForgeClient

client = StackForgeClient(
    base_url="http://localhost:8000",
    api_key="sf_...",
)

# Synchronous
result = client.build("Show supplier defect rates by region")
print(result.narration.summary)

# Streaming (async)
async for event in client.build_stream("Show supplier defect rates"):
    print(f"Stage: {event.stage} — {event.status}")

# Session-based iteration
session = client.session()
r1 = session.build("Executive summary of supply chain")
r2 = session.refine("Break that down by quarter")
r3 = session.refine("Add cost trends")
session.export("output.json")
```

- THE SDK SHALL provide both sync and async interfaces
- THE SDK SHALL handle authentication, retries, and error mapping
- THE SDK SHALL be included in the `stackforge` PyPI package (no separate install)

### R2.6: Rate Limiting & Quotas

**User Story:** As an admin, I want to control API usage to prevent abuse and manage OpenAI costs.

**Acceptance Criteria:**
- THE API SHALL support configurable rate limits per API key (default: 60 requests/minute)
- THE API SHALL return `429 Too Many Requests` when rate limits are exceeded
- THE API SHALL include `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- THE API SHALL support per-role quotas (e.g., viewers get fewer builds per day than analysts)

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| WebSocket | FastAPI WebSocket + Starlette |
| Auth | API keys + JWT (PyJWT) |
| Validation | Pydantic v2 |
| Rate Limiting | slowapi or custom middleware |
| Docs | Auto-generated OpenAPI/Swagger at `/docs` |
| Deployment | Docker, or `stackforge serve` CLI command |

---

## Running the Server

```bash
# Start the API server
stackforge serve --port 8000

# Start with specific config
stackforge serve --config production.toml --workers 4

# Docker
docker run -p 8000:8000 -e STACKFORGE_OPENAI_KEY=sk-... stackforge/api
```

---

## Success Criteria

- [ ] `POST /api/build` returns a complete pipeline result in < 15 seconds
- [ ] WebSocket streaming delivers stage-by-stage updates
- [ ] API key authentication works correctly
- [ ] Python SDK `build()` and `build_stream()` work end-to-end
- [ ] Auto-generated OpenAPI docs are complete and accurate at `/docs`
- [ ] Rate limiting returns proper `429` responses
- [ ] Docker image builds and runs successfully
