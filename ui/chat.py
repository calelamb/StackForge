"""
Chat interface for StackForge.
Handles message display, user input, and template selection.
"""

import streamlit as st
from typing import Dict, Optional
import json


# ============================================================================
# TEMPLATES
# ============================================================================

TEMPLATES = [
    {
        "name": "Supplier Performance",
        "icon": "📦",
        "description": "Track supplier metrics, defect rates, and delivery times",
        "governance": ["policy", "data-quality"],
        "prompt": (
            "Create a supplier performance dashboard with KPIs for total orders, "
            "average defect rate, and on-time delivery percentage. Include a bar chart "
            "of defect rate by supplier, a line chart of delivery trends, a pie chart "
            "of orders by region, and a table of supplier details. Add filters for region "
            "and category."
        ),
    },
    {
        "name": "Inventory Optimization",
        "icon": "📊",
        "description": "Track stock levels, turnover rates, and warehouse costs",
        "governance": ["policy"],
        "prompt": (
            "Build an inventory optimization dashboard with KPIs for total stock value, "
            "inventory turnover, and warehouse cost total. Include a bar chart of stock "
            "levels by category, a line chart of inventory trends over time, and a table "
            "of top items by cost. Add filters for category and region."
        ),
    },
    {
        "name": "Supply Chain Costs",
        "icon": "💰",
        "description": "Analyze cost breakdown across the supply chain",
        "governance": ["policy", "data-quality"],
        "prompt": (
            "Create a supply chain cost breakdown dashboard with KPIs for total cost, "
            "average unit cost, and total shipping cost. Include a bar chart of costs by "
            "supplier, a pie chart of cost distribution by category, a line chart of cost "
            "trends over time, and a detailed cost table. Add filters for region and shipping mode."
        ),
    },
    {
        "name": "Quality Control Monitor",
        "icon": "🔍",
        "description": "Monitor defect rates and quality trends across suppliers",
        "governance": ["policy", "data-quality"],
        "prompt": (
            "Build a quality control monitor dashboard with KPIs for average defect rate, "
            "worst supplier defect rate, and total defective orders. Include a bar chart of "
            "defect rates by supplier, a scatter plot of defect rate vs delivery days, a line "
            "chart of defect trends over time, and a flagged suppliers table. Add filters for "
            "region and supplier."
        ),
    },
    {
        "name": "Logistics & Shipping",
        "icon": "🚚",
        "description": "Monitor delivery times, shipping modes, and on-time rates",
        "governance": ["policy"],
        "prompt": (
            "Create a logistics and shipping tracker dashboard with KPIs for average delivery "
            "days, on-time delivery rate, and total shipping cost. Include a bar chart of "
            "delivery days by shipping mode, a line chart of on-time trends, a pie chart of "
            "orders by shipping mode, and a shipment details table. Add filters for region "
            "and shipping mode."
        ),
    },
    {
        "name": "Executive KPI Summary",
        "icon": "📈",
        "description": "High-level business metrics and performance overview",
        "governance": ["policy", "security"],
        "prompt": (
            "Build an executive KPI summary dashboard with KPIs for total revenue (total_cost), "
            "total orders, average defect rate, and on-time delivery rate. Include a bar chart "
            "of revenue by region, a line chart of monthly order trends, an area chart of "
            "cumulative costs, and a top suppliers performance table. Add filters for region "
            "and category."
        ),
    },
]


# ============================================================================
# CHAT RENDERING
# ============================================================================


def render_chat_interface() -> Optional[str]:
    """
    Render the chat interface.
    Returns user input from st.chat_input if provided, otherwise None.
    """
    # Display existing messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for i, msg in enumerate(st.session_state.messages):
        _render_message(msg, msg_id=i)

    # Template selector (only shown when chat is empty)
    if len(st.session_state.messages) == 0:
        selected = render_template_selector()
        if selected:
            return selected

    # Chat input at bottom
    user_input = st.chat_input("Describe your dashboard or refine the current one...")
    return user_input


def _render_message(message: Dict, msg_id: int = 0):
    """Render a single chat message."""
    role = message.get("role", "assistant")
    content = message.get("content", "")

    if role == "user":
        st.markdown(
            f"""
            <div class="chat-message user">
                <div class="chat-role">👤 You</div>
                <div>{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="chat-message assistant">
                <div class="chat-role">🏭 StackForge</div>
                <div>{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Show app summary if present
    app_summary = message.get("app_summary")
    if app_summary:
        with st.expander("📊 App Definition"):
            st.code(json.dumps(app_summary, indent=2, default=str), language="json")


# ============================================================================
# MESSAGE HELPERS
# ============================================================================


def add_assistant_message(content: str, app_summary: Optional[Dict] = None):
    """Add an assistant message to chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.session_state.messages.append(
        {"role": "assistant", "content": content, "app_summary": app_summary}
    )


def add_user_message(content: str):
    """Add a user message to chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.session_state.messages.append({"role": "user", "content": content})


# ============================================================================
# TEMPLATE SELECTOR
# ============================================================================


def render_template_selector() -> Optional[str]:
    """
    Render template selector with 6 template cards in 3-column grid.
    Returns the prompt string if a template was selected, otherwise None.
    """
    st.markdown("#### 📋 Start with a Template")
    st.caption("Choose a pre-built dashboard template or describe your own below.")

    cols = st.columns(3)
    for idx, template in enumerate(TEMPLATES):
        col = cols[idx % 3]
        with col:
            # Render card HTML
            governance_badges = " ".join(
                f'<span class="badge badge-green">{gov}</span>'
                for gov in template.get("governance", [])
            )

            st.markdown(
                f"""
                <div class="template-card">
                    <div class="template-icon">{template['icon']}</div>
                    <h4 class="template-name">{template['name']}</h4>
                    <p class="template-description">{template['description']}</p>
                    <div class="template-governance">{governance_badges}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Use {template['name']}",
                key=f"tmpl-{idx}",
                use_container_width=True,
                type="primary",
            ):
                return template["prompt"]

    return None
