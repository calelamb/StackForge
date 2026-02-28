"""
StackForge Main Application
AI Data App Factory — Build dashboards with natural language

This is the main Streamlit entry point.
Person 2 owns this file.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Optional
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from ui.styles import inject_custom_css
from ui.chat import (
    render_chat_interface,
    add_assistant_message,
    add_user_message,
)
from ui.dashboard import render_dashboard
from ui.engine_view import render_engine_view, add_audit_entry


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="StackForge — AI Data App Factory",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css(st)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "db_conn": None,
        "current_app": None,
        "execution_results": {},
        "validation": {"status": "pending", "checks": []},
        "governance": {"checks": []},
        "current_role": "analyst",
        "show_engine": False,
        "messages": [],
        "audit_log": [],
        "demo_mode": False,
        "demo_step": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============================================================================
# MOCK DATA — Full supplier performance dashboard
# ============================================================================


def get_mock_app_definition() -> Dict:
    """Return a mock app_definition for the Supplier Performance dashboard."""
    return {
        "id": "supplier-perf-001",
        "name": "Supplier Performance Dashboard",
        "data_source": "supply_chain (DuckDB in-memory)",
        "description": "Analyze supplier defect rates, delivery performance, and regional distribution.",
        "filters": [
            {
                "id": "region_filter",
                "type": "multiselect",
                "label": "Region",
                "options": [
                    "North America",
                    "Europe",
                    "Asia Pacific",
                    "Latin America",
                    "Africa",
                ],
            },
            {
                "id": "category_filter",
                "type": "multiselect",
                "label": "Category",
                "options": [
                    "Hardware",
                    "Materials",
                    "Electronics",
                    "Mechanical",
                    "Assembly",
                ],
            },
        ],
        "components": [
            {
                "id": "total_orders",
                "type": "kpi",
                "title": "Total Orders",
                "width": 0.33,
                "config": {"format": "number"},
                "generated_sql": "SELECT COUNT(*) as total_orders FROM supply_chain",
            },
            {
                "id": "avg_defect_rate",
                "type": "kpi",
                "title": "Avg Defect Rate",
                "width": 0.33,
                "config": {"format": "percentage"},
                "generated_sql": "SELECT ROUND(AVG(defect_rate), 2) as avg_defect FROM supply_chain",
            },
            {
                "id": "on_time_delivery",
                "type": "kpi",
                "title": "On-Time Delivery",
                "width": 0.33,
                "config": {"format": "percentage"},
                "generated_sql": "SELECT ROUND(AVG(on_time_delivery) * 100, 1) as on_time_pct FROM supply_chain",
            },
            {
                "id": "defect_by_supplier",
                "type": "bar",
                "title": "Defect Rate by Supplier",
                "width": 0.5,
                "config": {
                    "x_column": "supplier",
                    "y_column": "avg_defect",
                    "threshold": 3.0,
                },
                "generated_sql": "SELECT supplier, ROUND(AVG(defect_rate), 2) as avg_defect FROM supply_chain GROUP BY supplier ORDER BY avg_defect DESC",
            },
            {
                "id": "delivery_trends",
                "type": "line",
                "title": "Monthly Delivery Trends",
                "width": 0.5,
                "config": {
                    "x_column": "month",
                    "y_column": "on_time_pct",
                },
                "generated_sql": "SELECT strftime(order_date, '%Y-%m') as month, ROUND(AVG(on_time_delivery) * 100, 1) as on_time_pct FROM supply_chain GROUP BY month ORDER BY month",
            },
            {
                "id": "orders_by_region",
                "type": "pie",
                "title": "Orders by Region",
                "width": 0.5,
                "config": {
                    "labels_column": "region",
                    "values_column": "order_count",
                },
                "generated_sql": "SELECT region, COUNT(*) as order_count FROM supply_chain GROUP BY region",
            },
            {
                "id": "cost_vs_defect",
                "type": "scatter",
                "title": "Unit Cost vs Defect Rate",
                "width": 0.5,
                "config": {
                    "x_column": "unit_cost",
                    "y_column": "defect_rate",
                },
                "generated_sql": "SELECT unit_cost, defect_rate FROM supply_chain",
            },
            {
                "id": "supplier_details",
                "type": "table",
                "title": "Supplier Detail Table",
                "width": 1.0,
                "config": {"row_limit": 20},
                "generated_sql": "SELECT supplier, region, category, ROUND(AVG(defect_rate),2) as avg_defect, ROUND(AVG(on_time_delivery)*100,1) as on_time_pct, COUNT(*) as orders FROM supply_chain GROUP BY supplier, region, category ORDER BY avg_defect DESC",
            },
        ],
    }


def get_mock_execution_results() -> Dict[str, pd.DataFrame]:
    """Return mock execution results with realistic supply chain data."""
    return {
        "total_orders": pd.DataFrame({"total_orders": [500]}),
        "avg_defect_rate": pd.DataFrame({"avg_defect": [2.48]}),
        "on_time_delivery": pd.DataFrame({"on_time_pct": [80.4]}),
        "defect_by_supplier": pd.DataFrame(
            {
                "supplier": [
                    "Acme Corp",
                    "BuildRight Inc",
                    "Global Parts Ltd",
                    "Superior Materials",
                    "Reliable Suppliers Co",
                ],
                "avg_defect": [3.12, 2.85, 2.61, 2.34, 1.98],
            }
        ),
        "delivery_trends": pd.DataFrame(
            {
                "month": [
                    "2024-01", "2024-02", "2024-03", "2024-04",
                    "2024-05", "2024-06", "2024-07", "2024-08",
                    "2024-09", "2024-10", "2024-11", "2024-12",
                ],
                "on_time_pct": [
                    76.5, 78.2, 79.8, 80.5,
                    81.2, 82.1, 83.5, 82.8,
                    81.9, 80.7, 81.3, 82.6,
                ],
            }
        ),
        "orders_by_region": pd.DataFrame(
            {
                "region": [
                    "North America", "Europe", "Asia Pacific",
                    "Latin America", "Africa",
                ],
                "order_count": [142, 118, 126, 72, 42],
            }
        ),
        "cost_vs_defect": pd.DataFrame(
            {
                "unit_cost": [
                    15.5, 28.3, 42.1, 55.8, 67.2, 78.9, 12.4,
                    33.6, 49.7, 61.3, 85.2, 22.8, 38.5, 71.6,
                    93.4, 18.7, 45.2, 59.8, 74.1, 88.6,
                ],
                "defect_rate": [
                    1.2, 2.8, 0.9, 3.5, 1.8, 4.2, 0.5,
                    2.1, 3.8, 1.5, 4.9, 1.0, 2.5, 3.1,
                    4.5, 0.8, 2.3, 3.7, 1.9, 4.1,
                ],
            }
        ),
        "supplier_details": pd.DataFrame(
            {
                "supplier": [
                    "Acme Corp", "Acme Corp", "BuildRight Inc",
                    "BuildRight Inc", "Global Parts Ltd",
                    "Global Parts Ltd", "Superior Materials",
                    "Superior Materials", "Reliable Suppliers Co",
                    "Reliable Suppliers Co",
                ],
                "region": [
                    "North America", "Europe", "Asia Pacific",
                    "North America", "Europe", "Latin America",
                    "Asia Pacific", "Africa", "North America",
                    "Latin America",
                ],
                "category": [
                    "Hardware", "Electronics", "Materials",
                    "Mechanical", "Assembly", "Hardware",
                    "Electronics", "Materials", "Mechanical",
                    "Assembly",
                ],
                "avg_defect": [3.45, 2.78, 3.12, 2.58, 2.91, 2.31, 2.67, 2.01, 1.89, 2.07],
                "on_time_pct": [75.0, 78.5, 80.2, 83.1, 77.8, 85.4, 81.6, 88.2, 90.1, 86.7],
                "orders": [52, 48, 55, 43, 47, 38, 51, 32, 44, 36],
            }
        ),
    }


def get_mock_governance() -> Dict:
    """Return mock governance check results."""
    return {
        "status": "pass",
        "checks": [
            {
                "name": "PII Detection",
                "passed": True,
                "message": "No PII patterns detected in SQL queries",
                "details": json.dumps({"scanned_queries": 8, "pii_found": 0}),
            },
            {
                "name": "Access Control",
                "passed": True,
                "message": "Role permissions validated — analyst can view aggregated data",
                "details": json.dumps({"role": "analyst", "access_level": "aggregated"}),
            },
            {
                "name": "Query Complexity",
                "passed": True,
                "message": "Component count within limits (8 of 8 max)",
                "details": json.dumps({"components": 8, "limit": 8, "role": "analyst"}),
            },
            {
                "name": "Data Quality",
                "passed": True,
                "message": "No SELECT * anti-patterns detected",
                "details": json.dumps({"select_star_count": 0}),
            },
            {
                "name": "Export Control",
                "passed": True,
                "message": "Export permission granted for analyst role",
                "details": json.dumps({"role": "analyst", "can_export": True}),
            },
            {
                "name": "Audit Trail",
                "passed": True,
                "message": "Audit logging is active for all actions",
                "details": json.dumps({"logging_enabled": True}),
            },
        ],
    }


def get_mock_validation() -> Dict:
    """Return mock validation results."""
    return {
        "status": "valid",
        "checks": [
            {"check": "SQL Syntax", "passed": True},
            {"check": "Schema Validation", "passed": True},
            {"check": "Data Types", "passed": True},
            {"check": "Result Completeness", "passed": True},
        ],
    }


# ============================================================================
# PROCESS PROMPT (mock pipeline → real engine later)
# ============================================================================


def _process_prompt(prompt: str, is_refinement: bool = False):
    """
    Main pipeline: parse → execute → validate → govern → respond.
    Currently uses mock data. Replace with Person 1's engine later.
    """
    add_user_message(prompt)

    with st.spinner("🧠 Building your dashboard..."):
        import time
        time.sleep(1.5)  # Simulate AI processing

    # Build mock app
    mock_app = get_mock_app_definition()
    st.session_state.current_app = mock_app
    st.session_state.execution_results = get_mock_execution_results()
    st.session_state.validation = get_mock_validation()
    st.session_state.governance = get_mock_governance()

    # Compose response
    num_components = len(mock_app.get("components", []))
    num_filters = len(mock_app.get("filters", []))

    if is_refinement:
        response = (
            f"✅ Dashboard refined! Updated to {num_components} components "
            f"with {num_filters} filters. Check the updated view."
        )
    else:
        response = (
            f"✅ Built **{mock_app['name']}** with {num_components} components "
            f"and {num_filters} interactive filters. Explore the dashboard, "
            f"toggle **Show Engine** to see the SQL, or refine with another prompt."
        )

    add_audit_entry(
        "Dashboard Created" if not is_refinement else "Dashboard Refined",
        f"Prompt: {prompt[:80]}... | {num_components} components",
        st.session_state.current_role,
    )

    add_assistant_message(response, app_summary={"name": mock_app["name"], "components": num_components})


# ============================================================================
# HEADER & CONTROLS
# ============================================================================

col_title, col_role, col_engine, col_demo, col_reset = st.columns([2.5, 1.5, 0.8, 0.6, 0.6])

with col_title:
    st.markdown(
        '<h1 class="header-title">🏭 StackForge</h1>'
        '<p class="header-subtitle">AI-Powered Data App Factory</p>',
        unsafe_allow_html=True,
    )

with col_role:
    new_role = st.radio(
        "Role",
        options=["admin", "analyst", "viewer"],
        index=["admin", "analyst", "viewer"].index(st.session_state.current_role),
        horizontal=True,
        label_visibility="collapsed",
    )
    if new_role != st.session_state.current_role:
        st.session_state.current_role = new_role
        add_audit_entry("Role Changed", f"Switched to {new_role}")

with col_engine:
    st.session_state.show_engine = st.toggle(
        "🔧 Engine",
        value=st.session_state.show_engine,
    )

with col_demo:
    if st.button("🎬 Demo", use_container_width=True):
        st.session_state.demo_mode = True
        st.session_state.demo_step = 0

with col_reset:
    if st.button("🔄 Reset", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key != "db_conn":
                del st.session_state[key]
        init_session_state()
        st.rerun()


# ============================================================================
# DEMO MODE
# ============================================================================

if st.session_state.demo_mode and st.session_state.demo_step == 0:
    st.session_state.demo_step = 1
    _process_prompt(
        "Create a supplier performance dashboard with KPIs for total orders, "
        "average defect rate, and on-time delivery percentage. Include a bar chart "
        "of defect rate by supplier, a line chart of delivery trends, a pie chart "
        "of orders by region, a scatter plot of cost vs defect, and a full supplier "
        "details table. Add filters for region and category."
    )
    st.rerun()


# ============================================================================
# MAIN LAYOUT: CHAT | DASHBOARD
# ============================================================================

col_chat, col_dashboard = st.columns([0.35, 0.65], gap="medium")

with col_chat:
    st.markdown("### 💬 Chat")
    user_input = render_chat_interface()

    if user_input:
        is_refine = len(st.session_state.messages) > 0
        _process_prompt(user_input, is_refinement=is_refine)
        st.rerun()

with col_dashboard:
    if st.session_state.show_engine and st.session_state.current_app:
        tab_dash, tab_engine = st.tabs(["📊 Dashboard", "⚙️ Engine"])

        with tab_dash:
            render_dashboard(
                st.session_state.current_app,
                st.session_state.execution_results,
                st.session_state.current_role,
            )

        with tab_engine:
            render_engine_view(
                st.session_state.current_app,
                st.session_state.execution_results,
                st.session_state.validation,
                st.session_state.governance,
            )
    else:
        render_dashboard(
            st.session_state.current_app,
            st.session_state.execution_results,
            st.session_state.current_role,
        )


# ============================================================================
# SIDEBAR: GOVERNANCE + INFO PANELS
# ============================================================================

st.sidebar.markdown("---")

# Governance Panel
if st.session_state.current_app:
    st.sidebar.markdown("### ✅ Governance Status")
    gov_checks = st.session_state.governance.get("checks", [])
    passed = sum(1 for c in gov_checks if c.get("passed"))
    total = len(gov_checks)

    if passed == total:
        st.sidebar.success(f"All {total} checks passed")
    else:
        st.sidebar.warning(f"{passed}/{total} checks passed")

    for check in gov_checks:
        icon = "✅" if check.get("passed") else "⚠️"
        st.sidebar.caption(f"{icon} {check.get('name', 'Check')}")

    st.sidebar.markdown("---")

# Dataset Info
if st.session_state.current_app:
    st.sidebar.markdown("### 📊 App Info")
    st.sidebar.caption(f"**Source:** {st.session_state.current_app.get('data_source', 'Unknown')}")
    components = st.session_state.current_app.get("components", [])
    st.sidebar.caption(f"**Components:** {len(components)}")
    filters = st.session_state.current_app.get("filters", [])
    st.sidebar.caption(f"**Filters:** {len(filters)}")
    st.sidebar.markdown("---")

# Role Info
st.sidebar.markdown("### 👤 Current Role")
role_labels = {"admin": "🔑 Administrator", "analyst": "📊 Data Analyst", "viewer": "👁️ Viewer"}
st.sidebar.caption(role_labels.get(st.session_state.current_role, st.session_state.current_role))

# Recent Audit Entries
st.sidebar.markdown("### 📝 Recent Activity")
if st.session_state.audit_log:
    for entry in st.session_state.audit_log[-5:]:
        st.sidebar.caption(f"**{entry['action']}** — {entry['timestamp']}")
else:
    st.sidebar.caption("No activity yet")
