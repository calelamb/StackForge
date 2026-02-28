# Phase 6: Enterprise Features

> SSO, team workspaces, versioning, and scheduled pipelines

**Depends on:** Phase 3+ (Desktop IDE), Phase 5 (Cloud Integration)

---

## Goal

Make PipelineGPT production-ready for enterprise teams. Add real authentication (SSO/OAuth), team workspaces with shared pipelines, git-style pipeline versioning, scheduled execution, and admin controls. This phase transforms PipelineGPT from a single-user tool into a team platform.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  PipelineGPT Platform                                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  Auth Layer                                          │       │
│  │  ┌───────────┐  ┌───────────┐  ┌─────────────────┐  │       │
│  │  │ OAuth 2.0 │  │ SAML SSO  │  │ API Key Auth    │  │       │
│  │  │ (Google,  │  │ (Okta,    │  │ (CI/CD,         │  │       │
│  │  │  GitHub)  │  │  Azure AD)│  │  integrations)  │  │       │
│  │  └───────────┘  └───────────┘  └─────────────────┘  │       │
│  └──────────────────────────┬───────────────────────────┘       │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────┐       │
│  │  Team & Workspace Layer                              │       │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  │       │
│  │  │ Workspaces │  │ Team Members │  │ Permissions  │  │       │
│  │  │ (org-level │  │ (invite,     │  │ (RBAC +     │  │       │
│  │  │  isolation)│  │  roles)      │  │  workspace) │  │       │
│  │  └────────────┘  └──────────────┘  └─────────────┘  │       │
│  └──────────────────────────┬───────────────────────────┘       │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────┐       │
│  │  Pipeline Management Layer                           │       │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  │       │
│  │  │ Versioning │  │ Scheduling   │  │ Monitoring  │  │       │
│  │  │ (git-style │  │ (cron,       │  │ (run logs,  │  │       │
│  │  │  history)  │  │  triggers)   │  │  alerts)    │  │       │
│  │  └────────────┘  └──────────────┘  └─────────────┘  │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  PostgreSQL (metadata, users, teams, versions, runs) │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Requirements

### R6.1: Authentication (SSO / OAuth)

**User Story:** As an enterprise admin, I want team members to log in with their corporate SSO, so I don't need to manage separate credentials.

**Acceptance Criteria:**
- THE SYSTEM SHALL support OAuth 2.0 login (Google, GitHub, Microsoft)
- THE SYSTEM SHALL support SAML 2.0 SSO (Okta, Azure AD, OneLogin)
- WHEN a user logs in for the first time THE SYSTEM SHALL create their account with a default role (viewer)
- WHEN an admin configures SSO THE SYSTEM SHALL map IdP groups to PipelineGPT roles automatically
- THE DESKTOP APP SHALL open the system browser for SSO login and receive the token via deep link (`pipelinegpt://auth/callback`)
- THE SYSTEM SHALL issue JWT tokens with configurable expiration (default: 24 hours)
- THE SYSTEM SHALL support token refresh without re-login

**Login flow (desktop app):**
```
1. User clicks "Sign In" in the IDE
2. System browser opens: https://auth.pipelinegpt.dev/login?provider=okta
3. User authenticates with Okta
4. Redirect to: pipelinegpt://auth/callback?token=jwt_...
5. Tauri app captures the deep link and stores the JWT
6. IDE shows authenticated state with user name and role
```

### R6.2: Team Workspaces

**User Story:** As a team lead, I want a shared workspace where my team can collaborate on pipelines, so we avoid duplicating work and share best practices.

**Acceptance Criteria:**
- THE SYSTEM SHALL support multiple workspaces (one per team/org)
- WHEN a workspace is created THE SYSTEM SHALL provide isolated storage for pipelines, templates, connections, and audit logs
- WHEN a user is invited to a workspace THE SYSTEM SHALL assign them a role (admin, analyst, viewer)
- WHEN a pipeline is created THE SYSTEM SHALL save it to the active workspace
- WORKSPACE ADMINS SHALL be able to:
  - Invite/remove members
  - Assign roles
  - Configure governance policies
  - Manage connections
  - View team audit trail

**Workspace structure:**
```
Workspace: "Data Engineering — ACME Corp"
├── Members
│   ├── Cale (Admin)
│   ├── Clayton (Analyst)
│   └── Sarah (Viewer)
├── Pipelines
│   ├── customer_360_pipeline (v3, deployed)
│   ├── daily_sales_etl (v7, scheduled)
│   └── quality_audit (v1, draft)
├── Templates
│   ├── Standard ETL (team template)
│   └── Monthly Report (team template)
├── Connections
│   ├── Prod Databricks
│   ├── Dev Databricks
│   └── Data Lake S3
└── Audit Trail
    └── [all team activity]
```

### R6.3: Pipeline Versioning

**User Story:** As a data engineer, I want to see the history of changes to a pipeline, so I can understand what changed, who changed it, and roll back if needed.

**Acceptance Criteria:**
- WHEN a pipeline is saved THE SYSTEM SHALL create a new version with a sequential number
- EACH VERSION SHALL record: version number, author, timestamp, change summary (auto-generated), and full pipeline definition
- WHEN the user views version history THE SYSTEM SHALL show a timeline of changes with diffs
- WHEN the user selects a version THE SYSTEM SHALL show a side-by-side comparison (graph diff + code diff)
- WHEN the user clicks "Restore" on a version THE SYSTEM SHALL create a new version from the selected one (never destructive)
- THE SYSTEM SHALL support tagging versions (e.g., "v2.1-production", "pre-migration")
- THE SYSTEM SHALL support branching (create a variant pipeline from any version)

**Version diff view:**
```
┌─ Version History: customer_360_pipeline ────────────────────┐
│                                                              │
│  v5 ● Current   Cale, 2 hours ago                           │
│     │  "Added deduplication before join"                     │
│     │  + 1 node (deduplicate), modified join step            │
│  v4 ●           Clayton, yesterday                          │
│     │  "Switched to Delta merge for upserts"                │
│     │  Modified: write step (overwrite → merge)              │
│  v3 ● 🏷 production   Cale, 3 days ago                      │
│     │  "Added null handling for phone column"                │
│     │  + 1 node (fill_nulls)                                │
│  v2 ●           Clayton, 1 week ago                         │
│     │  "Expanded to include order history join"              │
│     │  + 2 nodes (read_orders, join)                         │
│  v1 ●           Cale, 1 week ago                            │
│       "Initial pipeline — read customers, write to Delta"    │
│                                                              │
│  [Compare v3 ↔ v5]  [Restore v3]  [Branch from v3]          │
└──────────────────────────────────────────────────────────────┘
```

### R6.4: Scheduled Pipeline Execution

**User Story:** As a data engineer, I want to schedule my pipelines to run automatically, so I don't need to trigger them manually every day.

**Acceptance Criteria:**
- WHEN the user configures a schedule THE SYSTEM SHALL create a cron-based job
- THE SYSTEM SHALL support: hourly, daily, weekly, monthly, and custom cron expressions
- WHEN a scheduled run executes THE SYSTEM SHALL:
  1. Load the latest pipeline version
  2. Run governance checks (block if non-compliant)
  3. Execute the pipeline against the configured data source
  4. Record the run result (success/failure, duration, rows processed)
  5. Send notifications on failure
- THE SYSTEM SHALL provide a "Runs" dashboard showing execution history with status, duration, and logs
- THE SYSTEM SHALL support manual "Run Now" triggers
- SCHEDULED RUNS SHALL use the deployment target (Databricks job if configured, local execution otherwise)

**Schedule configuration:**
```
Pipeline: daily_sales_etl
Schedule: Daily at 8:00 AM UTC
├── Last Run:  ✓ 2026-02-28 08:00:12 (43s, 12,450 rows)
├── Next Run:  2026-03-01 08:00:00
├── Status:    Active
├── Target:    Databricks Job #12345
└── Alerts:    team@company.com (on failure)
```

### R6.5: Monitoring & Alerting

**User Story:** As an admin, I want to monitor pipeline health and get alerts when things fail, so I can respond quickly to data issues.

**Acceptance Criteria:**
- THE SYSTEM SHALL provide a monitoring dashboard showing:
  - Active pipelines with health status (green/yellow/red)
  - Recent runs with success/failure rates
  - Average execution time trends
  - Data freshness (time since last successful run)
- WHEN a pipeline run fails THE SYSTEM SHALL send alerts via:
  - Email
  - Slack webhook
  - PagerDuty integration (optional)
- THE SYSTEM SHALL support alert rules (e.g., "alert if execution time > 2x average")
- THE SYSTEM SHALL retain run history for 90 days (configurable)

### R6.6: Admin Dashboard

**User Story:** As an admin, I want a centralized view of team activity, governance compliance, and usage, so I can manage the platform effectively.

**Acceptance Criteria:**
- THE ADMIN DASHBOARD SHALL show:
  - Team members and their roles
  - Pipeline count by status (draft, deployed, scheduled)
  - Governance compliance rate (% of pipelines passing all checks)
  - Usage metrics (builds per day, API calls, model tokens used)
  - Audit trail with filtering (by user, action, date, status)
  - Cost tracking (OpenAI API spend, Databricks compute)
- ONLY USERS WITH ADMIN ROLE SHALL access the admin dashboard
- THE DASHBOARD SHALL support date range filtering for all metrics

### R6.7: Custom Governance Policies

**User Story:** As an admin, I want to define custom governance rules specific to my organization, so the platform enforces our data policies.

**Acceptance Criteria:**
- THE SYSTEM SHALL provide a policy editor where admins can:
  - Define custom PII patterns (regex)
  - Configure column sensitivity labels per table
  - Set role-based access rules per catalog/schema/table
  - Define custom SQL blocklists
  - Configure max query complexity per role
  - Set data retention policies
- WHEN a custom policy is saved THE SYSTEM SHALL apply it to all future governance checks
- WHEN a policy is changed THE SYSTEM SHALL log the change in the audit trail
- THE SYSTEM SHALL support policy templates (HIPAA, SOC 2, GDPR basics)

### R6.8: Pipeline Sharing & Collaboration

**User Story:** As a team member, I want to share pipelines with colleagues and collaborate on refinements.

**Acceptance Criteria:**
- WHEN a user shares a pipeline THE SYSTEM SHALL generate a shareable link within the workspace
- SHARED PIPELINES SHALL respect the viewer's role (e.g., viewers see redacted PII columns)
- THE SYSTEM SHALL support comments on pipeline versions (review workflow)
- THE SYSTEM SHALL support "fork" — create a personal copy of a shared pipeline
- THE SYSTEM SHALL show who is currently viewing/editing a pipeline (presence indicators)

---

## Data Model

```sql
-- Core entities for enterprise features
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES workspaces(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'analyst', 'viewer')),
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE pipelines (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    current_version INTEGER DEFAULT 1,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pipeline_versions (
    id UUID PRIMARY KEY,
    pipeline_id UUID REFERENCES pipelines(id),
    version INTEGER NOT NULL,
    definition JSONB NOT NULL,
    generated_code TEXT,
    governance_result JSONB,
    change_summary TEXT,
    author_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    tag VARCHAR(100),
    UNIQUE (pipeline_id, version)
);

CREATE TABLE pipeline_runs (
    id UUID PRIMARY KEY,
    pipeline_id UUID REFERENCES pipelines(id),
    version INTEGER NOT NULL,
    status VARCHAR(20) CHECK (status IN ('running', 'success', 'failed', 'cancelled')),
    trigger VARCHAR(20) CHECK (trigger IN ('manual', 'scheduled', 'api')),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    rows_processed INTEGER,
    error_message TEXT,
    run_by UUID REFERENCES users(id)
);

CREATE TABLE schedules (
    id UUID PRIMARY KEY,
    pipeline_id UUID REFERENCES pipelines(id) UNIQUE,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    next_run_at TIMESTAMP,
    last_run_at TIMESTAMP,
    deployment_target JSONB
);

CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## Deployment Topology

```
┌─────────────────────────────────────────────────────────┐
│  Cloud Deployment (AWS / Azure / GCP)                    │
│                                                          │
│  ┌────────────────┐  ┌────────────────┐                 │
│  │  Load Balancer  │  │  CDN (desktop  │                 │
│  │  (HTTPS)        │  │  app updates)  │                 │
│  └───────┬────────┘  └────────────────┘                 │
│          │                                               │
│  ┌───────▼────────┐                                     │
│  │  FastAPI Server │  ← Autoscaling group               │
│  │  (Docker / ECS) │                                     │
│  └───────┬────────┘                                     │
│          │                                               │
│  ┌───────▼────────┐  ┌────────────────┐                 │
│  │  PostgreSQL     │  │  Redis          │                │
│  │  (RDS)          │  │  (sessions,     │                │
│  │                 │  │   rate limits)  │                │
│  └─────────────────┘  └────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

---

## Success Criteria

- [ ] SSO login works end-to-end (OAuth + SAML)
- [ ] Team workspaces provide isolation for pipelines and connections
- [ ] Pipeline versioning tracks changes with author, timestamp, and diffs
- [ ] Scheduled pipelines execute on time with success/failure tracking
- [ ] Monitoring dashboard shows pipeline health and run history
- [ ] Admin dashboard shows team activity and governance compliance
- [ ] Custom governance policies are editable and enforced
- [ ] Pipeline sharing respects role-based access
- [ ] All enterprise actions are logged in the audit trail
- [ ] System handles 50+ concurrent users per workspace
