# Phase 0: Engine Extraction

> Decouple the AI engine from Streamlit into a standalone Python package

---

## Goal

Extract StackForge's five-stage AI pipeline engine into an independent Python package (`stackforge`) with zero framework dependencies. This package becomes the foundation for every subsequent phase — CLI, API, desktop IDE, and cloud integrations all consume the same core engine.

---

## Current State

The hackathon engine already has **zero Streamlit imports** in the `engine/` directory:

```
engine/
├── pipeline.py        # Orchestration (calls stages in order)
├── intent_parser.py   # GPT-5.1 function calling → app definition JSON
├── executor.py        # DuckDB SQL execution → DataFrames
├── governance.py      # PII detection, RBAC, SQL sanitization, audit trail
├── validator.py       # Result validation per component type
└── overview.py        # AI-generated plain-English narration
```

The engine is *functionally* decoupled but not *structurally* packaged — it still reads config from a monolithic `config.py`, lacks a clean public API, and has no proper Python packaging.

---

## Requirements

### R0.1: Python Package Structure

**User Story:** As a developer, I want to `pip install stackforge` and import the engine programmatically, so I can build tools on top of it.

**Acceptance Criteria:**
- WHEN a developer runs `pip install stackforge` THE SYSTEM SHALL install cleanly with all dependencies
- WHEN a developer imports `from stackforge import Engine` THE SYSTEM SHALL provide a single entry point for the full pipeline
- THE PACKAGE SHALL have zero dependencies on Streamlit, Plotly, or any UI framework
- THE PACKAGE SHALL support Python 3.10+
- THE PACKAGE SHALL be structured as a proper Python package with `pyproject.toml`

**Package structure:**
```
stackforge/
├── pyproject.toml
├── README.md
├── src/
│   └── stackforge/
│       ├── __init__.py          # Public API exports
│       ├── engine.py            # StackForgeEngine class (main orchestrator)
│       ├── intent_parser.py     # Stage 1: NL → structured definition
│       ├── code_generator.py    # Stage 2: Definition → PySpark code
│       ├── executor.py          # Stage 3: SQL execution (pluggable backends)
│       ├── validator.py         # Stage 4: Result validation
│       ├── narrator.py          # Stage 5: AI narration
│       ├── governance/
│       │   ├── __init__.py
│       │   ├── pii.py           # PII detection and redaction
│       │   ├── rbac.py          # Role-based access control
│       │   ├── sql_security.py  # SQL injection prevention
│       │   ├── audit.py         # Audit trail logging
│       │   └── policies.py      # Governance policy definitions
│       ├── connectors/
│       │   ├── __init__.py
│       │   ├── base.py          # Abstract connector interface
│       │   ├── duckdb.py        # DuckDB connector (default)
│       │   └── csv.py           # CSV file connector
│       ├── config.py            # Configuration management
│       ├── types.py             # Type definitions (dataclasses/Pydantic)
│       └── exceptions.py        # Custom exception hierarchy
└── tests/
    ├── test_engine.py
    ├── test_governance/
    ├── test_connectors/
    └── conftest.py
```

### R0.2: Clean Public API

**User Story:** As a developer, I want a simple, well-documented API to run the engine, so I don't need to understand the internal pipeline stages.

**Acceptance Criteria:**

```python
from stackforge import StackForgeEngine, Config, Role

# Initialize with config
config = Config(
    openai_api_key="sk-...",
    openai_model="gpt-5.1",
    default_role=Role.ANALYST,
)

engine = StackForgeEngine(config)

# Connect a data source
engine.connect_duckdb(":memory:")
engine.load_csv("supply_chain.csv", table_name="supply_chain")

# Generate an app from natural language
result = engine.build("Show me supplier defect rates by region")

# Access results
print(result.definition)      # Structured app definition (JSON-serializable)
print(result.components)      # List of component results with data
print(result.governance)      # Governance check results
print(result.narration)       # Plain-English summary
print(result.audit_trail)     # Audit log entries

# Iterate conversationally
result2 = engine.refine(result, "Break that down by quarter")

# Export
result.to_json("output.json")
result.to_dict()
```

### R0.3: Pluggable Connector Interface

**User Story:** As a developer, I want to swap data sources without changing any engine code, so I can point the engine at DuckDB today and Databricks tomorrow.

**Acceptance Criteria:**
- THE ENGINE SHALL define an abstract `DataConnector` interface with `execute_query(sql) → DataFrame` and `get_schema() → Dict`
- THE ENGINE SHALL ship with `DuckDBConnector` and `CSVConnector` as built-in implementations
- WHEN a connector is registered THE ENGINE SHALL use it for all query execution
- THE CONNECTOR INTERFACE SHALL support async execution for future use

```python
from stackforge.connectors.base import DataConnector

class DataConnector(ABC):
    @abstractmethod
    def execute(self, sql: str) -> pd.DataFrame: ...

    @abstractmethod
    def get_tables(self) -> List[str]: ...

    @abstractmethod
    def get_schema(self, table: str) -> Dict[str, str]: ...

    @abstractmethod
    def get_date_range(self, table: str, column: str) -> Tuple[str, str]: ...
```

### R0.4: Configuration Management

**User Story:** As a developer, I want to configure the engine through code, environment variables, or config files, so I can use it in any deployment context.

**Acceptance Criteria:**
- THE ENGINE SHALL accept configuration via `Config` dataclass, environment variables, or `.stackforge.toml` file
- WHEN environment variables are set (e.g., `STACKFORGE_OPENAI_KEY`) THE SYSTEM SHALL use them as defaults
- WHEN a config file exists in the working directory THE SYSTEM SHALL load it automatically
- Configuration priority: explicit code > environment variables > config file > defaults

### R0.5: Type System

**User Story:** As a developer, I want strongly-typed pipeline definitions, so I get IDE autocomplete and catch errors at development time.

**Acceptance Criteria:**
- ALL public types SHALL be defined as Python dataclasses or Pydantic models
- THE SYSTEM SHALL provide `PipelineDefinition`, `PipelineStep`, `GovernanceResult`, `ComponentResult`, `AuditEntry` types
- ALL types SHALL be JSON-serializable via `.to_dict()` and `.to_json()` methods
- ALL types SHALL support round-trip serialization (serialize → deserialize → identical object)

### R0.6: Governance as Independent Module

**User Story:** As an IT admin, I want to run governance checks independently of the full pipeline, so I can validate policies without executing queries.

**Acceptance Criteria:**
- THE GOVERNANCE MODULE SHALL be importable and usable independently: `from stackforge.governance import GovernanceEngine`
- WHEN called standalone THE GOVERNANCE ENGINE SHALL accept a pipeline definition and role, returning check results without executing any SQL
- THE GOVERNANCE MODULE SHALL maintain its own audit trail
- ALL existing governance tests (486+ tests) SHALL pass against the extracted module

---

## Migration Strategy

1. **Copy, don't rewrite** — the existing engine code is solid. Restructure files into the new package layout.
2. **Break `config.py` into pieces** — PII patterns → `governance/pii.py`, roles → `governance/rbac.py`, SQL rules → `governance/sql_security.py`, etc.
3. **Replace direct `config` imports** with dependency injection — the `StackForgeEngine` constructor takes a `Config` object.
4. **Add `__init__.py` exports** — define the clean public API surface.
5. **Preserve backward compatibility** — the Streamlit app (`app.py`) can import from the new package structure during transition.

---

## Success Criteria

- [ ] `pip install -e .` works from the repo root
- [ ] `from stackforge import StackForgeEngine` works in a clean Python environment
- [ ] All 486+ existing tests pass against the new package structure
- [ ] Zero Streamlit/Plotly/UI imports in the `stackforge` package
- [ ] The existing Streamlit app still works (imports from new package paths)
- [ ] Package size < 500KB (excluding test data)
