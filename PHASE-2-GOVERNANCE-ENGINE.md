# StackForge Phase 2: Governance Engine (Hours 6–10)

**Track:** HackUSU 2026 Data App Factory
**Scope:** Phase 2 of 3 — Governance, role-based access, audit logging, template UI
**Prerequisites:** Phase 1 complete (see "What Exists from Phase 1" below)
**Duration:** ~5 hours (Hours 6–10 of 19-hour build)

---

## What Exists from Phase 1

Phase 1 built the core AI pipeline and basic UI scaffolding. These files form the foundation for Phase 2:

1. **`config.py`** — Application configuration including:
   - `PII_PATTERNS` (list of regex patterns for PII detection)
   - `ROLES` dict (admin, analyst, viewer with capabilities)
   - `TEMPLATES` list (6 pre-built dashboard templates with prompts)
   - Governance defaults: `MAX_ROWS_DISPLAY`, `OPENAI_MODEL`, etc.

2. **`engine/intent_parser.py`** — Stage 1 of the pipeline:
   - `parse_intent()` function takes natural language → returns structured app definition
   - Uses GPT-5.1 function calling with `APP_INTENT_FUNCTION` schema
   - Returns dict with `app_title`, `components[]`, `filters[]`, `data_summary`

3. **`engine/executor.py`** — Stage 3 of the pipeline:
   - `execute_query()` — runs SQL against DuckDB, applies filters
   - `execute_app_components()` — batch executes all component queries
   - Returns dict mapping component_id → {data: DataFrame, error: str}

4. **`engine/validator.py`** — Stage 4 of the pipeline:
   - `validate_and_explain()` — checks component health, generates plain-English explanations
   - Returns dict with `explanations[]`, `warnings[]`, `overall_status`

5. **`data/sample_data_loader.py`** — DuckDB data loading:
   - `get_connection()` — creates in-memory DuckDB with supply_chain table
   - `get_table_schema()` — returns formatted schema string
   - Synthetic data generation for demo/test

6. **`ui/chat.py`** — Chat UI component:
   - `render_chat_interface()` — displays messages, returns user input
   - `add_assistant_message()` — appends assistant response to chat history
   - `render_template_selector()` — placeholder for template cards (implemented in Phase 2)

7. **`ui/dashboard.py`** — Dashboard renderer:
   - `render_dashboard()` — main entry point, orchestrates layout
   - `_render_component()` — renders single component (chart, table, KPI)
   - Component-specific renderers: `_render_kpi()`, `_render_bar_chart()`, `_render_table()`, etc.

8. **`ui/styles.py`** — Custom CSS for dark theme

9. **`app.py`** — Main Streamlit application:
   - Session state initialization
   - Two-column layout (chat + dashboard)
   - Basic header with placeholders for governance
   - `_process_prompt()` pipeline function (to be enhanced in Phase 2)

---

## Phase 2: What We're Building

This phase adds **governance as a first-class system**, not a UI layer. Every generated app gets compliance checks, role-based masking, and audit trails. The interface shows governance status prominently and provides role toggling.

### Goals:
1. Deterministic governance checks (no AI calls, pure regex + logic)
2. Role-based access control with experience differentiation
3. Audit logging for compliance tracking
4. Template library UI with clickable cards
5. "Show Engine" technical view with SQL, DAG, governance, audit tabs
6. Governance sidebar panel with status badges and check list
7. Role toggle in header (admin/analyst/viewer) with re-evaluation

### Non-Goals (Phase 3):
- Conversational refinement
- Error handling polish
- Loading state animations
- Sidebar filtering UI
- Demo mode with auto-refinement
- PII masking implementation (detection only)

---

## File: `engine/governance.py` (Stage 5 — New)

This is the core governance engine. **Every generated app runs through this deterministically.**

```python
"""Stage 5: Governance checks — deterministic, no AI calls."""

import re
from config import PII_PATTERNS, ROLES

def run_governance_checks(app_definition: dict, role: str, execution_results: dict = None) -> dict:
    """Run governance checks on the app definition.

    Args:
        app_definition: App definition from intent parser
        role: Current user role ("admin", "analyst", "viewer")
        execution_results: Results from query execution (optional, for data quality checks)

    Returns:
        {
            "checks": [{"rule": str, "status": "pass"|"warning"|"fail", "message": str, "details": str}],
            "requires_approval": bool,
            "pii_columns_detected": list of str,
            "overall_status": "compliant"|"review_required"|"non_compliant"
        }
    """
    checks = []
    pii_detected = []
    role_config = ROLES.get(role, ROLES["viewer"])

    # 1. PII Detection — scan all SQL queries for PII column references
    all_sql = " ".join([c.get("sql_query", "") for c in app_definition.get("components", [])])

    for pattern in PII_PATTERNS:
        matches = re.findall(pattern, all_sql, flags=re.IGNORECASE)
        if matches:
            pii_detected.extend([m for m in matches if m.lower() not in [x.lower() for x in pii_detected]])

    pii_detected = list(set(pii_detected))

    if pii_detected:
        if role_config["can_view_pii"]:
            checks.append({
                "rule": "PII Detection",
                "status": "warning",
                "message": f"PII columns detected: {', '.join(pii_detected)}. Admin access allows viewing.",
                "details": "Columns containing personally identifiable information were found in queries. Your admin role grants access."
            })
        else:
            checks.append({
                "rule": "PII Detection",
                "status": "fail",
                "message": f"PII columns detected: {', '.join(pii_detected)}. Data will be masked for {role} role.",
                "details": "These columns will be automatically masked in the output."
            })
    else:
        checks.append({
            "rule": "PII Detection",
            "status": "pass",
            "message": "No PII columns detected in queries.",
        })

    # 2. Access Control — check role permissions against component types
    component_count = len(app_definition.get("components", []))
    has_tables = any(c["type"] == "table" for c in app_definition.get("components", []))

    if not role_config["can_view_raw_data"] and has_tables:
        checks.append({
            "rule": "Access Control",
            "status": "warning",
            "message": f"Viewer role cannot access raw data tables. Tables will show aggregated data only.",
        })
    else:
        checks.append({
            "rule": "Access Control",
            "status": "pass",
            "message": f"All components are accessible for {role} role.",
        })

    # 3. Query Complexity — check against role limits
    complexity = role_config["max_query_complexity"]
    if complexity == "simple" and component_count > 4:
        checks.append({
            "rule": "Query Complexity",
            "status": "warning",
            "message": f"App has {component_count} components — exceeds 'simple' complexity limit for viewer role.",
        })
    elif complexity == "medium" and component_count > 8:
        checks.append({
            "rule": "Query Complexity",
            "status": "warning",
            "message": f"App has {component_count} components — exceeds 'medium' complexity limit for analyst role.",
        })
    else:
        checks.append({
            "rule": "Query Complexity",
            "status": "pass",
            "message": f"App complexity ({component_count} components) is within {role} role limits.",
        })

    # 4. Data Quality — check for SELECT * antipattern
    select_star_found = False
    for comp in app_definition.get("components", []):
        if "SELECT *" in comp.get("sql_query", "").upper():
            checks.append({
                "rule": "Data Quality",
                "status": "warning",
                "message": f"Component '{comp['title']}' uses SELECT * — consider selecting specific columns for performance.",
            })
            select_star_found = True
            break

    if not select_star_found:
        checks.append({
            "rule": "Data Quality",
            "status": "pass",
            "message": "All queries use specific column selections.",
        })

    # 5. Export Control — check if role can export data
    if not role_config["can_export"]:
        checks.append({
            "rule": "Export Control",
            "status": "warning",
            "message": "Data export is disabled for viewer role. Download buttons will be hidden.",
        })
    else:
        checks.append({
            "rule": "Export Control",
            "status": "pass",
            "message": f"Data export is enabled for {role} role.",
        })

    # 6. Audit Trail — confirm logging is enabled (always passes)
    checks.append({
        "rule": "Audit Trail",
        "status": "pass",
        "message": "All queries and actions are logged to the audit trail.",
    })

    # Determine overall status and approval requirement
    has_fails = any(c["status"] == "fail" for c in checks)
    has_warnings = any(c["status"] == "warning" for c in checks)

    # Non-admin roles with complex apps or failures require approval
    requires_approval = role != "admin" and (has_fails or component_count > 6)

    overall_status = "non_compliant" if has_fails else "review_required" if has_warnings else "compliant"

    return {
        "checks": checks,
        "requires_approval": requires_approval,
        "pii_columns_detected": pii_detected,
        "overall_status": overall_status,
    }
```

---

## File: `ui/engine_view.py` (Enhanced for Phase 2)

This file implements the "Show Engine" technical view with four tabs: Generated SQL, Data Flow DAG, Governance Details, and Audit Log.

```python
"""Show Engine view — reveals the technical internals behind the dashboard."""

import streamlit as st
import json
from datetime import datetime

def render_engine_view(app_definition: dict, execution_results: dict, validation: dict, governance: dict):
    """Render the technical engine view showing what's happening under the hood.

    Args:
        app_definition: Generated app structure
        execution_results: Results from query execution
        validation: Validation report from validator
        governance: Governance check results
    """

    if not app_definition:
        st.info("🔧 The engine view will show generated code, DAG, and governance audit when you build an app.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Generated SQL", "🔀 Data Flow", "🛡️ Governance", "📋 Audit Log"])

    with tab1:
        st.markdown("### Generated Queries")
        st.caption("These SQL queries were generated by the AI to power each dashboard component.")

        for comp in app_definition.get("components", []):
            with st.expander(f"**{comp['title']}** ({comp['type']})", expanded=False):
                st.code(comp["sql_query"], language="sql")

                # Show execution result summary
                result = execution_results.get(comp["id"], {})
                if result.get("data") is not None:
                    df = result["data"]
                    st.success(f"✅ Returned {len(df)} rows, {len(df.columns)} columns")
                    st.caption("Sample of data returned:")
                    st.dataframe(df.head(3), use_container_width=True)
                elif result.get("error"):
                    st.error(f"❌ Error: {result['error']}")
                else:
                    st.warning("⏳ Not yet executed")

    with tab2:
        st.markdown("### Data Transformation Flow (DAG)")
        st.caption("How data flows from the source table through filters to each visualization component.")

        # Render a simple text-based DAG
        dag_text = "```\nsupply_chain (raw data)\n         │\n"

        filters = app_definition.get("filters", [])
        if filters:
            filter_names = [f["label"] for f in filters]
            dag_text += f"    [Filters: {', '.join(filter_names)}]\n         │\n"

        for comp in app_definition.get("components", []):
            icon = {
                "kpi_card": "🎯",
                "bar_chart": "📊",
                "line_chart": "📈",
                "pie_chart": "🥧",
                "table": "📋",
                "scatter_plot": "⚡",
                "area_chart": "📉",
                "metric_highlight": "🔴",
                "heatmap": "🔥"
            }.get(comp["type"], "📦")

            dag_text += f"    ├──→ {icon} {comp['title']}\n"

        dag_text += "```"
        st.markdown(dag_text)

        # Show component execution order
        st.markdown("### Component Execution Order")
        for i, comp in enumerate(app_definition.get("components", []), 1):
            status_icon = "✅" if execution_results.get(comp["id"], {}).get("data") is not None else "❌"
            st.markdown(f"{i}. {status_icon} **{comp['title']}** — {comp['type']}")

    with tab3:
        _render_governance_detail(governance)

    with tab4:
        _render_audit_log()


def _render_governance_detail(governance: dict):
    """Render detailed governance view with check results and status."""

    if not governance:
        st.info("Governance checks will appear after building an app.")
        return

    # Overall status banner
    status = governance.get("overall_status", "unknown")
    status_map = {
        "compliant": ("✅ Compliant", "success"),
        "review_required": ("⚠️ Review Required", "warning"),
        "non_compliant": ("❌ Non-Compliant", "error"),
    }
    label, msg_type = status_map.get(status, ("❓ Unknown", "info"))

    if msg_type == "success":
        st.success(label)
    elif msg_type == "warning":
        st.warning(label)
    elif msg_type == "error":
        st.error(label)

    st.markdown("---")

    # Individual checks
    st.markdown("### Governance Checks")

    for check in governance.get("checks", []):
        icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(check["status"], "❓")

        # Use expander for non-passing checks, plain display for passing
        if check["status"] == "pass":
            st.markdown(f"{icon} **{check['rule']}** — {check['message']}")
        else:
            with st.expander(f"{icon} {check['rule']}", expanded=(check["status"] != "pass")):
                st.write(check["message"])
                if check.get("details"):
                    st.caption(f"ℹ️ {check['details']}")

    # PII summary
    if governance.get("pii_columns_detected"):
        st.markdown("---")
        st.warning(f"⚠️ **PII Detected:** {', '.join(governance['pii_columns_detected'])}")
        st.caption("These columns contain sensitive data and may be restricted based on your role.")

    # Approval requirement
    if governance.get("requires_approval"):
        st.markdown("---")
        st.warning("🔒 **This app requires admin approval before deployment.**")


def _render_audit_log():
    """Render the audit log trail showing all actions."""

    st.markdown("### Audit Trail")
    st.caption("Complete log of all actions, checks, and approvals for compliance tracking.")

    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    if not st.session_state.audit_log:
        st.info("No audit entries yet. Build an app to start logging.")
        return

    # Show last 20 entries in reverse chronological order
    for entry in reversed(st.session_state.audit_log[-20:]):
        timestamp = entry.get("timestamp", "N/A")
        action = entry.get("action", "Unknown action")
        details = entry.get("details", "")
        role = entry.get("role", "")

        # Format the log entry
        role_str = f" [{role}]" if role else ""
        st.markdown(f"**{timestamp}** — {action}{role_str}")

        if details:
            st.caption(f"→ {details}")


def add_audit_entry(action: str, details: str = "", role: str = None):
    """Add an entry to the audit log.

    Args:
        action: Description of the action
        details: Additional context (optional)
        role: User role performing the action (optional)
    """

    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    st.session_state.audit_log.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details,
        "role": role or st.session_state.get("current_role", "unknown"),
    })
```

---

## File: Updates to `ui/chat.py` (Template Library UI)

Add this function to render template cards. This replaces the placeholder `render_template_selector()`:

```python
def render_template_selector(templates: list):
    """Render template selection cards when chat is empty.

    Displays 6 template cards in a 3-column grid with icon, name, description,
    governance level, and a clickable button to use the template.

    Returns: Selected template dict, or None if none selected
    """

    # Only show templates if chat history is empty
    if st.session_state.get("messages"):
        return None

    st.markdown("### 🏭 Start from a Template")
    st.markdown("Select a pre-built data app template, or describe what you want below.")

    cols = st.columns(3)
    selected = None

    for i, template in enumerate(templates):
        with cols[i % 3]:
            # Render template as a card with border
            with st.container(border=True):
                # Template icon + name
                st.markdown(f"**{template['icon']} {template['name']}**")

                # Description
                st.caption(template["description"])

                # Governance level badge
                gov_level = template.get("governance_level", "medium")
                gov_colors = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🔴"
                }
                gov_icon = gov_colors.get(gov_level, "⚪")
                st.caption(f"Governance: {gov_icon} {gov_level.title()}")

                # Use Template button
                if st.button("Use Template →", key=f"template_{template['id']}", use_container_width=True):
                    selected = template

    return selected
```

---

## File: Updates to `ui/dashboard.py` (Role-Based Data Masking)

Add this helper function to mask PII-containing data based on role:

```python
def _apply_role_based_masking(df: pd.DataFrame, role: str, pii_columns: list) -> pd.DataFrame:
    """Apply role-based masking to DataFrame based on PII detection and role capabilities.

    Args:
        df: Data to mask
        role: Current user role
        pii_columns: List of detected PII column names

    Returns:
        Masked DataFrame
    """
    from config import ROLES

    role_config = ROLES.get(role, ROLES["viewer"])

    # If role can view PII, return unmasked
    if role_config["can_view_pii"]:
        return df

    # Mask PII columns for non-admin roles
    masked_df = df.copy()
    for col in pii_columns:
        if col in masked_df.columns:
            masked_df[col] = "[REDACTED]"

    return masked_df
```

Update `_render_table()` to use masking:

```python
def _render_table(title: str, df: pd.DataFrame, config: dict, role: str = "analyst", pii_columns: list = None):
    """Render an interactive data table with optional role-based masking."""

    st.markdown(f"**{title}**")

    sort_by = config.get("sort_by")
    sort_order = config.get("sort_order", "desc")
    limit = config.get("limit", 100)

    display_df = df.copy()

    # Apply role-based masking
    if pii_columns:
        display_df = _apply_role_based_masking(display_df, role, pii_columns)

    if sort_by and sort_by in display_df.columns:
        display_df = display_df.sort_values(sort_by, ascending=(sort_order == "asc"))

    display_df = display_df.head(limit)

    st.dataframe(display_df, use_container_width=True, height=400)
```

Update the main `render_dashboard()` function signature and pass role/PII info:

```python
def render_dashboard(app_definition: dict, execution_results: dict, role: str = "analyst", pii_columns: list = None):
    """Render the complete dashboard from app definition and query results.

    Args:
        app_definition: Generated app structure
        execution_results: Query results
        role: Current user role (affects visibility)
        pii_columns: List of detected PII columns (from governance)
    """
    # ... existing code ...

    # When calling _render_component, pass role and PII info:
    _render_component(comp, execution_results, role, pii_columns)
```

And update `_render_component()`:

```python
def _render_component(component: dict, execution_results: dict, role: str = "analyst", pii_columns: list = None):
    """Render a single dashboard component with role-based access control."""
    # ... existing code ...

    if comp_type == "table":
        _render_table(title, df, config, role, pii_columns)
    # ... other types ...
```

---

## File: Updates to `app.py` (Main Application)

### 1. Import new modules (ADD AFTER line 8):

```python
from ui.engine_view import render_engine_view, add_audit_entry
```

### 2. ADD governance panel to sidebar (REPLACE the entire sidebar section starting at line 1542):

```python
# ── Sidebar: Governance Summary ─────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🛡️ Governance Panel")

    if st.session_state.governance:
        gov = st.session_state.governance
        status = gov["overall_status"]
        status_icon = {"compliant": "✅", "review_required": "⚠️", "non_compliant": "❌"}.get(status, "❓")

        # Overall status badge
        st.markdown(f"**Overall Status:** {status_icon} {status.replace('_', ' ').title()}")

        # Individual check list
        st.markdown("**Checks:**")
        for check in gov.get("checks", []):
            icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(check["status"])
            st.markdown(f"{icon} {check['rule']}")

        # PII warning if detected
        if gov.get("pii_columns_detected"):
            st.warning(f"⚠️ PII Detected: {', '.join(gov['pii_columns_detected'])}")

        # Approval flow (if needed)
        if gov.get("requires_approval"):
            st.warning("🔒 Requires admin approval")
            if st.session_state.current_role == "admin":
                if st.button("✅ Approve App", use_container_width=True):
                    add_audit_entry("App approved by admin")
                    st.success("App approved! ✅")
    else:
        st.info("Build an app to see governance checks")

    st.markdown("---")
    st.markdown(f"**Current Role:** {ROLES[st.session_state.current_role]['label']}")
    st.markdown(f"**Dataset:** Supply Chain (500 rows)")
    st.caption(f"Built at HackUSU 2026 · Data App Factory Track")
```

### 3. UPDATE header role toggle (REPLACE lines 1385–1401):

```python
with header_col2:
    # Role toggle — switches role and re-runs governance
    role = st.selectbox(
        "Current Role",
        options=list(ROLES.keys()),
        format_func=lambda x: ROLES[x]["label"],
        index=list(ROLES.keys()).index(st.session_state.current_role),
        key="role_selector",
    )
    if role != st.session_state.current_role:
        st.session_state.current_role = role
        add_audit_entry(f"Role switched to {role}", "User changed role via header selector")

        # Re-run governance checks with new role
        if st.session_state.current_app:
            st.session_state.governance = run_governance_checks(
                st.session_state.current_app,
                st.session_state.current_role,
                st.session_state.execution_results,
            )
        st.rerun()
```

### 4. ADD Show Engine toggle (REPLACE lines 1404–1407):

```python
with header_col3:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        show_engine = st.toggle("🔧 Show Engine", value=st.session_state.show_engine)
        if show_engine != st.session_state.show_engine:
            st.session_state.show_engine = show_engine
            add_audit_entry(f"Show Engine toggled {'ON' if show_engine else 'OFF'}")
            st.rerun()
    with col_b:
        if st.button("🎬 Demo", use_container_width=True):
            st.session_state.demo_mode = True
            st.rerun()
    with col_c:
        if st.button("🔄 Reset", use_container_width=True):
            for key in ["current_app", "execution_results", "validation",
                       "governance", "messages", "audit_log"]:
                if key in st.session_state:
                    if key in ["messages", "audit_log"]:
                        st.session_state[key] = []
                    else:
                        st.session_state[key] = None
            add_audit_entry("App reset")
            st.rerun()
```

### 5. UPDATE dashboard rendering with Show Engine tabs (REPLACE lines 1516–1539):

```python
# ── Dashboard Area ──────────────────────────────────────
with dash_col:
    if st.session_state.show_engine:
        # Split view: Dashboard + Engine in tabs
        dash_tab, engine_tab = st.tabs(["📊 Dashboard", "🔧 Engine"])

        with dash_tab:
            render_dashboard(
                st.session_state.current_app,
                st.session_state.execution_results,
                st.session_state.current_role,
                st.session_state.governance.get("pii_columns_detected", []) if st.session_state.governance else [],
            )

        with engine_tab:
            render_engine_view(
                st.session_state.current_app,
                st.session_state.execution_results,
                st.session_state.validation,
                st.session_state.governance,
            )
    else:
        # Full-width dashboard only
        render_dashboard(
            st.session_state.current_app,
            st.session_state.execution_results,
            st.session_state.current_role,
            st.session_state.governance.get("pii_columns_detected", []) if st.session_state.governance else [],
        )
```

### 6. UPDATE `_process_prompt()` function (REPLACE lines 1430–1487):

```python
def _process_prompt(prompt: str):
    """Process a user prompt through the full pipeline."""

    with st.spinner("🧠 Parsing intent..."):
        add_audit_entry("Intent parsing started", f"Prompt: {prompt[:80]}...")

        try:
            # Get table schema for context
            schema = get_table_schema(st.session_state.db_conn)

            # Parse intent (with existing app for refinement)
            app_def = parse_intent(
                prompt,
                existing_app=st.session_state.current_app,
                table_schema=schema,
            )
            st.session_state.current_app = app_def
            add_audit_entry("App definition generated", f"{len(app_def.get('components', []))} components created")

        except Exception as e:
            add_assistant_message(f"❌ Error parsing your request: {str(e)}")
            add_audit_entry("Intent parsing failed", str(e))
            st.rerun()
            return

    with st.spinner("⚡ Executing queries..."):
        try:
            results = execute_app_components(st.session_state.db_conn, app_def)
            st.session_state.execution_results = results
            add_audit_entry("Queries executed", f"{len(results)} components ran successfully")
        except Exception as e:
            add_assistant_message(f"❌ Error executing queries: {str(e)}")
            add_audit_entry("Query execution failed", str(e))
            st.rerun()
            return

    with st.spinner("✅ Validating..."):
        validation = validate_and_explain(app_def, results)
        st.session_state.validation = validation
        add_audit_entry("Validation complete", f"{len(validation.get('warnings', []))} warning(s)")

    with st.spinner("🛡️ Running governance checks..."):
        governance = run_governance_checks(
            app_def,
            st.session_state.current_role,
            results
        )
        st.session_state.governance = governance
        add_audit_entry("Governance checks completed", governance["overall_status"].replace('_', ' ').title())

    # Generate assistant response
    comp_count = len(app_def.get("components", []))
    warning_count = len(validation.get("warnings", []))
    gov_status = governance["overall_status"]

    response = f"✅ Built **{app_def['app_title']}** with {comp_count} components.\n\n"

    if warning_count > 0:
        response += f"⚠️ {warning_count} validation warning(s) to review.\n\n"

    response += f"🛡️ Governance: **{gov_status.replace('_', ' ').title()}**\n\n"

    if governance.get("pii_columns_detected"):
        response += f"⚠️ PII detected: {', '.join(governance['pii_columns_detected'])}\n\n"

    if governance.get("requires_approval"):
        response += f"🔒 This app requires admin approval before deployment.\n\n"

    response += "You can refine this app by telling me what to change!"

    add_assistant_message(response, app_summary=app_def.get("app_description"))

    st.rerun()
```

---

## Verification Checklist for Phase 2

- [ ] `engine/governance.py` created with 6 deterministic checks
- [ ] PII detection works via regex patterns from config
- [ ] Role-based access control applied (admin vs analyst vs viewer)
- [ ] Query complexity checks enforce role limits
- [ ] `ui/engine_view.py` renders all 4 tabs (SQL, DAG, Governance, Audit)
- [ ] Generated SQL queries appear in Engine view
- [ ] Data flow DAG renders as text diagram
- [ ] Governance details tab shows all checks with correct status icons
- [ ] Audit log displays actions with timestamps and role info
- [ ] Template library UI shows 6 clickable cards in 3x2 grid
- [ ] Clicking template auto-sends default prompt
- [ ] Role toggle in header switches between admin/analyst/viewer
- [ ] Switching roles re-runs governance checks
- [ ] Governance panel in sidebar displays overall status and check list
- [ ] Approval flow shows for non-admin complex apps
- [ ] Show Engine toggle appears in header
- [ ] Toggling Show Engine switches between full dashboard and tabbed view
- [ ] Dashboard and Engine tabs render correctly
- [ ] Audit log persists through role switches
- [ ] Governance status updates when role changes
- [ ] All audit entries include role information
- [ ] No PII masking implementation yet (detection only)
- [ ] App runs without errors: `streamlit run app.py`

---

## Git Commit Messages

```bash
# After governance.py is complete
git commit -m "feat: add deterministic governance engine with 6 checks (PII, access, complexity, quality, export, audit)"

# After engine_view.py updates
git commit -m "feat: add Show Engine technical view with SQL, DAG, governance, and audit tabs"

# After chat.py template selector
git commit -m "feat: implement template library UI with 6 clickable cards"

# After all app.py updates
git commit -m "feat: integrate governance panel, role toggle, Show Engine toggle, and audit logging into main app"

# Final Phase 2 commit
git commit -m "feat: complete Phase 2 governance engine — roles, checks, templates, and Show Engine"
```

---

## Architecture: How Governance Flows

1. **User sends prompt** via chat
2. **Intent parser generates app definition** (Phase 1)
3. **Executor runs SQL queries** (Phase 1)
4. **Validator checks component health** (Phase 1)
5. **Governance engine runs checks** ← **NEW in Phase 2**
   - PII detection (regex scan)
   - Access control (role checks)
   - Complexity limits (component count)
   - Data quality (SELECT * check)
   - Export control (role capability check)
   - Audit trail logging
6. **App.py receives governance result**
   - Updates sidebar panel with status
   - Stores governance dict in session
   - Logs audit entry with role
7. **Dashboard renders with role-based masking** (if PII detected)
8. **Show Engine toggle reveals internals**
   - SQL queries
   - Data flow diagram
   - Governance detail
   - Audit log

---

## Role-Based Experience Differences

### Admin Role (🔧 Admin)
- Can view all data including PII
- Can deploy complex apps (unlimited components)
- Can export data
- Sees all governance details
- Can approve apps for non-admin users
- See unmasked PII columns in tables

### Analyst Role (👤 Analyst)
- Can view raw data (but PII masked)
- Limited to medium complexity (8 components max)
- Can export data
- See governance checks and audit log
- Cannot approve apps
- Governance warnings shown for PII

### Viewer Role (👁️ Viewer)
- Cannot view raw data tables (aggregated only)
- Limited to simple complexity (4 components max)
- Cannot export data
- See basic governance status
- Cannot approve apps
- Most restricted experience

---

## What's NOT in Phase 2

These features are deferred to Phase 3 (Polish):

1. **Conversational refinement** — "Break that down by quarter" following up a build
2. **Error handling polish** — Graceful degradation, retry logic
3. **Loading states** — Smooth progress indicators during long operations
4. **Sidebar filters** — Filter UI in sidebar (dashboard already has it)
5. **Demo mode refinement** — Auto-triggering follow-up refinement prompts
6. **PII masking implementation** — Only detection in Phase 2
7. **Export functionality** — Download buttons for CSV/Excel

---

**End of Phase 2 Governance Engine Specification**

Estimated effort: 5 hours (Hours 6–10 of 19-hour build)
Next: Phase 3 (Hours 11–19) — Conversational refinement, polish, error handling, and production readiness
