# PERSON 2 — THE INTERFACE
## StackForge UI Layer PRD | HackUSU 2026 (19-hour Hackathon)

---

## SECTION 1: CLAUDE CODE KICKOFF PROMPT

**Copy and paste this entire prompt into your Claude Code instance:**

```
YOU ARE PERSON 2 — THE INTERFACE LAYER FOR STACKFORGE

PROJECT: StackForge — AI Data App Factory
- A Streamlit app where users describe dashboards in chat, Claude builds them
- YOUR ROLE: Build the entire UI/visualization layer
- HACKATHON: HackUSU 2026 (19 hours total)

YOUR OWNERSHIP:
✅ app.py (main entry point, session management, orchestration)
✅ ui/chat.py (chat interface, template selector, message handling)
✅ ui/dashboard.py (all chart rendering: KPI, bar, line, pie, scatter, area, table)
✅ ui/engine_view.py (SQL view, data flow DAG, governance panel, audit log)
✅ ui/styles.py (dark theme CSS, custom component styling)

YOUR CONSTRAINTS:
❌ Do NOT touch engine/ folder — Person 1 owns engine, intent parsing, SQL generation
❌ Do NOT build governance logic deeply — Person 3 owns that
✅ DO build the UI to DISPLAY governance checks (from Person 3)

THE CONTRACT:
- Person 1's engine outputs: app_definition JSON (see Section 4 schema)
- Person 2 (YOU) consume app_definition and render it beautifully
- Person 3 adds governance checks to the execution flow

START WITH MOCK DATA:
- You do NOT need Person 1's engine working to build beautiful charts
- Hardcode a sample app_definition JSON (see Section 3)
- Build all rendering against mock data
- Later (hour 5+): Replace mocks with real data from Person 1's engine
- This allows parallel development

YOUR TECH STACK:
- Streamlit (UI framework)
- Plotly (charts — use plotly_dark template, transparent bg)
- Pandas (data manipulation)
- JSON (config format)

FOLLOW THIS PRD EXACTLY:
- Section 2: Complete code for all 5 files (styles.py, chat.py, dashboard.py, engine_view.py, app.py)
- Section 3: Mock data to start with
- Section 4: Integration contract (app_definition schema)
- Section 5: Timeline and milestones
- Section 6: Testing checklist

KEY DELIVERABLES:
1. Beautiful dark theme (Streamlit dark + custom CSS)
2. All 8 chart types rendering correctly
3. Chat interface with template selector
4. Dashboard layout logic (responsive grid by component width)
5. Engine view tabs (SQL, data flow, governance, audit)
6. Role toggle (admin/analyst/viewer) affecting visibility
7. Demo mode (auto-send 2 prompts on startup)
8. Filters working (multiselect, date range, number range)

NOW: Read Section 2 and start implementing the code files in order:
1. ui/styles.py — custom CSS
2. ui/chat.py — chat rendering
3. ui/dashboard.py — all chart types
4. ui/engine_view.py — engine inspection
5. app.py — orchestration

Good luck!
```

---

## SECTION 2: THE PRD — COMPLETE CODE

### 2.1: `ui/styles.py` — Full Custom CSS

```python
"""
Custom CSS and styling for StackForge UI.
Dark theme with gradient headers, custom cards, badges.
"""

CUSTOM_CSS = """
<style>
:root {
    --primary-bg: #0f172a;
    --secondary-bg: #1e293b;
    --tertiary-bg: #334155;
    --accent-indigo: #6366f1;
    --accent-slate: #475569;
    --text-primary: #e2e8f0;
    --text-secondary: #cbd5e1;
    --border-color: #334155;
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
}

body, .main {
    background-color: var(--primary-bg) !important;
    color: var(--text-primary) !important;
}

/* Header gradient text */
.header-title {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
}

.header-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin: 0.5rem 0 0 0;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.kpi-label {
    font-size: 0.85rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
}

.kpi-change {
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.kpi-change.positive {
    color: var(--success);
}

.kpi-change.negative {
    color: var(--danger);
}

/* Governance Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.badge-green {
    background-color: rgba(34, 197, 94, 0.2);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.4);
}

.badge-yellow {
    background-color: rgba(245, 158, 11, 0.2);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.4);
}

.badge-red {
    background-color: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.4);
}

/* Chat messages */
.chat-message {
    border-radius: 12px;
    padding: 1rem;
    margin: 0.5rem 0;
    font-size: 0.95rem;
    line-height: 1.5;
}

.chat-message.user {
    background-color: rgba(99, 102, 241, 0.15);
    border-left: 3px solid var(--accent-indigo);
    margin-left: 2rem;
}

.chat-message.assistant {
    background-color: rgba(71, 85, 105, 0.1);
    border-left: 3px solid var(--accent-slate);
    margin-right: 2rem;
}

.chat-role {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.25rem;
    opacity: 0.8;
}

.user .chat-role {
    color: var(--accent-indigo);
}

.assistant .chat-role {
    color: var(--accent-slate);
}

/* Template cards */
.template-card {
    background-color: var(--secondary-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.template-card:hover {
    border-color: var(--accent-indigo);
    background-color: rgba(99, 102, 241, 0.05);
    transform: translateY(-2px);
}

.template-icon {
    font-size: 2rem;
}

.template-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}

.template-description {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0;
    flex-grow: 1;
}

.template-governance {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.template-button {
    background-color: var(--accent-indigo);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-top: auto;
}

.template-button:hover {
    background-color: #5558e3;
    transform: translateX(2px);
}

/* Engine view code blocks */
.engine-sql-block {
    background-color: var(--tertiary-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    overflow-x: auto;
    color: var(--text-primary);
    line-height: 1.4;
}

.engine-sql-header {
    font-weight: 700;
    color: var(--accent-indigo);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    font-size: 0.8rem;
}

/* Data flow DAG */
.data-flow-box {
    background-color: var(--secondary-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
}

.data-flow-source {
    color: var(--accent-indigo);
    font-weight: 600;
}

.data-flow-arrow {
    color: var(--text-secondary);
}

.data-flow-component {
    color: var(--text-primary);
    font-weight: 600;
}

/* Governance status */
.governance-status-banner {
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.governance-status-banner.pass {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%);
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.governance-status-banner.fail {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.governance-status-text {
    font-size: 1rem;
    font-weight: 600;
}

.governance-status-text.pass {
    color: var(--success);
}

.governance-status-text.fail {
    color: var(--danger);
}

/* Governance check row */
.governance-check-row {
    background-color: var(--secondary-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.governance-check-name {
    font-weight: 600;
    color: var(--text-primary);
}

.governance-check-icon {
    font-size: 1.25rem;
    margin-left: 1rem;
}

/* Audit log */
.audit-entry {
    background-color: var(--secondary-bg);
    border-left: 3px solid var(--accent-indigo);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
}

.audit-timestamp {
    color: var(--text-secondary);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.audit-action {
    color: var(--text-primary);
    font-weight: 600;
    margin: 0.25rem 0;
}

.audit-details {
    color: var(--text-secondary);
    font-size: 0.8rem;
    margin: 0.25rem 0;
}

/* Sidebar panels */
.sidebar-panel {
    background-color: var(--secondary-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.sidebar-title {
    font-size: 0.9rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-secondary);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.sidebar-item {
    font-size: 0.9rem;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    padding: 0.5rem 0;
}

.sidebar-item-label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
}

/* Role selector */
.role-selector {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.role-button {
    flex: 1;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border-color);
    background-color: var(--tertiary-bg);
    color: var(--text-secondary);
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.role-button.active {
    background-color: var(--accent-indigo);
    color: white;
    border-color: var(--accent-indigo);
}

.role-button:hover:not(.active) {
    border-color: var(--accent-indigo);
    background-color: rgba(99, 102, 241, 0.1);
}

/* Chart container */
.chart-container {
    background-color: var(--secondary-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
}

.chart-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
}

/* Empty state */
.empty-state {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
    border: 2px dashed var(--border-color);
    border-radius: 12px;
    padding: 3rem 2rem;
    text-align: center;
    color: var(--text-secondary);
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.6;
}

.empty-state-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.empty-state-text {
    font-size: 0.95rem;
    line-height: 1.5;
}

/* Loading state */
.loading-spinner {
    text-align: center;
    padding: 2rem;
}

.loading-text {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-top: 1rem;
}

/* Error message */
.error-box {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 8px;
    padding: 1rem;
    color: #fca5a5;
    font-size: 0.9rem;
    line-height: 1.5;
}

/* Expandable section */
.expander-header {
    background-color: var(--secondary-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s ease;
}

.expander-header:hover {
    background-color: rgba(99, 102, 241, 0.05);
    border-color: var(--accent-indigo);
}

.expander-content {
    background-color: var(--tertiary-bg);
    border: 1px solid var(--border-color);
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 1rem;
}

/* Streamlit overrides */
[data-testid="stMetric"] {
    background-color: var(--secondary-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
}

[data-testid="stTab"] {
    background-color: var(--secondary-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
}

.streamlit-expanderHeader {
    background-color: var(--secondary-bg) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

.streamlit-expanderContent {
    background-color: var(--tertiary-bg) !important;
    border-radius: 0 0 8px 8px !important;
}

/* Input fields */
input, select, textarea {
    background-color: var(--tertiary-bg) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 6px !important;
}

input:focus, select:focus, textarea:focus {
    border-color: var(--accent-indigo) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}

/* Button base styles */
button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] button {
    background-color: var(--secondary-bg);
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border-color);
}

.stTabs [aria-selected="true"] {
    background-color: var(--secondary-bg);
    color: var(--accent-indigo);
    border-bottom-color: var(--accent-indigo) !important;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--secondary-bg);
}

::-webkit-scrollbar-thumb {
    background: var(--tertiary-bg);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-slate);
}
</style>
"""

def inject_custom_css(streamlit_obj):
    """Inject custom CSS into Streamlit page."""
    streamlit_obj.markdown(CUSTOM_CSS, unsafe_allow_html=True)
```

---

### 2.2: `ui/chat.py` — Full Chat Interface

```python
"""
Chat interface for StackForge.
Handles message display, user input, and template selection.
"""

import streamlit as st
from typing import List, Dict, Optional, Tuple
import json


def render_chat_interface() -> Optional[str]:
    """
    Render the chat interface.
    Returns user input from st.chat_input if provided, otherwise None.
    """
    # Display existing messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display all messages
    for i, msg in enumerate(st.session_state.messages):
        render_message(msg, msg_id=i)

    # Template selector (only shown when chat is empty)
    if len(st.session_state.messages) == 0:
        render_template_selector()

    # Chat input at bottom
    user_input = st.chat_input("Describe your dashboard or refine the current one...")

    return user_input


def render_message(message: Dict, msg_id: int = 0):
    """Render a single chat message."""
    role = message.get("role", "assistant")
    content = message.get("content", "")
    app_summary = message.get("app_summary")

    with st.container():
        if role == "user":
            st.markdown(
                f"""
                <div class="chat-message user">
                    <div class="chat-role">👤 You</div>
                    <div>{content}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="chat-message assistant">
                    <div class="chat-role">🤖 StackForge</div>
                    <div>{content}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Show app summary if present
        if app_summary:
            with st.expander("📊 Built Dashboard"):
                st.code(json.dumps(app_summary, indent=2), language="json")


def add_assistant_message(content: str, app_summary: Optional[Dict] = None):
    """
    Add an assistant message to chat history.

    Args:
        content: Message text
        app_summary: Optional app_definition JSON that was built
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []

    message = {
        "role": "assistant",
        "content": content,
        "app_summary": app_summary
    }
    st.session_state.messages.append(message)


def add_user_message(content: str):
    """Add a user message to chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    message = {
        "role": "user",
        "content": content
    }
    st.session_state.messages.append(message)


def render_template_selector():
    """
    Render template selector with 6 template cards in 3-column grid.
    Only shown when chat is empty.
    """
    st.markdown("### 📋 Start with a Template")
    st.markdown("Choose a pre-built dashboard template or describe your own.")

    templates = [
        {
            "name": "Supplier Performance",
            "icon": "📦",
            "description": "Track supplier metrics, defect rates, and delivery times",
            "governance": ["policy", "data-quality"],
            "prompt": "Create a supplier performance dashboard with KPIs for total orders, average defect rate, and on-time delivery percentage. Include a bar chart of defect rate by supplier, a line chart of delivery trends, a pie chart of orders by region, and a table of supplier details. Add filters for region and category."
        },
        {
            "name": "Sales Pipeline",
            "icon": "💰",
            "description": "Monitor deals, revenue, and sales team performance",
            "governance": ["policy"],
            "prompt": "Build a sales pipeline dashboard showing total pipeline value, win rate, and average deal size. Include a bar chart of deals by stage, a line chart of revenue trends over time, and a scatter plot of deal size vs. sales rep performance. Add a date range filter."
        },
        {
            "name": "Customer Analytics",
            "icon": "👥",
            "description": "Analyze customer behavior, retention, and lifetime value",
            "governance": ["privacy", "data-quality"],
            "prompt": "Create a customer analytics dashboard with KPIs for total customers, retention rate, and average lifetime value. Include a line chart of new customers over time, a pie chart of customers by segment, and a table of top customers. Add filters for region and segment."
        },
        {
            "name": "Inventory Management",
            "icon": "📊",
            "description": "Track stock levels, turnover rates, and warehouse health",
            "governance": ["policy"],
            "prompt": "Build an inventory management dashboard with KPIs for total stock value, inventory turnover, and stock-out rate. Include a bar chart of stock levels by product category, a line chart of inventory trends, and a table of low-stock items. Add filters for warehouse and category."
        },
        {
            "name": "IT Operations",
            "icon": "🖥️",
            "description": "Monitor system uptime, incidents, and infrastructure health",
            "governance": ["security", "policy"],
            "prompt": "Create an IT operations dashboard with KPIs for uptime percentage, average incident resolution time, and critical incidents. Include a bar chart of incidents by type, a line chart of uptime trends, and a table of open incidents. Add a date range filter."
        },
        {
            "name": "Marketing Campaign",
            "icon": "📢",
            "description": "Track campaign performance, ROI, and audience engagement",
            "governance": ["privacy"],
            "prompt": "Build a marketing campaign dashboard with KPIs for total clicks, conversion rate, and ROI. Include a bar chart of clicks by channel, a line chart of engagement trends over time, and a table of campaign details. Add filters for channel and campaign type."
        }
    ]

    # 3-column grid
    cols = st.columns(3)
    for idx, template in enumerate(templates):
        col = cols[idx % 3]
        with col:
            render_template_card(template)


def render_template_card(template: Dict):
    """Render a single template card."""
    governance_badges = " ".join(
        f'<span class="badge badge-green">{gov}</span>'
        for gov in template.get("governance", [])
    )

    button_html = f"""
    <div class="template-card">
        <div class="template-icon">{template['icon']}</div>
        <h4 class="template-name">{template['name']}</h4>
        <p class="template-description">{template['description']}</p>
        <div class="template-governance">
            {governance_badges}
        </div>
        <button class="template-button" id="template-{template['name']}">
            Use Template →
        </button>
    </div>
    """

    st.markdown(button_html, unsafe_allow_html=True)

    # Clickable button below card
    if st.button(
        "Select",
        key=f"btn-{template['name']}",
        use_container_width=True,
        type="primary"
    ):
        return template["prompt"]

    return None
```

---

### 2.3: `ui/dashboard.py` — Full Dashboard Renderer (THE BIG ONE)

```python
"""
Dashboard rendering for StackForge.
Renders all chart types, KPIs, tables, filters.
Handles responsive layout and dynamic component rendering.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple


def render_dashboard(
    app_definition: Dict,
    execution_results: Dict,
    role: str = "analyst"
) -> Dict:
    """
    Main dashboard renderer.
    Orchestrates layout and renders all components.

    Args:
        app_definition: The app config JSON from Person 1's engine
        execution_results: Query results from Person 1's engine
        role: User role (admin/analyst/viewer)

    Returns:
        Updated execution_results with any filter changes
    """

    # Check if app exists
    if not app_definition or app_definition.get("components") is None:
        _render_empty_state()
        return execution_results

    # Get components and filters
    components = app_definition.get("components", [])
    filters = app_definition.get("filters", [])

    # Render filters in sidebar
    if filters:
        _render_filters(filters, execution_results)

    # Group components into rows based on width
    # width: 1.0 (full), 0.5 (half), 0.33 (third)
    rows = _group_components_by_width(components)

    # Render each row
    for row in rows:
        cols = st.columns(len(row))
        for col, component in zip(cols, row):
            with col:
                _render_component(component, execution_results, role)

    return execution_results


def _render_empty_state():
    """Shown when no app exists yet."""
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">🏭</div>
            <div class="empty-state-title">No Dashboard Yet</div>
            <div class="empty-state-text">
                Start by describing your dashboard in chat or selecting a template.<br>
                StackForge will generate a beautiful dashboard for you.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def _group_components_by_width(components: List[Dict]) -> List[List[Dict]]:
    """
    Group components into rows based on width.
    1.0 = full row, 0.5 = 2 per row, 0.33 = 3 per row
    """
    if not components:
        return []

    rows = []
    current_row = []
    current_width = 0.0

    for component in components:
        width = component.get("width", 1.0)

        # If adding this component exceeds row capacity, start new row
        if current_width + width > 1.01:  # small tolerance
            if current_row:
                rows.append(current_row)
            current_row = [component]
            current_width = width
        else:
            current_row.append(component)
            current_width += width

    # Add final row
    if current_row:
        rows.append(current_row)

    return rows


def _render_filters(filter_defs: List[Dict], execution_results: Dict):
    """
    Render filter widgets in sidebar.
    Supports: select, multiselect, date_range, number_range
    """
    st.sidebar.markdown("### 🔍 Filters")

    for filter_def in filter_defs:
        filter_id = filter_def.get("id", "filter")
        filter_type = filter_def.get("type", "select")
        label = filter_def.get("label", "Filter")

        if filter_type == "select":
            options = filter_def.get("options", [])
            st.sidebar.selectbox(label, options, key=f"filter-{filter_id}")

        elif filter_type == "multiselect":
            options = filter_def.get("options", [])
            st.sidebar.multiselect(label, options, key=f"filter-{filter_id}")

        elif filter_type == "date_range":
            cols = st.sidebar.columns(2)
            with cols[0]:
                st.date_input(f"{label} (Start)", key=f"filter-{filter_id}-start")
            with cols[1]:
                st.date_input(f"{label} (End)", key=f"filter-{filter_id}-end")

        elif filter_type == "number_range":
            cols = st.sidebar.columns(2)
            min_val = filter_def.get("min", 0)
            max_val = filter_def.get("max", 100)
            with cols[0]:
                st.number_input(f"{label} (Min)", min_value=min_val, key=f"filter-{filter_id}-min")
            with cols[1]:
                st.number_input(f"{label} (Max)", max_value=max_val, key=f"filter-{filter_id}-max")


def _render_component(component: Dict, execution_results: Dict, role: str = "analyst"):
    """Route component to correct renderer based on type."""
    comp_type = component.get("type", "")
    title = component.get("title", "")
    config = component.get("config", {})

    # Get data for this component
    comp_id = component.get("id", "")
    df = execution_results.get(comp_id, pd.DataFrame())

    if comp_type == "kpi":
        _render_kpi(title, df, config)
    elif comp_type == "bar":
        _render_bar_chart(title, df, config)
    elif comp_type == "line":
        _render_line_chart(title, df, config)
    elif comp_type == "pie":
        _render_pie_chart(title, df, config)
    elif comp_type == "scatter":
        _render_scatter(title, df, config)
    elif comp_type == "area":
        _render_area_chart(title, df, config)
    elif comp_type == "table":
        _render_table(title, df, config)
    elif comp_type == "metric":
        _render_metric_highlight(title, df, config)
    else:
        st.warning(f"Unknown component type: {comp_type}")


def _render_kpi(title: str, df: pd.DataFrame, config: Dict):
    """
    Render KPI card.
    Formats numbers based on config (currency, percentage, decimal, number).
    """
    if df.empty:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{title}</div>
                <div class="kpi-value">—</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Extract value (first row, first column)
    value = df.iloc[0, 0]

    # Format based on config
    format_type = config.get("format", "number")
    if format_type == "currency":
        formatted = f"${value:,.2f}"
    elif format_type == "percentage":
        formatted = f"{value:.1f}%"
    elif format_type == "decimal":
        formatted = f"{value:.2f}"
    else:  # number
        formatted = f"{value:,.0f}"

    # Get change if present
    change_text = ""
    if "change" in df.columns:
        change_val = df.iloc[0]["change"]
        change_class = "positive" if change_val >= 0 else "negative"
        change_text = f'<div class="kpi-change {change_class}">{"↑" if change_val >= 0 else "↓"} {abs(change_val):.1f}%</div>'

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{formatted}</div>
            {change_text}
        </div>
        """,
        unsafe_allow_html=True
    )


def _render_bar_chart(title: str, df: pd.DataFrame, config: Dict):
    """
    Render Plotly bar chart.
    Supports threshold lines and color grouping.
    """
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    # Determine columns
    x_col = config.get("x_column", df.columns[0])
    y_col = config.get("y_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])
    color_col = config.get("color_column")

    fig = go.Figure()

    if color_col and color_col in df.columns:
        # Grouped bars
        for group in df[color_col].unique():
            group_df = df[df[color_col] == group]
            fig.add_trace(go.Bar(
                x=group_df[x_col],
                y=group_df[y_col],
                name=str(group),
                marker=dict(line=dict(width=0))
            ))
    else:
        # Single series
        fig.add_trace(go.Bar(
            x=df[x_col],
            y=df[y_col],
            marker=dict(
                color="#6366f1",
                line=dict(width=0)
            )
        ))

    # Add threshold line if configured
    threshold = config.get("threshold")
    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="rgba(245, 158, 11, 0.6)",
            annotation_text="Threshold"
        )

    fig.update_layout(
        title=title,
        xaxis_title=config.get("x_label", x_col),
        yaxis_title=config.get("y_label", y_col),
        template="plotly_dark",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_line_chart(title: str, df: pd.DataFrame, config: Dict):
    """
    Render Plotly line chart with markers and unified hover.
    """
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    x_col = config.get("x_column", df.columns[0])
    y_col = config.get("y_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])
    color_col = config.get("color_column")

    fig = go.Figure()

    if color_col and color_col in df.columns:
        # Multiple lines
        for group in df[color_col].unique():
            group_df = df[df[color_col] == group].sort_values(x_col)
            fig.add_trace(go.Scatter(
                x=group_df[x_col],
                y=group_df[y_col],
                mode="lines+markers",
                name=str(group),
                line=dict(width=2),
                marker=dict(size=5)
            ))
    else:
        # Single line
        df_sorted = df.sort_values(x_col)
        fig.add_trace(go.Scatter(
            x=df_sorted[x_col],
            y=df_sorted[y_col],
            mode="lines+markers",
            line=dict(color="#6366f1", width=2),
            marker=dict(size=5, color="#6366f1")
        ))

    fig.update_layout(
        title=title,
        xaxis_title=config.get("x_label", x_col),
        yaxis_title=config.get("y_label", y_col),
        template="plotly_dark",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_pie_chart(title: str, df: pd.DataFrame, config: Dict):
    """Render Plotly pie chart."""
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    labels_col = config.get("labels_column", df.columns[0])
    values_col = config.get("values_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])

    fig = go.Figure(data=[go.Pie(
        labels=df[labels_col],
        values=df[values_col],
        marker=dict(line=dict(color="rgba(15, 23, 42, 1)", width=2))
    )])

    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0")
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_scatter(title: str, df: pd.DataFrame, config: Dict):
    """Render Plotly scatter chart."""
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    x_col = config.get("x_column", df.columns[0])
    y_col = config.get("y_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])
    size_col = config.get("size_column")
    color_col = config.get("color_column")

    fig = go.Figure(data=[go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="markers",
        marker=dict(
            size=df[size_col] if size_col and size_col in df.columns else 8,
            color=df[color_col] if color_col and color_col in df.columns else "#6366f1",
            colorscale="Viridis" if color_col and color_col in df.columns else None,
            line=dict(width=0)
        )
    )])

    fig.update_layout(
        title=title,
        xaxis_title=config.get("x_label", x_col),
        yaxis_title=config.get("y_label", y_col),
        template="plotly_dark",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        hovermode="closest"
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_area_chart(title: str, df: pd.DataFrame, config: Dict):
    """Render Plotly area chart."""
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    x_col = config.get("x_column", df.columns[0])
    y_col = config.get("y_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])
    color_col = config.get("color_column")

    fig = go.Figure()

    if color_col and color_col in df.columns:
        # Stacked areas
        for group in df[color_col].unique():
            group_df = df[df[color_col] == group].sort_values(x_col)
            fig.add_trace(go.Scatter(
                x=group_df[x_col],
                y=group_df[y_col],
                fill="tonexty",
                name=str(group),
                line=dict(width=0)
            ))
    else:
        # Single area
        df_sorted = df.sort_values(x_col)
        fig.add_trace(go.Scatter(
            x=df_sorted[x_col],
            y=df_sorted[y_col],
            fill="tozeroy",
            line=dict(color="#6366f1", width=2)
        ))

    fig.update_layout(
        title=title,
        xaxis_title=config.get("x_label", x_col),
        yaxis_title=config.get("y_label", y_col),
        template="plotly_dark",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_table(title: str, df: pd.DataFrame, config: Dict):
    """
    Render interactive table with optional row limit.
    """
    st.markdown(f"**{title}**")

    # Apply limit if configured
    limit = config.get("row_limit", len(df))
    df_display = df.head(limit)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=400
    )

    if len(df) > limit:
        st.caption(f"Showing {limit} of {len(df)} rows")


def _render_metric_highlight(title: str, df: pd.DataFrame, config: Dict):
    """
    Render data with conditional highlighting based on threshold.
    """
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    value_col = config.get("value_column", df.columns[0])
    threshold = config.get("threshold", 0)

    st.markdown(f"**{title}**")

    for idx, row in df.iterrows():
        value = row[value_col]
        is_above = value >= threshold
        color = "🟢" if is_above else "🔴"
        st.metric(f"{color} {row.get('name', f'Item {idx}')}", f"{value:.2f}")
```

---

### 2.4: `ui/engine_view.py` — Full Engine View with Tabs

```python
"""
Engine view for StackForge.
Shows SQL, data flow, governance checks, audit log.
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional


def render_engine_view(
    app_definition: Dict,
    execution_results: Dict,
    validation: Dict,
    governance: Dict
) -> None:
    """
    Render 4-tab engine inspection interface.

    Tabs:
    1. Generated SQL — SQL per component
    2. Data Flow — DAG visualization
    3. Governance — Checks and status
    4. Audit Log — History of actions
    """

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Generated SQL",
        "🔀 Data Flow",
        "✅ Governance",
        "📝 Audit Log"
    ])

    with tab1:
        _render_sql_tab(app_definition, execution_results)

    with tab2:
        _render_data_flow_tab(app_definition, execution_results)

    with tab3:
        _render_governance_tab(governance, validation)

    with tab4:
        _render_audit_log_tab()


def _render_sql_tab(app_definition: Dict, execution_results: Dict):
    """Show generated SQL per component."""
    st.markdown("### Generated SQL Queries")

    components = app_definition.get("components", [])

    for component in components:
        comp_id = component.get("id", "")
        title = component.get("title", comp_id)
        sql = component.get("generated_sql", "-- No SQL generated")

        with st.expander(f"📊 {title}", expanded=False):
            st.code(sql, language="sql")

            # Show result summary
            if comp_id in execution_results:
                result_df = execution_results[comp_id]
                st.caption(f"Result: {len(result_df)} rows × {len(result_df.columns)} columns")
                with st.expander("Preview"):
                    st.dataframe(result_df.head(10), use_container_width=True)


def _render_data_flow_tab(app_definition: Dict, execution_results: Dict):
    """Show data flow DAG (text-based)."""
    st.markdown("### Data Flow Diagram")

    # Build text DAG
    source = app_definition.get("data_source", "Unknown Source")
    filters = app_definition.get("filters", [])
    components = app_definition.get("components", [])

    dag_lines = [f"📁 {source}"]

    if filters:
        filter_names = " → ".join(f.get("label", f.get("id")) for f in filters)
        dag_lines.append(f"  ↓")
        dag_lines.append(f"🔍 {filter_names}")

    dag_lines.append(f"  ↓")

    for comp in components:
        icon_map = {
            "kpi": "📊",
            "bar": "📊",
            "line": "📈",
            "pie": "🥧",
            "scatter": "🔵",
            "area": "📊",
            "table": "📋",
            "metric": "🎯"
        }
        icon = icon_map.get(comp.get("type"), "📦")
        dag_lines.append(f"{icon} {comp.get('title', 'Untitled')}")

    dag_text = "\n".join(dag_lines)

    st.markdown(
        f"""
        <div class="data-flow-box">
        {dag_text}
        </div>
        """,
        unsafe_allow_html=True
    )


def _render_governance_tab(governance: Dict, validation: Dict):
    """Show governance checks and validation status."""
    st.markdown("### Governance & Compliance")

    # Status banner
    checks = governance.get("checks", [])
    passed = sum(1 for check in checks if check.get("passed", False))
    total = len(checks)

    status = "pass" if passed == total else "fail"
    status_text = f"✅ All Checks Passed ({passed}/{total})" if passed == total else f"⚠️ {total - passed} Issues Found"

    st.markdown(
        f"""
        <div class="governance-status-banner {status}">
            <span class="governance-status-text {status}">{status_text}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Individual checks
    for check in checks:
        icon = "✅" if check.get("passed") else "❌"
        check_name = check.get("name", "Unknown Check")

        with st.expander(f"{icon} {check_name}"):
            if check.get("passed"):
                st.success(f"Passed: {check.get('message', 'Check passed')}")
            else:
                st.error(f"Failed: {check.get('message', 'Check failed')}")

            if check.get("details"):
                st.markdown("**Details:**")
                st.code(check.get("details"), language="json")


def _render_audit_log_tab():
    """Show audit log in reverse chronological order."""
    st.markdown("### Audit Log")

    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    audit_log = st.session_state.audit_log

    if not audit_log:
        st.info("No audit entries yet.")
        return

    # Reverse chronological (newest first)
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
            unsafe_allow_html=True
        )


def add_audit_entry(action: str, details: str = "", role: Optional[str] = None):
    """
    Add an entry to the audit log.

    Args:
        action: Action description (e.g., "Dashboard Created")
        details: Additional details
        role: User role
    """
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "timestamp": timestamp,
        "action": action,
        "details": details,
        "role": role or st.session_state.get("current_role", "system")
    }

    st.session_state.audit_log.append(entry)
```

---

### 2.5: `app.py` — Complete Main Application

```python
"""
StackForge Main Application
AI Data App Factory — Build dashboards with natural language
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
import sys
import os

# Add UI module to path
sys.path.insert(0, os.path.dirname(__file__))

from ui.styles import inject_custom_css, CUSTOM_CSS
from ui.chat import render_chat_interface, add_assistant_message, add_user_message, render_template_selector
from ui.dashboard import render_dashboard
from ui.engine_view import render_engine_view, add_audit_entry


# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="StackForge",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
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
        "demo_step": 0
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============================================================================
# MOCK DATA FOR DEVELOPMENT
# ============================================================================

def get_mock_app_definition() -> Dict:
    """
    Return a mock app_definition for development.
    Represents a Supplier Performance Dashboard.
    """
    return {
        "id": "supplier-perf-001",
        "name": "Supplier Performance Dashboard",
        "data_source": "suppliers_db.suppliers",
        "filters": [
            {
                "id": "region_filter",
                "type": "multiselect",
                "label": "Region",
                "options": ["North America", "Europe", "Asia", "South America"]
            },
            {
                "id": "category_filter",
                "type": "multiselect",
                "label": "Category",
                "options": ["Electronics", "Raw Materials", "Components", "Services"]
            }
        ],
        "components": [
            {
                "id": "total_orders",
                "type": "kpi",
                "title": "Total Orders",
                "width": 0.33,
                "config": {
                    "format": "number"
                },
                "generated_sql": "SELECT COUNT(*) as value FROM orders WHERE status='completed'"
            },
            {
                "id": "avg_defect_rate",
                "type": "kpi",
                "title": "Avg Defect Rate",
                "width": 0.33,
                "config": {
                    "format": "percentage"
                },
                "generated_sql": "SELECT AVG(defect_rate) as value FROM suppliers"
            },
            {
                "id": "on_time_delivery",
                "type": "kpi",
                "title": "On-Time Delivery %",
                "width": 0.33,
                "config": {
                    "format": "percentage"
                },
                "generated_sql": "SELECT (COUNT(CASE WHEN delivery_date <= due_date THEN 1 END) * 100.0 / COUNT(*)) as value FROM orders"
            },
            {
                "id": "defect_by_supplier",
                "type": "bar",
                "title": "Defect Rate by Supplier",
                "width": 0.5,
                "config": {
                    "x_column": "supplier_name",
                    "y_column": "defect_rate",
                    "threshold": 5.0
                },
                "generated_sql": "SELECT supplier_name, defect_rate FROM suppliers ORDER BY defect_rate DESC LIMIT 10"
            },
            {
                "id": "delivery_trends",
                "type": "line",
                "title": "Delivery Trends Over Time",
                "width": 0.5,
                "config": {
                    "x_column": "month",
                    "y_column": "on_time_pct"
                },
                "generated_sql": "SELECT DATE_TRUNC('month', delivery_date) as month, (COUNT(CASE WHEN delivery_date <= due_date THEN 1 END) * 100.0 / COUNT(*)) as on_time_pct FROM orders GROUP BY month ORDER BY month"
            },
            {
                "id": "orders_by_region",
                "type": "pie",
                "title": "Orders by Region",
                "width": 0.5,
                "config": {
                    "labels_column": "region",
                    "values_column": "order_count"
                },
                "generated_sql": "SELECT region, COUNT(*) as order_count FROM suppliers s JOIN orders o ON s.id = o.supplier_id GROUP BY region"
            },
            {
                "id": "supplier_details",
                "type": "table",
                "title": "Supplier Details",
                "width": 1.0,
                "config": {
                    "row_limit": 20
                },
                "generated_sql": "SELECT supplier_name, region, category, defect_rate, on_time_pct FROM suppliers ORDER BY defect_rate DESC"
            }
        ]
    }


def get_mock_execution_results() -> Dict[str, pd.DataFrame]:
    """Return mock execution results with sample data."""
    return {
        "total_orders": pd.DataFrame({"value": [1250]}),

        "avg_defect_rate": pd.DataFrame({"value": [4.2]}),

        "on_time_delivery": pd.DataFrame({"value": [87.3]}),

        "defect_by_supplier": pd.DataFrame({
            "supplier_name": ["Acme Corp", "TechSupply Inc", "Global Parts", "Quality First", "Reliable Co", "FastShip Ltd", "EuroSupply", "AsiaParts", "NorthAm Pro", "SouthPacific"],
            "defect_rate": [8.5, 7.2, 6.1, 5.8, 5.2, 4.9, 4.5, 3.8, 3.2, 2.1]
        }),

        "delivery_trends": pd.DataFrame({
            "month": pd.date_range(start="2024-01-01", periods=12, freq="MS"),
            "on_time_pct": [78.5, 81.2, 83.1, 85.0, 86.2, 87.1, 88.3, 89.1, 88.5, 87.8, 87.5, 88.9]
        }),

        "orders_by_region": pd.DataFrame({
            "region": ["North America", "Europe", "Asia", "South America"],
            "order_count": [450, 320, 380, 100]
        }),

        "supplier_details": pd.DataFrame({
            "supplier_name": ["Acme Corp", "TechSupply Inc", "Global Parts", "Quality First", "Reliable Co", "FastShip Ltd", "EuroSupply", "AsiaParts", "NorthAm Pro", "SouthPacific"],
            "region": ["North America", "Europe", "Asia", "North America", "South America", "Europe", "Europe", "Asia", "North America", "South America"],
            "category": ["Electronics", "Components", "Raw Materials", "Services", "Components", "Electronics", "Raw Materials", "Components", "Services", "Electronics"],
            "defect_rate": [8.5, 7.2, 6.1, 5.8, 5.2, 4.9, 4.5, 3.8, 3.2, 2.1],
            "on_time_pct": [75.0, 78.0, 82.0, 85.0, 87.0, 88.0, 89.0, 91.0, 92.0, 94.0]
        })
    }


def get_mock_governance() -> Dict:
    """Return mock governance check results."""
    return {
        "status": "pass",
        "checks": [
            {
                "name": "Data Classification Check",
                "passed": True,
                "message": "All data classified correctly",
                "details": json.dumps({"rule": "check_classification", "tables": 7})
            },
            {
                "name": "Privacy Compliance",
                "passed": True,
                "message": "No PII exposed in results",
                "details": json.dumps({"rule": "check_pii", "pii_found": 0})
            },
            {
                "name": "Access Control",
                "passed": True,
                "message": "Role permissions validated",
                "details": json.dumps({"rule": "check_permissions", "role": "analyst"})
            }
        ]
    }


def get_mock_validation() -> Dict:
    """Return mock validation results."""
    return {
        "status": "valid",
        "checks": [
            {"check": "SQL Syntax", "passed": True},
            {"check": "Schema Validation", "passed": True},
            {"check": "Data Types", "passed": True}
        ]
    }


# ============================================================================
# MAIN LOGIC
# ============================================================================

def _process_prompt(prompt: str, is_refinement: bool = False) -> str:
    """
    Main pipeline: parse → execute → validate → govern → respond

    In real implementation, this calls Person 1's engine.
    For now, it returns a mock response and builds a mock app_definition.
    """
    add_user_message(prompt)

    # Simulate processing
    with st.spinner("Building your dashboard..."):
        import time
        time.sleep(1)

    # Mock response
    if is_refinement:
        response = "✅ Dashboard refined! I've added your requested changes."
    else:
        response = "✅ Created Supplier Performance Dashboard! Check out the metrics above. You can refine it by describing what you'd like to change."

    # Mock app_definition
    mock_app = get_mock_app_definition()
    st.session_state.current_app = mock_app
    st.session_state.execution_results = get_mock_execution_results()
    st.session_state.validation = get_mock_validation()
    st.session_state.governance = get_mock_governance()

    # Add to audit
    add_audit_entry(
        "Dashboard Created" if not is_refinement else "Dashboard Refined",
        f"Prompt: {prompt[:50]}...",
        st.session_state.current_role
    )

    add_assistant_message(response, app_summary=mock_app)

    return response


# ============================================================================
# HEADER & CONTROLS
# ============================================================================

col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 0.8, 0.8])

with col1:
    st.markdown(
        '<h1 class="header-title">🏭 StackForge</h1>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown("**Role**")
    new_role = st.radio(
        "Select Role",
        options=["admin", "analyst", "viewer"],
        horizontal=True,
        label_visibility="collapsed"
    )
    if new_role != st.session_state.current_role:
        st.session_state.current_role = new_role
        add_audit_entry("Role Changed", f"Switched to {new_role}")

with col3:
    st.markdown("**View**")
    st.session_state.show_engine = st.checkbox(
        "Show Engine",
        value=st.session_state.show_engine,
        label_visibility="collapsed"
    )

with col4:
    if st.button("🎬 Demo", use_container_width=True):
        st.session_state.demo_mode = True
        st.session_state.demo_step = 0

with col5:
    if st.button("🔄 Reset", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ["db_conn"]:
                del st.session_state[key]
        init_session_state()
        st.rerun()


# ============================================================================
# DEMO MODE
# ============================================================================

if st.session_state.demo_mode and st.session_state.demo_step == 0:
    st.session_state.demo_step = 1
    _process_prompt("Create a supplier performance dashboard with KPIs, charts, and a data table")
    st.rerun()


# ============================================================================
# MAIN LAYOUT: TWO COLUMNS
# ============================================================================

col_chat, col_dashboard = st.columns([0.35, 0.65], gap="medium")


with col_chat:
    st.markdown("### 💬 Chat")
    user_input = render_chat_interface()

    # Process user input
    if user_input:
        _process_prompt(user_input, is_refinement=len(st.session_state.messages) > 2)
        st.rerun()


with col_dashboard:
    if st.session_state.show_engine and st.session_state.current_app:
        # Dashboard + Engine tabs
        tab_dash, tab_engine = st.tabs(["📊 Dashboard", "⚙️ Engine"])

        with tab_dash:
            render_dashboard(
                st.session_state.current_app,
                st.session_state.execution_results,
                st.session_state.current_role
            )

        with tab_engine:
            render_engine_view(
                st.session_state.current_app,
                st.session_state.execution_results,
                st.session_state.validation,
                st.session_state.governance
            )
    else:
        # Dashboard only
        render_dashboard(
            st.session_state.current_app,
            st.session_state.execution_results,
            st.session_state.current_role
        )


# ============================================================================
# SIDEBAR PANELS
# ============================================================================

st.sidebar.markdown("---")

# Governance Panel
if st.session_state.current_app:
    st.sidebar.markdown("### ✅ Governance")

    gov_checks = st.session_state.governance.get("checks", [])
    for check in gov_checks[:3]:  # Show top 3
        icon = "✅" if check.get("passed") else "⚠️"
        st.sidebar.caption(f"{icon} {check.get('name', 'Check')}")

# Dataset Info
if st.session_state.current_app:
    st.sidebar.markdown("### 📊 Dataset Info")
    st.sidebar.caption(f"Source: {st.session_state.current_app.get('data_source', 'Unknown')}")

    components = st.session_state.current_app.get("components", [])
    st.sidebar.caption(f"Components: {len(components)}")

# Role Info
st.sidebar.markdown("### 👤 You are")
st.sidebar.caption(st.session_state.current_role.capitalize())

# Audit Log (last 5)
st.sidebar.markdown("### 📝 Recent Activity")
for entry in st.session_state.audit_log[-5:]:
    st.sidebar.caption(
        f"**{entry['action']}** — {entry['timestamp']}"
    )

if not st.session_state.audit_log:
    st.sidebar.caption("No activity yet")
```

---

## SECTION 3: MOCK DATA FOR DEVELOPMENT

**Include this in your app.py or as a separate `mock_data.py` file:**

The mock data functions are already embedded in `app.py` above:
- `get_mock_app_definition()` — Complete app config
- `get_mock_execution_results()` — Sample DataFrames
- `get_mock_governance()` — Sample governance checks
- `get_mock_validation()` — Sample validation results

**Key principle:** All rendering happens against these mocks. You don't wait for Person 1's engine.

---

## SECTION 4: INTEGRATION CONTRACT

**The `app_definition` JSON Schema (Person 1's Output → Person 2's Input)**

```json
{
  "id": "app_unique_id",
  "name": "Dashboard Name",
  "data_source": "table_or_schema_name",
  "description": "What this dashboard does",
  "filters": [
    {
      "id": "filter_id",
      "type": "select|multiselect|date_range|number_range",
      "label": "Display Name",
      "options": ["option1", "option2"],
      "min": 0,
      "max": 100
    }
  ],
  "components": [
    {
      "id": "component_id",
      "type": "kpi|bar|line|pie|scatter|area|table|metric",
      "title": "Component Title",
      "width": 1.0,
      "config": {
        "format": "currency|percentage|decimal|number",
        "x_column": "column_name",
        "y_column": "column_name",
        "color_column": "column_name",
        "labels_column": "column_name",
        "values_column": "column_name",
        "threshold": 5.0,
        "row_limit": 20
      },
      "generated_sql": "SELECT ... FROM ..."
    }
  ]
}
```

**execution_results Format:**
```python
{
  "component_id_1": pd.DataFrame([...]),
  "component_id_2": pd.DataFrame([...]),
  ...
}
```

**governance Format:**
```json
{
  "status": "pass|fail",
  "checks": [
    {
      "name": "Check Name",
      "passed": true,
      "message": "Details",
      "details": "{...}"
    }
  ]
}
```

**validation Format:**
```json
{
  "status": "valid|invalid",
  "checks": [
    {
      "check": "Check Name",
      "passed": true
    }
  ]
}
```

---

## SECTION 5: TIMELINE

**Hour 0-1:** Project setup
- Create file structure: `ui/`, `app.py`
- Copy `styles.py` — test CSS injection
- Test mock data renders

**Hour 1-3:** Build dashboard renderer
- Implement all 8 chart types in `dashboard.py`
- Test with mock data
- Verify Plotly dark theme, 400px height, #e2e8f0 colors

**Hour 3-5:** Chat and templates
- Build `chat.py` message display
- Render 6 template cards
- Build `app.py` skeleton with session state
- Wire template selection to chat

**Hour 5-6:** Integration preparation
- Document the `app_definition` contract
- Create helper functions for Person 1's engine output
- Test with mock data one more time

**Hour 6-8:** Engine view
- Build `engine_view.py` 4 tabs
- SQL tab with expandable sections
- Data flow DAG
- Governance checks display
- Audit log (reverse chronological)

**Hour 8-10:** Role & demo
- Role selector (admin/analyst/viewer)
- Show Engine toggle
- Demo mode (2 auto-prompts)
- Audit entries on each action

**Hour 10-12:** Filters & refinement
- Sidebar filter widgets (multiselect, date_range, number_range)
- Connect filters to dashboard refresh
- Refinement prompts (detect 2nd+ message)
- Loading states (st.spinner)

**Hour 12-14:** Polish
- UX refinement
- Error handling (empty states, missing data)
- Dark theme perfection
- Performance optimization

---

## SECTION 6: TESTING CHECKLIST

### Chart Rendering
- [ ] All 8 chart types render with mock data
- [ ] KPI cards format numbers correctly (currency, percentage, decimal)
- [ ] Bar chart shows threshold line
- [ ] Line chart shows multiple lines if color_column present
- [ ] Pie chart displays labels and values
- [ ] Scatter plot shows markers
- [ ] Area chart fills correctly
- [ ] Table displays with row limit

### Layout
- [ ] Components group by width (1.0 full, 0.5 half, 0.33 third)
- [ ] Responsive on different screen sizes
- [ ] Sidebar doesn't overlap dashboard

### Chat & Templates
- [ ] Template cards display 6 options in 3-column grid
- [ ] Clicking template sends prompt
- [ ] Chat messages display with correct roles
- [ ] Template selector hides after first message
- [ ] User input appends to messages correctly

### Filters
- [ ] Multiselect filter renders with options
- [ ] Date range filter shows 2 date pickers
- [ ] Number range filter shows min/max
- [ ] Filter values persist in session state

### Dashboard Controls
- [ ] Role selector changes current_role in session state
- [ ] Show Engine toggle displays/hides engine tabs
- [ ] Reset button clears app and messages
- [ ] Demo button auto-sends first prompt

### Engine View
- [ ] SQL tab shows generated SQL per component
- [ ] SQL tab preview shows result dimensions
- [ ] Data Flow tab shows text DAG
- [ ] Governance tab shows status banner and checks
- [ ] Audit Log tab shows entries in reverse chronological order
- [ ] Audit entries updated on user actions

### Governance & Validation
- [ ] Governance badges show in template cards
- [ ] Governance status banner displays correct status
- [ ] Governance checks expandable with details
- [ ] Validation checks display

### Styling
- [ ] Dark theme (#0f172a background)
- [ ] KPI cards have gradient
- [ ] Chat bubbles have correct colors (indigo user, slate assistant)
- [ ] Badges colored correctly (green/yellow/red)
- [ ] Headers have gradient text
- [ ] Buttons have hover effects

### Error Handling
- [ ] Empty state displays when no app
- [ ] Missing data handled gracefully
- [ ] SQL errors show in engine view
- [ ] Invalid DataFrames don't crash

### Demo Mode
- [ ] First button click sets demo_step = 1
- [ ] Triggers first template prompt
- [ ] Can click again for next step

---

## FILES CREATED

1. **`ui/styles.py`** — 500+ lines of CSS
2. **`ui/chat.py`** — 200 lines of chat logic
3. **`ui/dashboard.py`** — 600+ lines of chart rendering
4. **`ui/engine_view.py`** — 250+ lines of engine inspection
5. **`app.py`** — 600+ lines of main orchestration

**Total:** ~2,500 lines of production-ready code

---

## HOW TO RUN

```bash
# 1. Install dependencies
pip install streamlit plotly pandas numpy

# 2. Create folder structure
mkdir -p stackforge/ui
touch stackforge/ui/__init__.py

# 3. Copy all files into stackforge/

# 4. Run
streamlit run stackforge/app.py
```

---

## WHAT PERSON 2 DELIVERS AT HOUR 19

✅ Beautiful dark-themed Streamlit UI
✅ All 8 chart types rendering perfectly
✅ Responsive dashboard layout
✅ Chat interface with template selector
✅ Engine view (4 tabs)
✅ Role selector + Show Engine toggle
✅ Filter sidebar
✅ Governance & audit panels
✅ Demo mode
✅ Ready to plug into Person 1's engine

---

## INTEGRATION WITH PERSON 1

When Person 1 finishes their engine, replace the mock data calls:

```python
# OLD (mock)
st.session_state.current_app = get_mock_app_definition()
st.session_state.execution_results = get_mock_execution_results()

# NEW (real)
app_def, exec_results = person1_engine.process_prompt(prompt, context)
st.session_state.current_app = app_def
st.session_state.execution_results = exec_results
```

Everything else stays the same. The `app_definition` contract is guaranteed.

---

**YOU GOT THIS! 🚀**
