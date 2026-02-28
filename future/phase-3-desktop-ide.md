# Phase 3: Desktop IDE Foundation

> Tauri + React + TypeScript — a native desktop app for building data pipelines

**Depends on:** Phase 2 (REST API / SDK)

---

## Goal

Build the PipelineGPT desktop IDE — a native application using Tauri (Rust + web frontend) with a dark-themed, split-pane layout inspired by Linear and Vercel. This phase delivers the application shell, chat interface, code preview (Monaco Editor), and governance panel. The visual pipeline builder (React Flow) is Phase 4.

---

## Why Tauri

| Factor | Tauri | Electron |
|--------|-------|----------|
| Binary size | ~5 MB | ~150 MB |
| Memory usage | ~30 MB | ~100+ MB |
| Backend | Rust (native perf) | Node.js |
| Security | Strict CSP, no Node in renderer | Full Node access in renderer |
| Auto-update | Built-in | electron-updater |
| Native APIs | File system, system tray, notifications | Everything via Node |

Tauri gives us a lightweight, fast, secure desktop app. The Rust backend can also embed the Python engine directly (via PyO3) in future iterations, eliminating the need for a separate API server for local use.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Tauri Desktop App                                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐      │
│  │  React Frontend (TypeScript)                           │      │
│  │                                                        │      │
│  │  ┌──────────────┐  ┌──────────────────────────────┐   │      │
│  │  │  Chat Panel   │  │  Results Panel               │   │      │
│  │  │  (35% width)  │  │  (65% width)                 │   │      │
│  │  │              │  │                               │   │      │
│  │  │  Messages    │  │  ┌─────────────────────────┐  │   │      │
│  │  │  Input bar   │  │  │  Code Preview (Monaco)  │  │   │      │
│  │  │  Templates   │  │  └─────────────────────────┘  │   │      │
│  │  │              │  │  ┌─────────────────────────┐  │   │      │
│  │  │              │  │  │  Pipeline Diagram       │  │   │      │
│  │  │              │  │  │  (placeholder → Ph 4)   │  │   │      │
│  │  │              │  │  └─────────────────────────┘  │   │      │
│  │  │              │  │  ┌─────────────────────────┐  │   │      │
│  │  │              │  │  │  Governance Panel       │  │   │      │
│  │  │              │  │  └─────────────────────────┘  │   │      │
│  │  └──────────────┘  └──────────────────────────────┘   │      │
│  └────────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌────────────────────┐                                          │
│  │  Tauri Rust Backend │──▶ Spawns local FastAPI server          │
│  │  (native bridge)    │──▶ File system access (CSV upload)      │
│  │                     │──▶ System tray, notifications           │
│  └────────────────────┘                                          │
└──────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌───────────────┐
    │  FastAPI Server │  (Phase 2 — local or remote)
    │  + StackForge   │
    │  Engine          │
    └───────────────┘
```

---

## UI Design

### Layout

The IDE follows the PipelineGPT design spec — two-column, 35/65 split:

```
┌──────────────────────────────────────────────────────────────────┐
│  ╭─ PipelineGPT ───────────────────╮  ╭─ Role ──╮  ╭─ Conn ──╮ │
│  │  AI Pipeline IDE                │  │ Analyst │  │ Local  │ │
│  ╰─────────────────────────────────╯  ╰─────────╯  ╰────────╯ │
├────────────────────┬─────────────────────────────────────────────┤
│                    │                                             │
│  CHAT              │  RESULTS                                   │
│  ────              │  ───────                                   │
│                    │  ┌─ Code ─────────────────────────────────┐ │
│  ┌──────────────┐  │  │  # PySpark code preview               │ │
│  │ User: Show   │  │  │  df = spark.read.format("delta")...   │ │
│  │ supplier     │  │  │  [Copy] [Download .py]                │ │
│  │ defect rates │  │  └───────────────────────────────────────┘ │
│  └──────────────┘  │                                             │
│                    │  ┌─ Pipeline ─────────────────────────────┐ │
│  ┌──────────────┐  │  │  [React Flow diagram — Phase 4]       │ │
│  │ Assistant:   │  │  │  "Your pipeline will appear here"     │ │
│  │ Generated a  │  │  └───────────────────────────────────────┘ │
│  │ 4-component  │  │                                             │
│  │ pipeline...  │  │  ┌─ Governance ───────────────────────────┐ │
│  └──────────────┘  │  │  ✓ PII Detection      Passed          │ │
│                    │  │  ✓ Column Access       Passed          │ │
│  ┌──────────────┐  │  │  ✓ SQL Sanitization   Passed          │ │
│  │ User: Break  │  │  │  ✓ Export Control     Passed          │ │
│  │ that down by │  │  │                                       │ │
│  │ quarter      │  │  │  Status: ● Compliant                 │ │
│  └──────────────┘  │  └───────────────────────────────────────┘ │
│                    │                                             │
│  ┌──────────────┐  │  ┌─ Audit Trail ─────────────────────────┐ │
│  │  [input bar] │  │  │  12:34:56  governance_check  passed   │ │
│  └──────────────┘  │  │  12:34:55  sql_sanitize     passed   │ │
├────────────────────┴─────────────────────────────────────────────┤
│  Ready │ Local DuckDB │ 3 tables │ gpt-5.1                      │
└──────────────────────────────────────────────────────────────────┘
```

### Dark Theme (Linear/Vercel Aesthetic)

```css
/* Core palette */
--bg-base:     #0a0a0f;       /* slate-950 */
--bg-surface:  #111118;       /* slate-900 */
--bg-elevated: #1a1a24;       /* slate-800 */
--border:      #2a2a3a;       /* slate-700 */
--text-primary:   #f8f8fc;    /* white-ish */
--text-secondary: #8888a0;    /* slate-400 */
--text-muted:     #555568;    /* slate-500 */
--accent:         #6366f1;    /* indigo-500 */
--accent-hover:   #4f46e5;    /* indigo-600 */

/* Pipeline node colors */
--node-source:      #3b82f6;  /* blue-500 */
--node-transform:   #f59e0b;  /* amber-500 */
--node-destination: #22c55e;  /* green-500 */

/* Status colors */
--status-pass:    #22c55e;    /* green-500 */
--status-warning: #eab308;    /* yellow-500 */
--status-fail:    #ef4444;    /* red-500 */

/* Typography */
--font-ui:   'Inter', -apple-system, sans-serif;
--font-code: 'JetBrains Mono', 'Fira Code', monospace;
```

---

## Requirements

### R3.1: Application Shell

**User Story:** As a user, I want a fast, native desktop application that feels like a premium developer tool.

**Acceptance Criteria:**
- WHEN the app launches THE SYSTEM SHALL display the IDE layout within 2 seconds
- THE APP SHALL use a frameless window with custom title bar (macOS-style traffic lights on Mac, custom buttons on Windows/Linux)
- THE APP SHALL support window resizing, maximizing, and minimizing
- THE APP SHALL persist window size and position between launches
- THE APP SHALL display a status bar at the bottom showing: connection status, data source info, and model name
- THE APP SHALL support both light and dark themes (dark by default)
- THE APP SHALL have a system tray icon with quick actions (new pipeline, open recent, quit)

### R3.2: Chat Panel

**User Story:** As a business user, I want to type natural language descriptions and get pipelines back through a conversational interface.

**Acceptance Criteria:**
- WHEN the user types in the chat input and presses Enter THE SYSTEM SHALL send the message to the API and display a loading indicator
- WHEN the API responds THE SYSTEM SHALL display the assistant's response with the pipeline summary
- WHEN the user sends a follow-up message THE SYSTEM SHALL refine the existing pipeline (conversational context)
- THE CHAT SHALL display typing indicators during AI processing
- THE CHAT SHALL support Shift+Enter for newlines
- THE CHAT SHALL auto-scroll to the latest message
- WHEN the chat is empty THE SYSTEM SHALL show template cards and example prompts
- WHEN a template is clicked THE SYSTEM SHALL auto-send the template's default prompt

### R3.3: Code Preview Panel

**User Story:** As a data engineer, I want to see the generated PySpark code in a proper code editor, so I can review and copy it.

**Acceptance Criteria:**
- WHEN a pipeline is generated THE SYSTEM SHALL display the PySpark code in a Monaco Editor instance
- THE EDITOR SHALL use `vs-dark` theme with Python language mode
- THE EDITOR SHALL be read-only by default with a toggle to enable editing
- WHEN "Copy Code" is clicked THE SYSTEM SHALL copy to clipboard and show "Copied!" feedback
- WHEN "Download .py" is clicked THE SYSTEM SHALL save the code as a Python file via Tauri's save dialog
- THE EDITOR SHALL support code folding, minimap, and bracket matching
- WHEN no pipeline exists THE SYSTEM SHALL show a placeholder: "Generate a pipeline to see the code"

### R3.4: Governance Panel

**User Story:** As an IT admin, I want to see governance check results for every pipeline, so I can verify compliance at a glance.

**Acceptance Criteria:**
- WHEN a pipeline is generated THE SYSTEM SHALL display governance results in the governance panel
- EACH CHECK SHALL show: rule name, status (✓/⚠/✗), and details
- WHEN all checks pass THE SYSTEM SHALL show a green "Compliant" badge
- WHEN any checks fail THE SYSTEM SHALL show a red "Non-Compliant" badge with failed checks highlighted
- THE PANEL SHALL include an expandable audit trail showing timestamped entries
- WHEN the role changes THE SYSTEM SHALL re-run governance checks and update the panel

### R3.5: Role Switcher

**User Story:** As a demo user, I want to switch between Admin, Analyst, and Viewer roles to see how governance changes.

**Acceptance Criteria:**
- THE HEADER SHALL include a role selector dropdown (Admin / Analyst / Viewer)
- WHEN the role changes THE SYSTEM SHALL re-run governance checks on the current pipeline
- WHEN the role changes THE SYSTEM SHALL update the code preview (redact restricted columns for lower roles)
- THE CURRENT ROLE SHALL be persisted between sessions

### R3.6: Data Source Connection

**User Story:** As a user, I want to connect to local data files from the desktop app.

**Acceptance Criteria:**
- THE APP SHALL support drag-and-drop CSV files onto the window to load them
- WHEN a CSV is dropped THE SYSTEM SHALL upload it to the local API server and register it as a table
- THE SIDEBAR SHALL show connected data sources with table names, row counts, and column counts
- THE APP SHALL support connecting to a local DuckDB file via a file picker dialog
- CONNECTION STATE SHALL persist between app launches

### R3.7: Local Engine Mode

**User Story:** As a developer, I want the desktop app to work without a remote server, using a local engine instance.

**Acceptance Criteria:**
- WHEN the app launches THE SYSTEM SHALL start a local FastAPI server in the background (bundled Python runtime)
- WHEN the local server is ready THE SYSTEM SHALL connect automatically
- THE USER SHALL also be able to connect to a remote API server (for team deployments)
- WHEN the app closes THE SYSTEM SHALL gracefully shut down the local server
- THE STATUS BAR SHALL show "Local" or "Remote: [url]" to indicate connection mode

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Shell | Tauri 2.x (Rust) |
| Frontend | React 18 + TypeScript |
| Styling | Tailwind CSS |
| Code Editor | Monaco Editor (@monaco-editor/react) |
| State Management | Zustand (lightweight, no boilerplate) |
| HTTP Client | Axios or fetch + TanStack Query |
| Icons | Lucide React |
| Fonts | Inter (UI), JetBrains Mono (code) |
| Build | Vite |

---

## File Structure

```
desktop/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs              # Tauri entry point
│   │   ├── commands.rs          # Rust → JS bridge commands
│   │   └── server.rs            # Local Python server management
│   ├── Cargo.toml
│   └── tauri.conf.json          # Window config, permissions, bundling
├── src/
│   ├── App.tsx                  # Root layout (split-pane)
│   ├── main.tsx                 # React entry point
│   ├── components/
│   │   ├── ChatPanel.tsx        # Chat interface
│   │   ├── CodePreview.tsx      # Monaco Editor wrapper
│   │   ├── GovernancePanel.tsx  # Governance checks + audit trail
│   │   ├── RoleSwitcher.tsx     # Role dropdown
│   │   ├── StatusBar.tsx        # Bottom status bar
│   │   ├── TitleBar.tsx         # Custom title bar
│   │   ├── DataSources.tsx      # Sidebar data source list
│   │   └── TemplateCards.tsx    # Empty state templates
│   ├── stores/
│   │   ├── pipelineStore.ts     # Zustand store for pipeline state
│   │   ├── chatStore.ts         # Chat messages state
│   │   └── configStore.ts       # App configuration state
│   ├── api/
│   │   ├── client.ts            # HTTP/WebSocket client
│   │   └── types.ts             # API response types
│   ├── styles/
│   │   └── globals.css          # Tailwind + custom dark theme
│   └── lib/
│       ├── theme.ts             # Theme configuration
│       └── utils.ts             # Utility functions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── vite.config.ts
```

---

## Distribution

| Platform | Format | Auto-Update |
|----------|--------|-------------|
| macOS | `.dmg` (universal binary: Intel + Apple Silicon) | Tauri built-in updater |
| Windows | `.msi` installer + `.exe` portable | Tauri built-in updater |
| Linux | `.AppImage` + `.deb` | Tauri built-in updater |

---

## Success Criteria

- [ ] App launches in < 2 seconds on macOS, Windows, and Linux
- [ ] Chat panel sends messages and displays AI responses
- [ ] Monaco Editor renders PySpark code with syntax highlighting
- [ ] Governance panel shows check results with status indicators
- [ ] CSV drag-and-drop works and registers tables
- [ ] Local engine mode starts and connects automatically
- [ ] App binary size < 15 MB (excluding bundled Python)
- [ ] Dark theme matches the Linear/Vercel design language
