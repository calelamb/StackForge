"""
Dashboard rendering for StackForge.
Renders all chart types, KPIs, tables, filters.
Handles responsive layout and dynamic component rendering.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List, Any


# ============================================================================
# PLOTLY THEME DEFAULTS
# ============================================================================

PLOTLY_LAYOUT_DEFAULTS = dict(
    template="plotly_dark",
    height=400,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e2e8f0", size=12),
    margin=dict(l=40, r=20, t=50, b=40),
    hovermode="x unified",
)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def render_dashboard(
    app_definition: Dict,
    execution_results: Dict,
    role: str = "analyst",
) -> Dict:
    """
    Main dashboard renderer. Orchestrates layout and renders all components.

    Args:
        app_definition: The app config JSON from the engine
        execution_results: Query results mapping component_id → DataFrame
        role: User role (admin/analyst/viewer)

    Returns:
        Updated execution_results (after filter changes)
    """
    if not app_definition or app_definition.get("components") is None:
        _render_empty_state()
        return execution_results

    components = app_definition.get("components", [])
    filters = app_definition.get("filters", [])

    # Render filters in sidebar
    if filters:
        _render_filters(filters, execution_results)

    # Group components into rows based on width
    rows = _group_components_by_width(components)

    # Render each row
    for row in rows:
        cols = st.columns(len(row))
        for col, component in zip(cols, row):
            with col:
                _render_component(component, execution_results, role)

    return execution_results


# ============================================================================
# EMPTY STATE
# ============================================================================


def _render_empty_state():
    """Shown when no app exists yet."""
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">🏭</div>
            <div class="empty-state-title">No Dashboard Yet</div>
            <div class="empty-state-text">
                Start by describing your dashboard in chat or selecting a template.<br>
                StackForge will generate a live, interactive data application.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# LAYOUT: GROUP COMPONENTS BY WIDTH
# ============================================================================


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

        if current_width + width > 1.01:  # small tolerance
            if current_row:
                rows.append(current_row)
            current_row = [component]
            current_width = width
        else:
            current_row.append(component)
            current_width += width

    if current_row:
        rows.append(current_row)

    return rows


# ============================================================================
# SIDEBAR FILTERS
# ============================================================================


def _render_filters(filter_defs: List[Dict], execution_results: Dict):
    """Render filter widgets in sidebar."""
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
                st.date_input(f"{label} Start", key=f"filter-{filter_id}-start")
            with cols[1]:
                st.date_input(f"{label} End", key=f"filter-{filter_id}-end")

        elif filter_type == "number_range":
            min_val = filter_def.get("min", 0)
            max_val = filter_def.get("max", 100)
            st.sidebar.slider(
                label,
                min_value=float(min_val),
                max_value=float(max_val),
                value=(float(min_val), float(max_val)),
                key=f"filter-{filter_id}",
            )


# ============================================================================
# COMPONENT ROUTER
# ============================================================================


def _render_component(component: Dict, execution_results: Dict, role: str = "analyst"):
    """Route component to correct renderer based on type."""
    comp_type = component.get("type", "")
    title = component.get("title", "")
    config = component.get("config", {})

    comp_id = component.get("id", "")
    df = execution_results.get(comp_id, pd.DataFrame())

    renderers = {
        "kpi": _render_kpi,
        "bar": _render_bar_chart,
        "line": _render_line_chart,
        "pie": _render_pie_chart,
        "scatter": _render_scatter,
        "area": _render_area_chart,
        "table": _render_table,
        "metric": _render_metric_highlight,
    }

    renderer = renderers.get(comp_type)
    if renderer:
        renderer(title, df, config)
    else:
        st.warning(f"Unknown component type: {comp_type}")


# ============================================================================
# KPI CARD
# ============================================================================


def _render_kpi(title: str, df: pd.DataFrame, config: Dict):
    """Render a KPI card with formatted value."""
    if df.empty:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{title}</div>
                <div class="kpi-value">—</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    value = df.iloc[0, 0]

    # Format
    fmt = config.get("format", "number")
    if fmt == "currency":
        formatted = f"${value:,.2f}"
    elif fmt == "percentage":
        formatted = f"{value:.1f}%"
    elif fmt == "decimal":
        formatted = f"{value:.2f}"
    else:
        formatted = f"{value:,.0f}"

    # Change indicator
    change_html = ""
    if len(df.columns) > 1:
        try:
            change_val = float(df.iloc[0, 1])
            cls = "positive" if change_val >= 0 else "negative"
            arrow = "↑" if change_val >= 0 else "↓"
            change_html = f'<div class="kpi-change {cls}">{arrow} {abs(change_val):.1f}%</div>'
        except (ValueError, TypeError):
            pass

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{formatted}</div>
            {change_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# BAR CHART
# ============================================================================


def _render_bar_chart(title: str, df: pd.DataFrame, config: Dict):
    """Render Plotly bar chart with optional threshold and color grouping."""
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    x_col = config.get("x_column", df.columns[0])
    y_col = config.get("y_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])
    color_col = config.get("color_column")

    fig = go.Figure()

    if color_col and color_col in df.columns:
        for group in df[color_col].unique():
            group_df = df[df[color_col] == group]
            fig.add_trace(
                go.Bar(x=group_df[x_col], y=group_df[y_col], name=str(group))
            )
    else:
        fig.add_trace(
            go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker=dict(color="#6366f1", line=dict(width=0)),
            )
        )

    threshold = config.get("threshold")
    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="rgba(245, 158, 11, 0.7)",
            annotation_text=f"Threshold ({threshold})",
            annotation_font_color="#f59e0b",
        )

    fig.update_layout(
        title=title,
        xaxis_title=config.get("x_label", x_col),
        yaxis_title=config.get("y_label", y_col),
        **PLOTLY_LAYOUT_DEFAULTS,
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# LINE CHART
# ============================================================================


def _render_line_chart(title: str, df: pd.DataFrame, config: Dict):
    """Render Plotly line chart with markers."""
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    x_col = config.get("x_column", df.columns[0])
    y_col = config.get("y_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])
    color_col = config.get("color_column")

    fig = go.Figure()

    if color_col and color_col in df.columns:
        for group in df[color_col].unique():
            group_df = df[df[color_col] == group].sort_values(x_col)
            fig.add_trace(
                go.Scatter(
                    x=group_df[x_col],
                    y=group_df[y_col],
                    mode="lines+markers",
                    name=str(group),
                    line=dict(width=2),
                    marker=dict(size=5),
                )
            )
    else:
        df_sorted = df.sort_values(x_col)
        fig.add_trace(
            go.Scatter(
                x=df_sorted[x_col],
                y=df_sorted[y_col],
                mode="lines+markers",
                line=dict(color="#6366f1", width=2),
                marker=dict(size=5, color="#6366f1"),
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title=config.get("x_label", x_col),
        yaxis_title=config.get("y_label", y_col),
        **PLOTLY_LAYOUT_DEFAULTS,
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# PIE CHART
# ============================================================================


def _render_pie_chart(title: str, df: pd.DataFrame, config: Dict):
    """Render Plotly pie chart."""
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    labels_col = config.get("labels_column", df.columns[0])
    values_col = config.get("values_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df[labels_col],
                values=df[values_col],
                marker=dict(line=dict(color="rgba(15, 23, 42, 1)", width=2)),
            )
        ]
    )

    fig.update_layout(
        title=title,
        **{k: v for k, v in PLOTLY_LAYOUT_DEFAULTS.items() if k != "hovermode"},
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# SCATTER PLOT
# ============================================================================


def _render_scatter(title: str, df: pd.DataFrame, config: Dict):
    """Render Plotly scatter chart."""
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    x_col = config.get("x_column", df.columns[0])
    y_col = config.get("y_column", df.columns[1] if len(df.columns) > 1 else df.columns[0])
    size_col = config.get("size_column")
    color_col = config.get("color_column")

    marker_config = dict(size=8, color="#6366f1", line=dict(width=0))

    if size_col and size_col in df.columns:
        marker_config["size"] = df[size_col]
    if color_col and color_col in df.columns:
        marker_config["color"] = df[color_col]
        marker_config["colorscale"] = "Viridis"

    fig = go.Figure(
        data=[
            go.Scatter(
                x=df[x_col], y=df[y_col], mode="markers", marker=marker_config
            )
        ]
    )

    fig.update_layout(
        title=title,
        xaxis_title=config.get("x_label", x_col),
        yaxis_title=config.get("y_label", y_col),
        hovermode="closest",
        **{k: v for k, v in PLOTLY_LAYOUT_DEFAULTS.items() if k != "hovermode"},
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# AREA CHART
# ============================================================================


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
        for group in df[color_col].unique():
            group_df = df[df[color_col] == group].sort_values(x_col)
            fig.add_trace(
                go.Scatter(
                    x=group_df[x_col],
                    y=group_df[y_col],
                    fill="tonexty",
                    name=str(group),
                    line=dict(width=1),
                )
            )
    else:
        df_sorted = df.sort_values(x_col)
        fig.add_trace(
            go.Scatter(
                x=df_sorted[x_col],
                y=df_sorted[y_col],
                fill="tozeroy",
                line=dict(color="#6366f1", width=2),
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title=config.get("x_label", x_col),
        yaxis_title=config.get("y_label", y_col),
        **PLOTLY_LAYOUT_DEFAULTS,
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# TABLE
# ============================================================================


def _render_table(title: str, df: pd.DataFrame, config: Dict):
    """Render interactive data table with optional row limit."""
    st.markdown(f"**{title}**")

    if df.empty:
        st.info("No data available for this table.")
        return

    limit = config.get("row_limit", len(df))
    df_display = df.head(limit)

    st.dataframe(df_display, use_container_width=True, height=400)

    if len(df) > limit:
        st.caption(f"Showing {limit} of {len(df)} rows")


# ============================================================================
# METRIC HIGHLIGHT
# ============================================================================


def _render_metric_highlight(title: str, df: pd.DataFrame, config: Dict):
    """Render data with conditional highlighting based on threshold."""
    if df.empty:
        st.markdown(f"**{title}** — No data available")
        return

    value_col = config.get("value_column", df.columns[-1] if len(df.columns) > 0 else None)
    if value_col is None:
        st.warning(f"No value column for metric: {title}")
        return

    label_col = df.columns[0] if len(df.columns) > 1 and df.columns[0] != value_col else None
    threshold = config.get("threshold", 0)

    st.markdown(f"**{title}**")

    for idx, row in df.iterrows():
        value = row[value_col]
        label = row[label_col] if label_col else f"Item {idx}"
        is_above = value >= threshold
        icon = "🟢" if not is_above else "🔴"  # Red if above threshold (bad)
        st.metric(f"{icon} {label}", f"{value:.2f}")
