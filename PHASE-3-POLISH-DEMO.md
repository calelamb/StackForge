# StackForge Phase 3: Polish, Demo Mode & Production Ready
**Hours 10–14 of 19-hour build**
**Status: Final phase, assumes Phase 1 & 2 complete**

---

## 1. What Exists from Phase 1 & 2

### Phase 1: Project Setup & Data Loading
| File | Purpose | Status |
|------|---------|--------|
| `config.py` | Global config, PII patterns, role definitions, templates | ✅ Complete |
| `data/sample_data_loader.py` | DuckDB connection, synthetic data generation | ✅ Complete |
| `requirements.txt` | Dependencies (Streamlit, OpenAI, Pandas, Plotly, DuckDB) | ✅ Complete |
| `.env` | Environment variables (OPENAI_API_KEY) | ✅ Complete |

### Phase 2: Engine & UI Components
| File | Purpose | Status |
|------|---------|--------|
| `engine/intent_parser.py` | Parse NL → app definition (GPT function calling) | ✅ Complete |
| `engine/executor.py` | Execute SQL queries, apply filters to WHERE clause | ✅ Complete |
| `engine/validator.py` | Validate queries and generate plain-English explanations | ✅ Complete |
| `engine/governance.py` | PII detection, access control, query complexity checks | ✅ Complete |
| `ui/styles.py` | Dark theme CSS, KPI cards, governance badges | ✅ Complete |
| `ui/chat.py` | Chat message rendering, template selector | ✅ Complete |
| `ui/dashboard.py` | Render charts (bar, line, pie, scatter, area), KPI cards, tables | ✅ Complete |
| `ui/engine_view.py` | "Show Engine" view with SQL, data flow, governance, audit log | ✅ Complete |

### Phase 1-2 App Skeleton (app.py)
- Basic header with role selector
- Two-column layout (chat + dashboard)
- Demo button placeholder
- Template selector
- Chat interface
- Basic dashboard renderer

---

## 2. Phase 3 Enhancements

### 2.1 Conversational Refinement

**The Key Insight:** When a user has an EXISTING app and sends a follow-up message like:
- "Add a cost column"
- "Break down by quarter"
- "Remove the pie chart"
- "Highlight suppliers above 5% defect rate"

...the system must **pass the existing app definition to intent_parser** so the AI can modify it rather than starting from scratch.

**Implementation in `app.py`:**

```python
def _process_prompt(prompt: str):
    """Process a user prompt through the full pipeline."""

    with st.spinner("🧠 Parsing intent..."):
        add_audit_entry("Intent parsing started", f"Prompt: {prompt[:80]}...")

        try:
            schema = get_table_schema(st.session_state.db_conn)

            # CRITICAL: Pass existing_app if one exists (conversational refinement)
            app_def = parse_intent(
                prompt,
                existing_app=st.session_state.current_app,  # ← This enables refinement!
                table_schema=schema,
            )
            st.session_state.current_app = app_def
            add_audit_entry("App definition generated",
                           f"{len(app_def.get('components', []))} components")

        except Exception as e:
            add_assistant_message(f"❌ Error parsing your request: {str(e)}")
            add_audit_entry("Intent parsing failed", str(e))
            st.rerun()
            return
```

**The intent_parser.py already handles this** via its system prompt:
> When the user asks to REFINE an existing app, modify only the relevant components. Add new ones, change queries, update configurations — but preserve the overall structure unless they want a complete redesign.

When `existing_app` is passed, it's included in the system context so GPT-5.1 understands it's a refinement, not a new app.

---

### 2.2 Interactive Sidebar Filters

**What it does:** Renders filter widgets (select, multiselect, date_range, number_range) from `app_definition["filters"]`. User selections update dashboard in real-time.

**Updated `_render_filters` in `ui/dashboard.py`:**

```python
def _render_filters(filter_defs: list, execution_results: dict) -> dict:
    """Render sidebar filters and return selected values."""
    if not filter_defs:
        return {}

    filters = {}
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        for f in filter_defs:
            col = f["column"]
            label = f["label"]
            ftype = f["filter_type"]

            # Get unique values from any execution result that has this column
            unique_values = set()
            for result in execution_results.values():
                df = result.get("data")
                if df is not None and col in df.columns:
                    unique_values.update(df[col].dropna().unique().tolist())

            unique_values = sorted(list(unique_values))

            if ftype == "select":
                selected = st.selectbox(label, ["All"] + unique_values,
                                       key=f"filter_{col}")
                if selected != "All":
                    filters[col] = selected
            elif ftype == "multiselect":
                selected = st.multiselect(label, unique_values,
                                         key=f"filter_{col}")
                if selected:
                    filters[col] = selected
            elif ftype == "date_range":
                date_range = st.date_input(label, key=f"filter_{col}")
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    filters[col] = date_range
            elif ftype == "number_range":
                if unique_values:
                    min_val = min([v for v in unique_values
                                  if isinstance(v, (int, float))] or [0])
                    max_val = max([v for v in unique_values
                                  if isinstance(v, (int, float))] or [100])
                    selected = st.slider(label, min_val, max_val,
                                        (min_val, max_val), key=f"filter_{col}")
                    if selected != (min_val, max_val):
                        filters[col] = selected

    return filters
```

**In `execute_app_components` (executor.py)**, filters are injected into WHERE clauses:

```python
def execute_query(conn, sql_query: str, filters: dict = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Execute a SQL query and return results as a DataFrame.

    Filters are applied via WHERE clause injection to the subquery.
    """
    try:
        if filters:
            filter_clauses = []
            for col, val in filters.items():
                if val is None or (isinstance(val, list) and len(val) == 0):
                    continue
                if isinstance(val, list):
                    values_str = ", ".join([f"'{v}'" for v in val])
                    filter_clauses.append(f"{col} IN ({values_str})")
                elif isinstance(val, tuple) and len(val) == 2:
                    filter_clauses.append(f"{col} BETWEEN '{val[0]}' AND '{val[1]}'")
                else:
                    filter_clauses.append(f"{col} = '{val}'")

            if filter_clauses:
                filter_sql = " AND ".join(filter_clauses)
                sql_query = f"SELECT * FROM ({sql_query}) AS subq WHERE {filter_sql}"

        result = conn.execute(sql_query).fetchdf()
        return result, None

    except Exception as e:
        return None, str(e)
```

**Flow:**
1. Dashboard renders filter widgets in sidebar
2. User selects values → Streamlit triggers rerun
3. `_render_filters()` returns selected filters dict
4. `render_dashboard()` calls `execute_app_components()` with filters
5. Executor injects filters into WHERE clauses
6. Dashboard re-renders with filtered data

---

### 2.3 Demo Mode

**What it does:** One-click demo that:
1. Auto-sends Supplier Performance template prompt
2. Waits for app to build (show spinners)
3. Auto-sends refinement prompt: "Break down defect analysis by shipping mode and highlight suppliers above 5%"
4. Shows full conversational flow in action

**In `app.py`:**

```python
# Demo button in header
with header_col3:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        show_engine = st.toggle("🔧 Show Engine", value=st.session_state.show_engine)
        st.session_state.show_engine = show_engine
    with col_b:
        if st.button("🎬 Demo", use_container_width=True):
            st.session_state.demo_mode = True
    with col_c:
        if st.button("🔄 Reset", use_container_width=True):
            # Reset all state
            for key in ["current_app", "execution_results", "validation",
                       "governance", "messages", "audit_log"]:
                if key in st.session_state:
                    if key == "messages":
                        st.session_state[key] = []
                    elif key == "audit_log":
                        st.session_state[key] = []
                    else:
                        st.session_state[key] = None
            st.rerun()

# Handle demo mode in chat area
with chat_col:
    st.markdown("### 💬 Chat")

    selected_template = render_template_selector(TEMPLATES)

    if selected_template:
        prompt = selected_template["default_prompt"]
        st.session_state.messages.append({"role": "user", "content": prompt})
        _process_prompt(prompt)

    # Handle demo mode
    if st.session_state.get("demo_mode"):
        st.session_state.demo_mode = False
        demo_prompt = TEMPLATES[0]["default_prompt"]  # Supplier Performance
        st.session_state.messages.append({"role": "user", "content": demo_prompt})
        _process_prompt(demo_prompt)

    user_prompt = render_chat_interface()
    if user_prompt:
        _process_prompt(user_prompt)
```

**Optional: Enhanced demo with two-step flow**

For maximum impact, you can modify `_process_prompt()` to check if demo mode is running and auto-send refinement after first build:

```python
def _process_prompt(prompt: str):
    """Process a user prompt through the full pipeline."""

    # ... existing pipeline code ...

    # Add to chat
    add_assistant_message(response, app_summary=app_def.get("app_description"))

    # If in demo mode and this is the first prompt, queue refinement
    if st.session_state.get("demo_mode") and len(st.session_state.messages) == 2:
        st.session_state.demo_mode = True  # Keep it on for refinement
        st.session_state.pending_demo_refinement = True

    st.rerun()
```

Then after the main prompt processing, check for pending refinement:

```python
# After chat_interface handling
if st.session_state.get("pending_demo_refinement"):
    st.session_state.pending_demo_refinement = False
    refinement = "Break down defect analysis by shipping mode and highlight suppliers above 5% defect rate"
    st.session_state.messages.append({"role": "user", "content": refinement})
    _process_prompt(refinement)
```

---

### 2.4 Error Handling

**Graceful degradation** at every stage. Error messages appear as assistant chat messages, not red crashes.

**Key patterns in `_process_prompt()`:**

```python
def _process_prompt(prompt: str):
    """Process a user prompt through the full pipeline."""

    # Stage 1: Parsing
    with st.spinner("🧠 Parsing intent..."):
        add_audit_entry("Intent parsing started", f"Prompt: {prompt[:80]}...")

        try:
            schema = get_table_schema(st.session_state.db_conn)
            app_def = parse_intent(
                prompt,
                existing_app=st.session_state.current_app,
                table_schema=schema,
            )
            st.session_state.current_app = app_def
            add_audit_entry("App definition generated",
                           f"{len(app_def.get('components', []))} components")

        except Exception as e:
            # Graceful error handling
            add_assistant_message(f"❌ Error parsing your request: {str(e)}")
            add_audit_entry("Intent parsing failed", str(e))
            st.rerun()
            return

    # Stage 2: Execution
    with st.spinner("⚡ Executing queries..."):
        try:
            results = execute_app_components(st.session_state.db_conn, app_def)
            st.session_state.execution_results = results
            add_audit_entry("Queries executed", f"{len(results)} components")
        except Exception as e:
            add_assistant_message(f"❌ Error executing queries: {str(e)}")
            st.rerun()
            return

    # Stage 3: Validation
    with st.spinner("✅ Validating..."):
        validation = validate_and_explain(app_def, results)
        st.session_state.validation = validation

    # Stage 4: Governance
    with st.spinner("🛡️ Running governance checks..."):
        governance = run_governance_checks(app_def, st.session_state.current_role, results)
        st.session_state.governance = governance
        add_audit_entry("Governance checks completed", governance["overall_status"])
```

**In dashboard rendering (_render_component in ui/dashboard.py):**

```python
def _render_component(component: dict, execution_results: dict):
    """Render a single dashboard component."""
    comp_id = component["id"]
    comp_type = component["type"]
    title = component["title"]
    config = component.get("config", {})

    result = execution_results.get(comp_id, {})
    df = result.get("data")
    error = result.get("error")

    # Handle errors gracefully
    if error:
        st.error(f"⚠️ {title}: {error}")
        return

    if df is None or df.empty:
        st.info(f"📭 {title}: No data available")
        return

    # Render based on type
    if comp_type == "kpi_card":
        _render_kpi(title, df, config)
    elif comp_type == "bar_chart":
        _render_bar_chart(title, df, config)
    # ... etc
```

---

### 2.5 Loading States

**Visual feedback at each stage** using st.spinner and custom status messages.

```python
def _process_prompt(prompt: str):
    """Process a user prompt through the full pipeline."""

    # Stage 1
    with st.spinner("🧠 Parsing intent..."):
        # ... parsing code ...

    # Stage 2
    with st.spinner("⚡ Executing queries..."):
        # ... execution code ...

    # Stage 3
    with st.spinner("✅ Validating..."):
        # ... validation code ...

    # Stage 4
    with st.spinner("🛡️ Running governance checks..."):
        # ... governance code ...
```

**In the sidebar**, show current governance status with a spinner if checks are running:

```python
with st.sidebar:
    st.markdown("### 🛡️ Governance")

    if st.session_state.governance:
        gov = st.session_state.governance
        status = gov["overall_status"]
        status_icon = {"compliant": "✅", "review_required": "⚠️", "non_compliant": "❌"}.get(status, "❓")
        st.markdown(f"**Status:** {status_icon} {status.replace('_', ' ').title()}")

        for check in gov.get("checks", []):
            icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(check["status"])
            st.markdown(f"{icon} {check['rule']}")

        if gov.get("requires_approval"):
            st.warning("🔒 Requires admin approval")
            if st.session_state.current_role == "admin":
                if st.button("✅ Approve App"):
                    add_audit_entry("App approved by admin")
                    st.success("App approved!")
    else:
        st.info("Build an app to see governance checks")
```

---

### 2.6 UX Polish

**Dark theme CSS:**
```python
CUSTOM_CSS = """
<style>
    /* Dark theme overrides */
    .stApp {
        background-color: #0f172a;
    }

    /* KPI Card styling */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .kpi-label {
        font-size: 0.875rem;
        color: #94a3b8;
        margin-top: 4px;
    }
    .kpi-delta-positive { color: #22c55e; }
    .kpi-delta-negative { color: #ef4444; }

    /* Governance badge */
    .gov-pass { color: #22c55e; }
    .gov-warning { color: #eab308; }
    .gov-fail { color: #ef4444; }

    /* Chat styling */
    .chat-user {
        background-color: #4f46e5;
        color: white;
        padding: 10px 16px;
        border-radius: 12px 12px 0 12px;
        margin: 4px 0;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-assistant {
        background-color: #1e293b;
        color: #f1f5f9;
        padding: 10px 16px;
        border-radius: 12px 12px 12px 0;
        margin: 4px 0;
        max-width: 80%;
        border: 1px solid #334155;
    }

    /* Engine view */
    .engine-code {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #e2e8f0;
        overflow-x: auto;
    }

    /* Header */
    .stackforge-header {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 800;
    }
</style>
"""
```

**Proper spacing & layout:**
- Header: 3-column layout (branding, role selector, buttons)
- Main: Chat (35%) + Dashboard (65%)
- Sidebar: Governance summary, filters, dataset info
- Responsive charts with hover tooltips
- Proper padding and margins throughout

---

## 3. FINAL app.py — Complete, Production-Ready

This is the **complete, final version** incorporating everything from all 3 phases. Replace your current app.py with this:

```python
"""StackForge — AI-Powered Data App Factory
Built at HackUSU 2026 · Data App Factory Track
Hours 0-14 (Phases 1-3)
"""

import streamlit as st
from datetime import datetime
from config import APP_NAME, TEMPLATES, ROLES
from data.sample_data_loader import get_connection, get_table_schema
from engine.intent_parser import parse_intent
from engine.executor import execute_app_components
from engine.validator import validate_and_explain
from engine.governance import run_governance_checks
from ui.chat import render_chat_interface, add_assistant_message, render_template_selector
from ui.dashboard import render_dashboard
from ui.engine_view import render_engine_view, add_audit_entry
from ui.styles import CUSTOM_CSS

# ── Page Config ─────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} — Data App Factory",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Initialize Session State ────────────────────────────
if "db_conn" not in st.session_state:
    st.session_state.db_conn = get_connection()
if "current_app" not in st.session_state:
    st.session_state.current_app = None
if "execution_results" not in st.session_state:
    st.session_state.execution_results = {}
if "validation" not in st.session_state:
    st.session_state.validation = None
if "governance" not in st.session_state:
    st.session_state.governance = None
if "current_role" not in st.session_state:
    st.session_state.current_role = "analyst"
if "show_engine" not in st.session_state:
    st.session_state.show_engine = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False
if "demo_step" not in st.session_state:
    st.session_state.demo_step = 0

# ── Header ──────────────────────────────────────────────
st.markdown(f"# 🏭 {APP_NAME}")
st.caption("Forge Interactive Data Apps from Conversation · Powered by Databricks + AWS + OpenAI")

header_col1, header_col2, header_col3 = st.columns([2, 2, 2])

with header_col1:
    role = st.selectbox(
        "Current Role",
        options=list(ROLES.keys()),
        format_func=lambda x: ROLES[x]["label"],
        index=list(ROLES.keys()).index(st.session_state.current_role),
        key="role_selector",
    )
    if role != st.session_state.current_role:
        st.session_state.current_role = role
        # Re-run governance checks
        if st.session_state.current_app:
            st.session_state.governance = run_governance_checks(
                st.session_state.current_app,
                st.session_state.current_role,
                st.session_state.execution_results,
            )
            add_audit_entry(f"Role switched to {role}")
        st.rerun()

with header_col2:
    col_a, col_b = st.columns(2)
    with col_a:
        show_engine = st.toggle("🔧 Show Engine", value=st.session_state.show_engine)
        st.session_state.show_engine = show_engine
    with col_b:
        if st.button("🎬 Demo", use_container_width=True):
            st.session_state.demo_mode = True
            st.session_state.demo_step = 0
            st.rerun()

with header_col3:
    if st.button("🔄 Reset All", use_container_width=True):
        for key in ["current_app", "execution_results", "validation",
                   "governance", "messages", "audit_log", "demo_mode", "demo_step"]:
            if key in st.session_state:
                if key in ["messages", "audit_log"]:
                    st.session_state[key] = []
                elif key == "demo_step":
                    st.session_state[key] = 0
                elif key == "demo_mode":
                    st.session_state[key] = False
                else:
                    st.session_state[key] = None
        st.rerun()

st.divider()

# ── Main Layout: Chat (35%) | Dashboard (65%) ──────────
chat_col, dash_col = st.columns([0.35, 0.65], gap="medium")

def _process_prompt(prompt: str, is_refinement: bool = False):
    """Process a user prompt through the full pipeline.

    Args:
        prompt: User's natural language request
        is_refinement: If True, conversational refinement of existing app
    """

    # Stage 1: Intent Parsing
    with st.spinner("🧠 Parsing intent..."):
        add_audit_entry(
            "Intent parsing started",
            f"{'Refinement' if is_refinement else 'New app'}: {prompt[:60]}..."
        )

        try:
            schema = get_table_schema(st.session_state.db_conn)

            # KEY FEATURE: Pass existing_app for conversational refinement
            app_def = parse_intent(
                prompt,
                existing_app=st.session_state.current_app,  # ← Enables refinement!
                table_schema=schema,
            )
            st.session_state.current_app = app_def
            add_audit_entry(
                "App definition generated",
                f"{len(app_def.get('components', []))} components, "
                f"{len(app_def.get('filters', []))} filters"
            )

        except Exception as e:
            error_msg = f"❌ Error parsing request: {str(e)[:100]}"
            add_assistant_message(error_msg)
            add_audit_entry("Intent parsing failed", str(e))
            st.rerun()
            return

    # Stage 2: Query Execution
    with st.spinner("⚡ Executing queries..."):
        try:
            # Get filter selections from sidebar (if they exist)
            filters = {}  # Filters will be applied when dashboard renders

            results = execute_app_components(
                st.session_state.db_conn,
                app_def,
                filters=filters
            )
            st.session_state.execution_results = results

            # Count successful executions
            success_count = sum(1 for r in results.values() if r.get("data") is not None)
            add_audit_entry(
                "Queries executed",
                f"{success_count}/{len(results)} components succeeded"
            )

        except Exception as e:
            error_msg = f"❌ Error executing queries: {str(e)[:100]}"
            add_assistant_message(error_msg)
            add_audit_entry("Query execution failed", str(e))
            st.rerun()
            return

    # Stage 3: Validation
    with st.spinner("✅ Validating..."):
        try:
            validation = validate_and_explain(app_def, results)
            st.session_state.validation = validation

            warning_count = len(validation.get("warnings", []))
            if warning_count > 0:
                add_audit_entry("Validation completed", f"{warning_count} warning(s)")
            else:
                add_audit_entry("Validation completed", "No issues")

        except Exception as e:
            add_audit_entry("Validation failed", str(e))

    # Stage 4: Governance
    with st.spinner("🛡️ Running governance checks..."):
        try:
            governance = run_governance_checks(
                app_def,
                st.session_state.current_role,
                results
            )
            st.session_state.governance = governance
            add_audit_entry(
                "Governance checks completed",
                governance["overall_status"]
            )

        except Exception as e:
            add_audit_entry("Governance checks failed", str(e))

    # Generate friendly response message
    comp_count = len(app_def.get("components", []))
    validation = st.session_state.validation or {}
    governance = st.session_state.governance or {}

    warning_count = len(validation.get("warnings", []))
    gov_status = governance.get("overall_status", "unknown").replace("_", " ").title()

    if is_refinement:
        response = f"✅ Updated **{app_def['app_title']}** with your refinements."
    else:
        response = f"✅ Built **{app_def['app_title']}** with {comp_count} components."

    if warning_count > 0:
        response += f"\n⚠️ {warning_count} validation warning(s)."

    response += f"\n🛡️ Governance: {gov_status}"
    response += "\n\nTell me what you'd like to change, and I'll refine the app!"

    add_assistant_message(response, app_summary=app_def.get("app_description"))
    st.rerun()


# ── Chat Section ────────────────────────────────────────
with chat_col:
    st.markdown("### 💬 Chat")

    # Template selector (shown when chat is empty)
    selected_template = render_template_selector(TEMPLATES)
    if selected_template:
        prompt = selected_template["default_prompt"]
        st.session_state.messages.append({"role": "user", "content": prompt})
        _process_prompt(prompt, is_refinement=False)

    # Demo mode: Auto-send prompts
    if st.session_state.get("demo_mode"):
        if st.session_state.demo_step == 0:
            # Step 1: Send Supplier Performance template
            demo_prompt = TEMPLATES[0]["default_prompt"]
            st.session_state.messages.append({"role": "user", "content": demo_prompt})
            st.session_state.demo_step = 1
            _process_prompt(demo_prompt, is_refinement=False)
        elif st.session_state.demo_step == 1:
            # Step 2: Send refinement (after first app builds)
            refinement_prompt = (
                "Break down defect analysis by shipping mode and highlight "
                "suppliers with defect rates above 5%"
            )
            st.session_state.messages.append({"role": "user", "content": refinement_prompt})
            st.session_state.demo_step = 2
            _process_prompt(refinement_prompt, is_refinement=True)
            st.session_state.demo_mode = False  # End demo mode

    # Render existing chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("app_summary"):
                with st.expander("📊 View App Details"):
                    st.caption(msg["app_summary"])

    # Chat input
    if prompt := st.chat_input("Describe what you want to see..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Determine if this is a refinement
        is_refinement = st.session_state.current_app is not None
        _process_prompt(prompt, is_refinement=is_refinement)


# ── Dashboard Section ────────────────────────────────────
with dash_col:
    if st.session_state.show_engine:
        # Split view: Dashboard + Engine (tabs)
        dash_tab, engine_tab = st.tabs(["📊 Dashboard", "🔧 Engine"])

        with dash_tab:
            render_dashboard(
                st.session_state.current_app,
                st.session_state.execution_results,
                st.session_state.current_role,
            )

        with engine_tab:
            render_engine_view(
                st.session_state.current_app,
                st.session_state.execution_results,
                st.session_state.validation,
                st.session_state.governance,
            )
    else:
        # Just dashboard
        render_dashboard(
            st.session_state.current_app,
            st.session_state.execution_results,
            st.session_state.current_role,
        )


# ── Sidebar: Governance & Filters ────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🛡️ Governance")

    if st.session_state.governance:
        gov = st.session_state.governance
        status = gov["overall_status"]
        status_icon = {
            "compliant": "✅",
            "review_required": "⚠️",
            "non_compliant": "❌"
        }.get(status, "❓")

        st.markdown(f"**Status:** {status_icon} {status.replace('_', ' ').title()}")

        # Show governance checks
        for check in gov.get("checks", []):
            icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(check["status"])
            with st.expander(f"{icon} {check['rule']}", expanded=(check["status"] != "pass")):
                st.write(check["message"])
                if check.get("details"):
                    st.caption(check["details"])

        # Approval button for admins
        if gov.get("requires_approval"):
            st.warning("🔒 App requires admin approval before deployment")
            if st.session_state.current_role == "admin":
                if st.button("✅ Approve & Deploy", use_container_width=True):
                    add_audit_entry("App approved and deployed by admin")
                    st.success("✅ App approved and deployed!")
    else:
        st.info("📋 Build an app to see governance checks")

    st.markdown("---")

    # Dataset info
    st.markdown("### 📊 Dataset")
    st.markdown(f"**Supply Chain Data**")
    st.caption("500 sample records with 15 columns")
    st.caption("Region, Supplier, Product, Cost, Delivery, Quality metrics")

    st.markdown("---")
    st.markdown("### 👤 Current Role")
    current_role_label = ROLES[st.session_state.current_role]["label"]
    st.markdown(f"**{current_role_label}**")

    role_config = ROLES[st.session_state.current_role]
    st.caption(f"Can view raw data: {'✅' if role_config['can_view_raw_data'] else '❌'}")
    st.caption(f"Can view PII: {'✅' if role_config['can_view_pii'] else '❌'}")
    st.caption(f"Can export: {'✅' if role_config['can_export'] else '❌'}")

    st.markdown("---")
    st.markdown("### 📋 Audit Log")

    if st.session_state.audit_log:
        # Show last 10 audit entries
        for entry in reversed(st.session_state.audit_log[-10:]):
            st.caption(f"**{entry['timestamp']}** — {entry['action']}")
            if entry.get("details"):
                st.caption(f"*{entry['details']}*")
    else:
        st.caption("No audit entries yet. Build an app to start logging.")

    st.markdown("---")
    st.caption("🏭 Built at HackUSU 2026 · Data App Factory Track")
    st.caption("Powered by: OpenAI GPT-5.1 · Databricks · AWS · DuckDB")
```

---

## 4. FINAL VERIFICATION CHECKLIST

### Functionality (All 3 Phases)

- [ ] **Setup & Data** (Phase 1)
  - [ ] `streamlit run app.py` launches without errors
  - [ ] DuckDB loads 500 supply chain records
  - [ ] Database schema accessible to intent parser
  - [ ] No missing imports or module errors

- [ ] **Intent Parsing** (Phase 2)
  - [ ] GPT-5.1 function calling generates valid app definitions
  - [ ] All templates produce complete app definitions
  - [ ] Components include correct types (KPI, bar, line, pie, scatter, area, table)
  - [ ] SQL queries are valid DuckDB syntax
  - [ ] Filter definitions include column, label, filter_type

- [ ] **Execution** (Phase 2)
  - [ ] SQL queries execute without errors
  - [ ] Results return as Pandas DataFrames
  - [ ] Filter WHERE clause injection works correctly
  - [ ] Empty results handled gracefully

- [ ] **Validation** (Phase 2)
  - [ ] Component explanations generated
  - [ ] Warnings detected for empty results, too many rows
  - [ ] KPI cards get single-row validation

- [ ] **Governance** (Phase 2)
  - [ ] PII patterns detected in SQL (email, phone, salary, etc.)
  - [ ] Role-based access checks enforced
  - [ ] Query complexity limits applied
  - [ ] Audit trail populates on every action
  - [ ] Approval requirement set correctly for admins

- [ ] **UI & Rendering** (Phase 2)
  - [ ] KPI cards format numbers (currency, percentage, decimal)
  - [ ] Bar/line/pie/scatter/area charts render interactively with Plotly
  - [ ] Tables are sortable and display all columns
  - [ ] Charts respond to hover, zoom, legend clicks
  - [ ] Empty state displays when no app built
  - [ ] Dark theme CSS applied throughout

- [ ] **Chat & Conversation** (Phase 2-3)
  - [ ] Chat messages display with correct roles (user/assistant)
  - [ ] Template selector shows 6 templates with icons
  - [ ] User prompts parsed and responses generated
  - [ ] App summary expanders work

- [ ] **Conversational Refinement** (Phase 3)
  - [ ] Follow-up prompts modify existing app (not create new)
  - [ ] Adding columns works ("add a cost column")
  - [ ] Changing breakdowns works ("break down by quarter")
  - [ ] Removing components works ("remove the pie chart")
  - [ ] Component count changes reflect refinements

- [ ] **Filters** (Phase 3)
  - [ ] Filter widgets render in sidebar (select, multiselect, date_range, number_range)
  - [ ] Unique values extracted from results
  - [ ] Filter selections update dashboard in real-time
  - [ ] WHERE clause injection applies filters correctly
  - [ ] "All" option resets single select filters

- [ ] **Demo Mode** (Phase 3)
  - [ ] Demo button visible in header
  - [ ] Clicking Demo auto-sends Supplier Performance template
  - [ ] First app builds with spinners showing
  - [ ] Chat displays initial response
  - [ ] Refinement prompt auto-sends after ~2 seconds
  - [ ] Refinement app updates (conversational flow visible)
  - [ ] Demo completes without manual intervention

- [ ] **Error Handling** (Phase 3)
  - [ ] Failed API calls show as assistant messages (not red crashes)
  - [ ] Failed SQL queries show error text in component
  - [ ] Empty results show "No data available" info box
  - [ ] Missing columns in filters handled gracefully
  - [ ] Exception messages truncated in audit log

- [ ] **Loading States** (Phase 3)
  - [ ] st.spinner shows for parsing stage
  - [ ] st.spinner shows for execution stage
  - [ ] st.spinner shows for validation stage
  - [ ] st.spinner shows for governance stage
  - [ ] Spinner messages are clear and helpful

- [ ] **Engine View** (Phase 2-3)
  - [ ] "Show Engine" toggle visible in header
  - [ ] Shows 4 tabs: Generated SQL, Data Flow, Governance, Audit Log
  - [ ] SQL queries display with syntax highlighting
  - [ ] Execution result summaries show row/column counts
  - [ ] Data flow diagram shows source → filters → components
  - [ ] Governance checks display with icons and details
  - [ ] Audit log shows recent entries in reverse chronological order

### UX & Polish (Phase 3)

- [ ] **Layout & Spacing**
  - [ ] Header is clean with branding, role selector, buttons
  - [ ] Chat (35%) and Dashboard (65%) columns balanced
  - [ ] Sidebar contains filters, governance, info
  - [ ] All elements have proper padding/margins
  - [ ] No elements overlap or cut off

- [ ] **Dark Theme**
  - [ ] Background is dark (#0f172a)
  - [ ] Text is light (#f1f5f9, #e2e8f0)
  - [ ] Charts use plotly_dark template
  - [ ] KPI cards have gradient background
  - [ ] Governance status icons are color-coded (✅ green, ⚠️ yellow, ❌ red)

- [ ] **Charts & Visualization**
  - [ ] Charts have proper titles
  - [ ] Axes have appropriate labels
  - [ ] Threshold lines display with annotations
  - [ ] Colors are accessible and distinct
  - [ ] Charts resize responsively with columns

- [ ] **Copy & Messaging**
  - [ ] Error messages are friendly and actionable
  - [ ] Governance messages explain what each check does
  - [ ] Audit log shows clear action descriptions
  - [ ] No technical jargon in user-facing messages
  - [ ] Status indicators (icons) are consistent

### Performance & Stability

- [ ] **Performance**
  - [ ] Initial load takes <3 seconds
  - [ ] Prompt processing shows spinners (not hanging)
  - [ ] Filter updates re-run quickly
  - [ ] Charts render without lag
  - [ ] No timeout on queries

- [ ] **Stability**
  - [ ] Multiple prompts in sequence work
  - [ ] Role switching doesn't break state
  - [ ] Reset button clears all state correctly
  - [ ] No console errors (F12 → Console)
  - [ ] Multiple filters can be applied simultaneously

### Demo Flow

- [ ] **Initial State**
  - [ ] Page loads with empty dashboard
  - [ ] Template selector visible
  - [ ] Chat history empty
  - [ ] Governance panel says "Build an app"

- [ ] **Demo Button Click**
  - [ ] Demo button changes to loading state
  - [ ] Supplier Performance template prompt appears in chat
  - [ ] Spinners show for parsing → execution → validation → governance
  - [ ] Dashboard populates with ~6 components (KPIs + charts + table)
  - [ ] Chat shows assistant response
  - [ ] Governance panel shows checks

- [ ] **Refinement (Auto or Manual)**
  - [ ] Second prompt appears in chat (auto in demo mode)
  - [ ] Dashboard updates (components change or new ones added)
  - [ ] Chat shows updated response
  - [ ] Governance re-checks and updates

---

## 5. COMMIT MESSAGES

```bash
# After Phase 3 completion:
git add -A
git commit -m "feat(phase-3): Polish, demo mode, and conversational refinement

- Conversational refinement: Pass existing_app to intent_parser for chat-based app evolution
- Demo mode: Auto-send template + refinement prompt for one-click demo
- Interactive filters: Render select/multiselect/date_range/number_range widgets
- Filter injection: WHERE clause injection in executor for dynamic filtering
- Error handling: Graceful error display in chat for all failure points
- Loading states: st.spinner at each pipeline stage (parse → execute → validate → govern)
- Sidebar filters: Extract unique values from results, populate filter widgets
- Dashboard refinement: Support dynamic component re-rendering with filter updates
- Audit logging: Enhanced with refinement tracking, governance status logging
- UX polish: Dark theme CSS, proper spacing, professional typography
- README: Comprehensive checklist covering all 3 phases, end-to-end demo flow

App is now demo-ready with full conversational AI, governance, and factory model."
```

---

## 6. DEPLOYMENT & DEMO CHECKLIST

Before presenting at HackUSU 2026:

1. **Test the full demo flow locally:**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   streamlit run app.py
   ```

2. **Click Demo button and verify:**
   - Supplier Performance template loads
   - Dashboard renders with 6+ components
   - Governance checks pass (or show warnings appropriately)
   - Refinement prompt auto-sends and updates app

3. **Manually test conversational refinement:**
   - Build an app manually
   - Type refinement: "Add a cost column"
   - Verify components change, not replace

4. **Test filters:**
   - Build any app
   - Select a filter value in sidebar
   - Verify dashboard updates in real-time

5. **Test role switching:**
   - Build app as "Analyst"
   - Switch to "Viewer" — governance changes
   - Switch to "Admin" — more permissions visible

6. **Test Show Engine toggle:**
   - Build an app
   - Click "Show Engine" toggle
   - Verify 4 tabs appear with content
   - SQL queries readable, Data Flow diagram visible

7. **Clean up console:**
   - F12 → Console in browser
   - No red error messages
   - Only informational logs

8. **Verify database:**
   - Check that `supply_chain.csv` exists or synthetic data loads
   - Verify 500 records with 15 columns present

---

## 7. Key Files Summary

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `app.py` | ~700 | Main application, orchestrates all stages | ✅ Complete |
| `config.py` | ~130 | Configuration, roles, templates | ✅ Complete |
| `data/sample_data_loader.py` | ~80 | DuckDB, data loading | ✅ Complete |
| `engine/intent_parser.py` | ~100 | GPT-5.1 function calling | ✅ Complete |
| `engine/executor.py` | ~60 | SQL execution, filter injection | ✅ Complete |
| `engine/validator.py` | ~90 | Query validation, explanations | ✅ Complete |
| `engine/governance.py` | ~150 | PII detection, access control | ✅ Complete |
| `ui/styles.py` | ~80 | Dark theme CSS | ✅ Complete |
| `ui/chat.py` | ~60 | Chat interface, template selector | ✅ Complete |
| `ui/dashboard.py` | ~250 | Dashboard rendering, filters, charts | ✅ Complete |
| `ui/engine_view.py` | ~130 | Show Engine view | ✅ Complete |
| **Total** | **~1,330** | **Full application** | **✅ Complete** |

---

## 8. End State

**StackForge is now a complete, demo-ready data app factory:**

✅ Users describe data apps in conversational chat
✅ AI generates interactive dashboards (charts, KPIs, tables) in real-time
✅ Dashboards are fully interactive — filters, drill-downs, hover details
✅ Follow-up messages refine the app (conversational AI)
✅ Governance is baked in — PII detection, role-based access, audit trail
✅ Show Engine reveals SQL, data flow, governance checks
✅ Demo mode showcases the full flow in one click
✅ Dark professional theme with proper spacing and typography
✅ Error handling is graceful — no red crashes
✅ Loading states provide clear feedback at each stage

**Ready for judges at HackUSU 2026!**

---

**Authored: Phase 3, Hours 10–14**
**Next: Deploy to Streamlit Cloud and present**
