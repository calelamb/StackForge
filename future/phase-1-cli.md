# Phase 1: CLI Tool

> `stackforge build` — Generate data pipelines from the command line

**Depends on:** Phase 0 (Engine Extraction)

---

## Goal

Ship a production CLI tool that lets developers and data engineers generate, validate, and audit data pipelines from their terminal. The CLI wraps the `stackforge` Python package and integrates into CI/CD workflows, shell scripts, and developer toolchains.

---

## Commands

### Core Commands

```bash
# Generate a pipeline from natural language
stackforge build "Show supplier defect rates by region, highlight above 5%"

# Generate with options
stackforge build "Customer 360 dashboard" \
  --data supply_chain.csv \
  --role analyst \
  --output dashboard.json \
  --format json

# Iterative refinement (reads previous output)
stackforge refine dashboard.json "Break that down by quarter and add cost trends"

# Validate governance without executing
stackforge validate dashboard.json --role viewer

# Run governance audit on a pipeline definition
stackforge audit dashboard.json --verbose

# Execute and export results
stackforge exec dashboard.json --export csv --output results/
```

### Data Commands

```bash
# Connect to a data source
stackforge connect duckdb --path warehouse.duckdb
stackforge connect csv --file data.csv --table sales

# List available tables and schemas
stackforge tables
stackforge schema supply_chain

# Inspect date ranges (for smart filtering)
stackforge inspect supply_chain --dates
```

### Config Commands

```bash
# Initialize a project config
stackforge init

# Set configuration
stackforge config set openai_key sk-...
stackforge config set default_role analyst
stackforge config set model gpt-5.1

# Show current config
stackforge config show
```

### Template Commands

```bash
# List available templates
stackforge templates

# Use a template
stackforge build --template supplier_performance

# Create a custom template from an existing pipeline
stackforge template save dashboard.json --name "My Dashboard Template"
```

---

## Requirements

### R1.1: Core Build Command

**User Story:** As a data engineer, I want to generate a pipeline by typing a natural language description in my terminal, so I can create dashboards without opening a browser.

**Acceptance Criteria:**
- WHEN the user runs `stackforge build "description"` THE SYSTEM SHALL call the engine's intent parser, governance checks, query execution, and narration
- WHEN generation succeeds THE SYSTEM SHALL print a summary to stdout: pipeline name, component count, governance status, and narration
- WHEN `--output` is specified THE SYSTEM SHALL write the full result to the specified file (JSON or YAML)
- WHEN `--format` is specified THE SYSTEM SHALL output in that format (json, yaml, table, minimal)
- WHEN `--dry-run` is specified THE SYSTEM SHALL run intent parsing and governance checks but NOT execute queries
- WHEN `--role` is specified THE SYSTEM SHALL use that role for governance checks (default: from config)
- WHEN generation fails THE SYSTEM SHALL print the error message to stderr and exit with code 1

### R1.2: Interactive Mode

**User Story:** As a data engineer, I want an interactive REPL where I can iteratively build pipelines through conversation, just like the Streamlit chat.

**Acceptance Criteria:**
- WHEN the user runs `stackforge interactive` THE SYSTEM SHALL start a REPL session
- WHEN the user types a message THE SYSTEM SHALL generate/refine the current pipeline
- WHEN the user types `/export [filename]` THE SYSTEM SHALL save the current pipeline
- WHEN the user types `/role [admin|analyst|viewer]` THE SYSTEM SHALL switch roles and re-run governance
- WHEN the user types `/audit` THE SYSTEM SHALL display the session's audit trail
- WHEN the user types `/sql` THE SYSTEM SHALL display the generated SQL queries
- WHEN the user types `/quit` THE SYSTEM SHALL exit the REPL
- THE REPL SHALL use Rich library for styled output (syntax highlighting, tables, panels)

### R1.3: Terminal Output Formatting

**User Story:** As a developer, I want beautiful terminal output that makes the generated pipeline easy to read and understand.

**Acceptance Criteria:**
- THE CLI SHALL use Rich library for all output formatting
- WHEN displaying a pipeline THE SYSTEM SHALL show a styled tree view of components
- WHEN displaying governance results THE SYSTEM SHALL use green ✓ / yellow ⚠ / red ✗ status indicators
- WHEN displaying SQL queries THE SYSTEM SHALL use syntax highlighting
- WHEN `--quiet` is specified THE SYSTEM SHALL output only the essential result (JSON) with no decoration
- WHEN stdout is not a TTY (piped) THE SYSTEM SHALL automatically switch to `--quiet` mode

```
╭─ StackForge ────────────────────────────────────╮
│                                                  │
│  Pipeline: supplier_defect_analysis              │
│  Components: 4                                   │
│  Governance: ✓ Passed (analyst)                  │
│                                                  │
│  ┌─ bar_chart ──────────────────────────────┐    │
│  │  Supplier Defect Rates by Region         │    │
│  │  Query: SELECT region, supplier, ...     │    │
│  │  Rows: 24                                │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌─ kpi_card ───────────────────────────────┐    │
│  │  Average Defect Rate: 3.2%               │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌─ line_chart ─────────────────────────────┐    │
│  │  Defect Trend Over Time                  │    │
│  │  Query: SELECT order_date, ...           │    │
│  │  Rows: 12                                │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  Narration: The data reveals that the East       │
│  region has the highest average defect rate at    │
│  4.8%, driven primarily by Supplier X...         │
│                                                  │
╰──────────────────────────────────────────────────╯
```

### R1.4: Pipeline Export Formats

**User Story:** As a data engineer, I want to export pipelines in multiple formats, so I can integrate with different tools and workflows.

**Acceptance Criteria:**
- WHEN `--format json` is specified THE SYSTEM SHALL output the full pipeline definition as JSON
- WHEN `--format yaml` is specified THE SYSTEM SHALL output as YAML
- WHEN `--export csv` is specified THE SYSTEM SHALL write component result data to CSV files (one per component)
- WHEN `--export pdf` is specified THE SYSTEM SHALL generate a PDF report with component summaries and governance status
- WHEN exporting THE SYSTEM SHALL respect role-based export permissions (viewers cannot export)

### R1.5: CI/CD Integration

**User Story:** As a DevOps engineer, I want to run governance checks in my CI pipeline, so I can block non-compliant pipelines before deployment.

**Acceptance Criteria:**
- WHEN `stackforge validate` passes THE SYSTEM SHALL exit with code 0
- WHEN `stackforge validate` fails THE SYSTEM SHALL exit with code 1 and print failures to stderr
- WHEN `--junit` is specified THE SYSTEM SHALL output governance results in JUnit XML format
- WHEN `--json` is specified THE SYSTEM SHALL output raw governance check results as JSON
- THE CLI SHALL support `STACKFORGE_API_KEY` environment variable for CI environments
- THE CLI SHALL support `--config` flag to specify a config file path

### R1.6: Installable via pip/pipx

**User Story:** As a developer, I want to install the CLI with a single command.

**Acceptance Criteria:**
- WHEN the user runs `pip install stackforge` THE SYSTEM SHALL install the CLI as a console script
- WHEN the user runs `pipx install stackforge` THE SYSTEM SHALL install in an isolated environment
- THE CLI SHALL register the `stackforge` command via `pyproject.toml` entry points
- THE CLI SHALL work on macOS, Linux, and Windows (WSL)
- THE CLI SHALL display version info via `stackforge --version`

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| CLI Framework | Click or Typer |
| Terminal UI | Rich (tables, panels, syntax highlighting, progress bars) |
| Config | TOML (`.stackforge.toml`) |
| Packaging | PyPI via `pyproject.toml` console_scripts entry point |

---

## Configuration File

```toml
# .stackforge.toml
[engine]
openai_key = "sk-..."          # or use STACKFORGE_OPENAI_KEY env var
model = "gpt-5.1"
default_role = "analyst"

[data]
type = "duckdb"
path = ":memory:"
auto_load = ["data/*.csv"]     # Auto-load CSVs on startup

[governance]
audit_log = "audit.jsonl"      # Persistent audit trail
strict_mode = false            # Fail on warnings (for CI)

[output]
format = "table"               # Default output format
color = true
```

---

## Success Criteria

- [ ] `pip install stackforge && stackforge build "hello"` works end-to-end
- [ ] `stackforge validate` returns proper exit codes for CI
- [ ] Interactive REPL supports conversational refinement
- [ ] All output respects `--quiet` and pipe detection
- [ ] Config file + env vars + CLI flags all work with proper precedence
- [ ] Help text (`stackforge --help`) is comprehensive and well-organized
