import streamlit as st
import json
import time
import pandas as pd
import plotly.express as px
from pathlib import Path

# ─── Page config ───
st.set_page_config(page_title="StackForge", page_icon="🏗️", layout="wide")

# ─── Paths ───
GRAPHS_DIR = Path(__file__).parent / "graphs"
GRAPHS_DIR.mkdir(exist_ok=True)


def load_graphs_from_disk() -> list[dict]:
    """Load all JSON files from the graphs/ folder, sorted newest first."""
    results = []
    for f in sorted(GRAPHS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text())
            title = data.get("app_definition", {}).get("app_title", f.stem)
            results.append({"file": f.name, "title": title, "result": data})
        except (json.JSONDecodeError, KeyError):
            continue
    return results


def fake_backend_api(user_prompt: str) -> dict:
    """Simulate a backend call. Reads the first JSON in graphs/ as mock output."""
    time.sleep(1.5)  # fake latency
    # Use any existing graph file as the mock response
    files = sorted(GRAPHS_DIR.glob("*.json"))
    if files:
        raw = files[0].read_text().strip()
        return json.loads(raw)
    raise FileNotFoundError("No mock data found in graphs/ folder")


# ─── Renderer helpers ───
def render_kpi(component: dict, data: list):
    """Render a KPI card."""
    cfg = component.get("config", {})
    value_col = cfg.get("value_column", "")
    label = cfg.get("metric_name", component["title"])
    if data and value_col in data[0]:
        val = data[0][value_col]
        fmt = cfg.get("format", "")
        if fmt == "percentage":
            display = f"{val:.2f}%"
        else:
            display = f"{val:,.2f}"
    else:
        display = "N/A"
    st.metric(label=label, value=display)


def render_bar_chart(component: dict, data: list):
    """Render a Plotly bar chart."""
    cfg = component.get("config", {})
    df = pd.DataFrame(data)
    if df.empty:
        st.warning("No data for this chart.")
        return
    x = cfg.get("x_axis", df.columns[0])
    y = cfg.get("y_axis", df.columns[1])
    # If there's a 'supplier' or color-like column, use it
    color_col = None
    for candidate in ["supplier", "category", "group"]:
        if candidate in df.columns and candidate != x and candidate != y:
            color_col = candidate
            break
    fig = px.bar(
        df, x=x, y=y, color=color_col,
        title=component["title"],
        template="plotly_dark",
        barmode="group",
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


def render_table(component: dict, data: list):
    """Render a data table."""
    df = pd.DataFrame(data)
    if df.empty:
        st.warning("No data for this table.")
        return
    cfg = component.get("config", {})
    sort_col = cfg.get("sort_column")
    sort_order = cfg.get("sort_order", "asc")
    if sort_col and sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=(sort_order == "asc"))
    st.dataframe(df, width="stretch")


def render_line_chart(component: dict, data: list):
    df = pd.DataFrame(data)
    if df.empty:
        st.warning("No data.")
        return
    cfg = component.get("config", {})
    x = cfg.get("x_axis", df.columns[0])
    y = cfg.get("y_axis", df.columns[1])
    fig = px.line(df, x=x, y=y, title=component["title"], template="plotly_dark")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


def render_pie_chart(component: dict, data: list):
    df = pd.DataFrame(data)
    if df.empty:
        st.warning("No data.")
        return
    cfg = component.get("config", {})
    names = cfg.get("names", df.columns[0])
    values = cfg.get("values", df.columns[1])
    fig = px.pie(df, names=names, values=values, title=component["title"], template="plotly_dark")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


def render_scatter(component: dict, data: list):
    df = pd.DataFrame(data)
    if df.empty:
        st.warning("No data.")
        return
    cfg = component.get("config", {})
    x = cfg.get("x_axis", df.columns[0])
    y = cfg.get("y_axis", df.columns[1])
    fig = px.scatter(df, x=x, y=y, title=component["title"], template="plotly_dark")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


RENDERERS = {
    "kpi_card": render_kpi,
    "bar_chart": render_bar_chart,
    "table": render_table,
    "line_chart": render_line_chart,
    "pie_chart": render_pie_chart,
    "scatter": render_scatter,
}


def render_dashboard(result: dict):
    """Render all components from a backend result."""
    app_def = result.get("app_definition", {})
    exec_results = result.get("execution_results", {})

    st.subheader(app_def.get("app_title", "Dashboard"))
    st.caption(app_def.get("app_description", ""))

    # Governance badge
    gov = result.get("governance", {})
    if gov:
        status = gov.get("overall_status", "unknown")
        if status == "pass":
            st.success(f"✅ Governance: PASSED  |  Role: {gov.get('role', '?')}")
        else:
            st.error(f"❌ Governance: {status.upper()}")

    # Render each component
    for comp in app_def.get("components", []):
        cid = comp["id"]
        ctype = comp["type"]
        comp_data = exec_results.get(cid, {}).get("data", [])
        renderer = RENDERERS.get(ctype)
        if renderer:
            renderer(comp, comp_data)
        else:
            st.info(f"Unsupported component type: {ctype}")


# ─── Main layout ───
st.title("🏗️ StackForge")

tab_create, tab_view = st.tabs(["📝 Create New Chart", "📊 View Charts"])

# ── Tab 1: Create ──
with tab_create:
    st.markdown("Describe the dashboard you want and we'll build it.")
    user_prompt = st.text_area(
        "What would you like to visualize?",
        placeholder="e.g. Show me supplier defect rates by region",
        height=100,
    )
    if st.button("🚀 Generate", type="primary"):
        if not user_prompt.strip():
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Building your dashboard…"):
                result = fake_backend_api(user_prompt)
            # Save to graphs/ folder with a timestamped name
            import datetime
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = user_prompt[:40].replace(" ", "_").replace("/", "-")
            out_path = GRAPHS_DIR / f"{ts}_{safe_name}.json"
            out_path.write_text(json.dumps(result, indent=2))
            st.success("Dashboard generated! Switch to the **View Charts** tab to see it.")
            st.rerun()

# ── Tab 2: View saved charts ──
with tab_view:
    saved = load_graphs_from_disk()
    if not saved:
        st.info("No charts found. Go to **Create New Chart** and submit a prompt, or drop a JSON into the `graphs/` folder.")
    else:
        for i, entry in enumerate(saved):
            with st.expander(
                f"{entry['title']}  ({entry['file']})",
                expanded=(i == 0),
            ):
                render_dashboard(entry["result"])
