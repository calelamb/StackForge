"""
Engine view for StackForge.
Shows SQL, data flow, governance checks, audit log.
The "Show Engine" differentiator — reveals what's under the hood.
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional


def render_engine_view(
    app_definition: Dict,
    execution_results: Dict,
    validation: Dict,
    governance: Dict,
) -> None:
    """
    Render 4-tab engine inspection interface.

    Tabs:
    1. Generated SQL — SQL per component
    2. Data Flow — DAG visualization
    3. Governance — Checks and status
    4. Audit Log — History of actions
    """

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍 Generated SQL", "🔀 Data Flow", "✅ Governance", "📝 Audit Log"]
    )

    with tab1:
        _render_sql_tab(app_definition, execution_results)

    with tab2:
        _render_data_flow_tab(app_definition, execution_results)

    with tab3:
        _render_governance_tab(governance, validation)

    with tab4:
        _render_audit_log_tab()


# ============================================================================
# TAB 1: GENERATED SQL
# ============================================================================


def _render_sql_tab(app_definition: Dict, execution_results: Dict):
    """Show generated SQL per component."""
    st.markdown("### Generated SQL Queries")
    st.caption("Each dashboard component is powered by an AI-generated SQL query.")

    components = app_definition.get("components", [])

    if not components:
        st.info("No components — generate a dashboard first.")
        return

    for component in components:
        comp_id = component.get("id", "")
        title = component.get("title", comp_id)
        sql = component.get("generated_sql", "-- No SQL generated")
        comp_type = component.get("type", "unknown")

        icon_map = {
            "kpi": "🎯", "bar": "📊", "line": "📈", "pie": "🥧",
            "scatter": "🔵", "area": "📊", "table": "📋", "metric": "🎯",
        }
        icon = icon_map.get(comp_type, "📦")

        with st.expander(f"{icon} {title} ({comp_type})", expanded=False):
            st.code(sql, language="sql")

            # Show result summary if available
            if comp_id in execution_results:
                result_df = execution_results[comp_id]
                st.caption(
                    f"Result: {len(result_df)} rows × {len(result_df.columns)} columns"
                )
                with st.expander("Preview data"):
                    st.dataframe(result_df.head(10), use_container_width=True)


# ============================================================================
# TAB 2: DATA FLOW
# ============================================================================


def _render_data_flow_tab(app_definition: Dict, execution_results: Dict):
    """Show data flow DAG (text-based)."""
    st.markdown("### Data Flow Diagram")
    st.caption("How data flows from source through filters to dashboard components.")

    source = app_definition.get("data_source", "supply_chain (DuckDB)")
    filters = app_definition.get("filters", [])
    components = app_definition.get("components", [])

    # Build text DAG
    dag_lines = []
    dag_lines.append(f"📁 Source: {source}")
    dag_lines.append("   │")

    if filters:
        filter_names = ", ".join(f.get("label", f.get("id", "?")) for f in filters)
        dag_lines.append(f"   ├── 🔍 Filters: [{filter_names}]")
        dag_lines.append("   │")

    dag_lines.append("   ├── 🧠 AI Intent Parser (GPT-5.1 Function Calling)")
    dag_lines.append("   │       └── Natural Language → Structured App Definition")
    dag_lines.append("   │")
    dag_lines.append("   ├── ⚡ SQL Executor (DuckDB)")
    dag_lines.append("   │       └── App Definition → SQL Queries → DataFrames")
    dag_lines.append("   │")
    dag_lines.append("   └── 📊 Dashboard Components:")

    icon_map = {
        "kpi": "🎯", "bar": "📊", "line": "📈", "pie": "🥧",
        "scatter": "🔵", "area": "📊", "table": "📋", "metric": "🎯",
    }

    for i, comp in enumerate(components):
        icon = icon_map.get(comp.get("type"), "📦")
        title = comp.get("title", "Untitled")
        comp_type = comp.get("type", "unknown")
        prefix = "       ├──" if i < len(components) - 1 else "       └──"

        # Row count from execution results
        comp_id = comp.get("id", "")
        row_info = ""
        if comp_id in execution_results:
            row_info = f" ({len(execution_results[comp_id])} rows)"

        dag_lines.append(f"{prefix} {icon} {title} [{comp_type}]{row_info}")

    dag_text = "\n".join(dag_lines)

    st.markdown(
        f'<div class="data-flow-box">{dag_text}</div>',
        unsafe_allow_html=True,
    )


# ============================================================================
# TAB 3: GOVERNANCE
# ============================================================================


def _render_governance_tab(governance: Dict, validation: Dict):
    """Show governance checks and validation status."""
    st.markdown("### Governance & Compliance")

    checks = governance.get("checks", [])
    if not checks:
        st.info("No governance checks run yet. Generate a dashboard first.")
        return

    # Count pass/fail
    passed = sum(1 for c in checks if c.get("passed", c.get("status") == "pass"))
    total = len(checks)

    status = "pass" if passed == total else "fail"
    if passed == total:
        status_text = f"✅ All Checks Passed ({passed}/{total})"
    else:
        status_text = f"⚠️ {total - passed} Issue(s) Found ({passed}/{total} passed)"

    st.markdown(
        f"""
        <div class="governance-status-banner {status}">
            <span class="governance-status-text {status}">{status_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Individual checks
    for check in checks:
        is_pass = check.get("passed", check.get("status") == "pass")
        icon = "✅" if is_pass else "❌"
        check_name = check.get("name", check.get("rule", "Unknown Check"))
        message = check.get("message", "")
        details = check.get("details", "")

        with st.expander(f"{icon} {check_name}"):
            if is_pass:
                st.success(message)
            else:
                st.error(message)

            if details:
                st.markdown("**Details:**")
                if isinstance(details, str):
                    try:
                        st.code(json.dumps(json.loads(details), indent=2), language="json")
                    except (json.JSONDecodeError, TypeError):
                        st.code(details)
                else:
                    st.code(json.dumps(details, indent=2), language="json")

    # Validation (if available)
    val_checks = validation.get("checks", [])
    if val_checks:
        st.markdown("---")
        st.markdown("#### Data Validation")
        for vc in val_checks:
            icon = "✅" if vc.get("passed") else "❌"
            st.caption(f"{icon} {vc.get('check', 'Unknown')}")


# ============================================================================
# TAB 4: AUDIT LOG
# ============================================================================


def _render_audit_log_tab():
    """Show audit log in reverse chronological order."""
    st.markdown("### Audit Log")
    st.caption("Every action is logged for compliance and transparency.")

    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    audit_log = st.session_state.audit_log

    if not audit_log:
        st.info("No audit entries yet. Actions will appear here as you use the app.")
        return

    for entry in reversed(audit_log):
        timestamp = entry.get("timestamp", "")
        action = entry.get("action", "Unknown")
        role = entry.get("role", "system")
        details = entry.get("details", "")

        st.markdown(
            f"""
            <div class="audit-entry">
                <div class="audit-timestamp">{timestamp}</div>
                <div class="audit-action">{action}</div>
                <div class="audit-details">Role: {role} | {details}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================================
# AUDIT HELPER
# ============================================================================


def add_audit_entry(action: str, details: str = "", role: Optional[str] = None):
    """Add an entry to the audit log."""
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    st.session_state.audit_log.append(
        {
            "timestamp": timestamp,
            "action": action,
            "details": details,
            "role": role or st.session_state.get("current_role", "system"),
        }
    )
