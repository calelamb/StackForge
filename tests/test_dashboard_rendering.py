"""
Tests for dashboard rendering edge cases.

Covers scenarios that caused the StreamlitDuplicateElementId crash:
- Duplicate component IDs within a single app_definition
- Multiple back-to-back executions with overlapping component IDs
- Overview / narration lookup edge cases (missing, empty, mismatched)
- Renderer key uniqueness across dashboards
- _get_data helper resilience
- Component re-execution after refinement (same IDs, different SQL)

Does NOT require OpenAI API key — tests executor and validator layers
directly with hand-crafted app_definitions.

Run:  pytest tests/test_dashboard_rendering.py -v
"""

import pytest
import pandas as pd

from data.sample_data_loader import get_connection
from engine.executor import execute_app_components
from engine.validator import validate_and_explain


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def conn():
    return get_connection()


def _make_app(components, title="Test App"):
    return {
        "app_title": title,
        "app_description": "Test",
        "components": components,
        "filters": [],
    }


# ============================================================================
# DUPLICATE / OVERLAPPING COMPONENT IDS
# ============================================================================

class TestDuplicateComponentIds:
    """The bug was caused by multiple charts sharing auto-generated Streamlit
    element IDs. These tests ensure the data layer handles overlapping IDs
    gracefully — the UI layer adds unique keys on top of these results."""

    def test_two_identical_component_ids_both_execute(self, conn):
        """If an LLM accidentally returns two components with the same id,
        the executor should still run both (last one wins in the dict)."""
        app_def = _make_app([
            {
                "id": "chart_1",
                "type": "bar_chart",
                "title": "By Region",
                "sql_query": "SELECT region, COUNT(*) as cnt FROM supply_chain GROUP BY region",
                "config": {"x_axis": "region", "y_axis": "cnt"},
            },
            {
                "id": "chart_1",
                "type": "bar_chart",
                "title": "By Supplier",
                "sql_query": "SELECT supplier, COUNT(*) as cnt FROM supply_chain GROUP BY supplier",
                "config": {"x_axis": "supplier", "y_axis": "cnt"},
            },
        ])
        results = execute_app_components(conn, app_def)
        # Last component with same ID overwrites the first
        assert results["chart_1"]["status"] == "success"

    def test_many_components_with_unique_ids(self, conn):
        """10 components with unique IDs should all execute independently."""
        components = [
            {
                "id": f"comp_{i}",
                "type": "kpi_card",
                "title": f"KPI {i}",
                "sql_query": "SELECT COUNT(*) as total FROM supply_chain",
                "config": {"value_column": "total"},
            }
            for i in range(10)
        ]
        app_def = _make_app(components)
        results = execute_app_components(conn, app_def)
        assert len(results) == 10
        for i in range(10):
            assert results[f"comp_{i}"]["status"] == "success"

    def test_same_sql_different_ids(self, conn):
        """Two components with identical SQL but different IDs should
        both succeed with their own results."""
        sql = "SELECT region, AVG(defect_rate) as avg_defect FROM supply_chain GROUP BY region"
        app_def = _make_app([
            {"id": "chart_a", "type": "bar_chart", "title": "Chart A",
             "sql_query": sql, "config": {"x_axis": "region", "y_axis": "avg_defect"}},
            {"id": "chart_b", "type": "bar_chart", "title": "Chart B",
             "sql_query": sql, "config": {"x_axis": "region", "y_axis": "avg_defect"}},
        ])
        results = execute_app_components(conn, app_def)
        assert results["chart_a"]["status"] == "success"
        assert results["chart_b"]["status"] == "success"
        assert results["chart_a"]["row_count"] == results["chart_b"]["row_count"]


# ============================================================================
# BACK-TO-BACK EXECUTIONS (simulates multiple dashboards in chat history)
# ============================================================================

class TestBackToBackExecutions:
    """The duplicate element ID bug happens when the same dashboard is
    rendered multiple times in the chat. These tests verify that repeated
    executions produce independent, correct results."""

    def test_identical_app_executed_twice(self, conn):
        """Running the exact same app_definition twice should produce
        two independent result dicts."""
        app_def = _make_app([
            {"id": "kpi1", "type": "kpi_card", "title": "Total",
             "sql_query": "SELECT COUNT(*) as total FROM supply_chain",
             "config": {"value_column": "total"}},
            {"id": "bar1", "type": "bar_chart", "title": "By Region",
             "sql_query": "SELECT region, COUNT(*) as cnt FROM supply_chain GROUP BY region",
             "config": {"x_axis": "region", "y_axis": "cnt"}},
        ])
        results1 = execute_app_components(conn, app_def)
        results2 = execute_app_components(conn, app_def)

        # Both should succeed independently
        assert results1["kpi1"]["status"] == "success"
        assert results2["kpi1"]["status"] == "success"
        assert results1["bar1"]["status"] == "success"
        assert results2["bar1"]["status"] == "success"
        # They should be separate dict objects
        assert results1 is not results2

    def test_five_sequential_identical_executions(self, conn):
        """Simulate 5 messages in chat history all rendering the same dashboard."""
        app_def = _make_app([
            {"id": "chart_1", "type": "line_chart", "title": "Trend",
             "sql_query": "SELECT shipping_mode, AVG(delivery_days) as avg_days "
                          "FROM supply_chain GROUP BY shipping_mode",
             "config": {"x_axis": "shipping_mode", "y_axis": "avg_days"}},
        ])
        all_results = [execute_app_components(conn, app_def) for _ in range(5)]
        for r in all_results:
            assert r["chart_1"]["status"] == "success"
            assert r["chart_1"]["row_count"] > 0

    def test_overlapping_ids_across_different_apps(self, conn):
        """Two different apps that both use 'chart_1' as an ID should
        produce independent results with different data."""
        app1 = _make_app([
            {"id": "chart_1", "type": "bar_chart", "title": "Regions",
             "sql_query": "SELECT region, COUNT(*) as cnt FROM supply_chain GROUP BY region",
             "config": {"x_axis": "region", "y_axis": "cnt"}},
        ])
        app2 = _make_app([
            {"id": "chart_1", "type": "bar_chart", "title": "Suppliers",
             "sql_query": "SELECT supplier, COUNT(*) as cnt FROM supply_chain GROUP BY supplier",
             "config": {"x_axis": "supplier", "y_axis": "cnt"}},
        ])
        r1 = execute_app_components(conn, app1)
        r2 = execute_app_components(conn, app2)
        # Both succeed but have different row counts (5 regions vs 5 suppliers)
        assert r1["chart_1"]["status"] == "success"
        assert r2["chart_1"]["status"] == "success"
        # Results are independent objects
        assert r1["chart_1"]["data"] is not r2["chart_1"]["data"]

    def test_refinement_same_ids_different_sql(self, conn):
        """Simulates conversational refinement: user says 'change it to a pie chart'
        — same component ID, different SQL/type."""
        v1 = _make_app([
            {"id": "main_chart", "type": "bar_chart", "title": "By Region",
             "sql_query": "SELECT region, COUNT(*) as cnt FROM supply_chain GROUP BY region",
             "config": {"x_axis": "region", "y_axis": "cnt"}},
        ])
        v2 = _make_app([
            {"id": "main_chart", "type": "pie_chart", "title": "By Region",
             "sql_query": "SELECT region, SUM(total_cost) as cost FROM supply_chain GROUP BY region",
             "config": {"x_axis": "region", "y_axis": "cost"}},
        ])
        r1 = execute_app_components(conn, v1)
        r2 = execute_app_components(conn, v2)
        assert r1["main_chart"]["status"] == "success"
        assert r2["main_chart"]["status"] == "success"
        # Different SQL → different data
        assert r1["main_chart"]["row_count"] == r2["main_chart"]["row_count"]  # both 5 regions


# ============================================================================
# OVERVIEW / NARRATION EDGE CASES
# ============================================================================

class TestOverviewNarration:
    """The narration map is built from overview.components and matched by ID.
    These tests verify graceful behavior when the overview is missing,
    malformed, or doesn't match the actual components."""

    def test_missing_overview_key(self):
        """Pipeline result with no overview key at all."""
        result = {
            "app_definition": {"components": [
                {"id": "c1", "type": "kpi_card", "title": "KPI"}
            ]},
            "execution_results": {},
            "governance": {"passed": True},
        }
        overview = result.get("overview", {})
        narration_map = {
            nc.get("id"): nc.get("narration", "")
            for nc in overview.get("components", [])
            if nc.get("id") and nc.get("narration")
        }
        assert narration_map == {}

    def test_empty_overview(self):
        """Overview exists but is an empty dict."""
        overview = {}
        narration_map = {
            nc.get("id"): nc.get("narration", "")
            for nc in overview.get("components", [])
            if nc.get("id") and nc.get("narration")
        }
        assert narration_map == {}

    def test_overview_with_no_components(self):
        """Overview has a summary but no components list."""
        overview = {"summary": "This dashboard shows supply chain data."}
        narration_map = {
            nc.get("id"): nc.get("narration", "")
            for nc in overview.get("components", [])
            if nc.get("id") and nc.get("narration")
        }
        assert narration_map == {}

    def test_narration_map_matches_component_ids(self):
        """Normal case: narration IDs match component IDs."""
        overview = {
            "summary": "Overall summary.",
            "components": [
                {"id": "kpi1", "title": "Total", "narration": "Shows total count."},
                {"id": "bar1", "title": "By Region", "narration": "Breaks down by region."},
            ],
        }
        narration_map = {
            nc.get("id"): nc.get("narration", "")
            for nc in overview.get("components", [])
            if nc.get("id") and nc.get("narration")
        }
        assert narration_map["kpi1"] == "Shows total count."
        assert narration_map["bar1"] == "Breaks down by region."
        assert len(narration_map) == 2

    def test_narration_with_mismatched_ids(self):
        """Overview references component IDs that don't exist in the app."""
        app_components = [{"id": "real_chart"}]
        overview = {
            "summary": "Summary",
            "components": [
                {"id": "nonexistent_1", "title": "X", "narration": "Orphan narration."},
                {"id": "nonexistent_2", "title": "Y", "narration": "Another orphan."},
            ],
        }
        narration_map = {
            nc.get("id"): nc.get("narration", "")
            for nc in overview.get("components", [])
            if nc.get("id") and nc.get("narration")
        }
        # Narrations exist in map but won't match any real component — no crash
        assert "nonexistent_1" in narration_map
        assert "real_chart" not in narration_map

    def test_narration_with_empty_strings(self):
        """Components with empty narration should be excluded from the map."""
        overview = {
            "summary": "",
            "components": [
                {"id": "c1", "title": "A", "narration": ""},
                {"id": "c2", "title": "B", "narration": "Has narration."},
                {"id": "", "title": "C", "narration": "No ID."},
            ],
        }
        narration_map = {
            nc.get("id"): nc.get("narration", "")
            for nc in overview.get("components", [])
            if nc.get("id") and nc.get("narration")
        }
        assert "c1" not in narration_map  # empty narration
        assert "c2" in narration_map
        assert "" not in narration_map  # empty id

    def test_narration_with_none_values(self):
        """Components with None narration or id."""
        overview = {
            "summary": None,
            "components": [
                {"id": None, "title": "A", "narration": "text"},
                {"id": "c1", "title": "B", "narration": None},
                {"id": "c2", "title": "C", "narration": "Valid."},
            ],
        }
        narration_map = {
            nc.get("id"): nc.get("narration", "")
            for nc in overview.get("components", [])
            if nc.get("id") and nc.get("narration")
        }
        assert len(narration_map) == 1
        assert narration_map["c2"] == "Valid."

    def test_duplicate_ids_in_overview_last_wins(self):
        """If overview has duplicate component IDs, last one wins."""
        overview = {
            "summary": "Summary",
            "components": [
                {"id": "chart_1", "title": "V1", "narration": "First version."},
                {"id": "chart_1", "title": "V2", "narration": "Second version."},
            ],
        }
        narration_map = {
            nc.get("id"): nc.get("narration", "")
            for nc in overview.get("components", [])
            if nc.get("id") and nc.get("narration")
        }
        assert narration_map["chart_1"] == "Second version."


# ============================================================================
# DASHBOARD KEY UNIQUENESS
# ============================================================================

class TestDashboardKeyUniqueness:
    """Verifies that the key generation scheme produces unique keys
    across the scenarios that caused the duplicate element ID crash."""

    def _generate_keys(self, dashboard_key, component_ids):
        return [f"{dashboard_key}_{cid}" for cid in component_ids]

    def test_different_messages_same_components(self):
        """Two chat messages (msg_0, msg_1) with identical component IDs
        should produce completely disjoint key sets."""
        ids = ["kpi1", "bar1", "line1"]
        keys_msg0 = self._generate_keys("msg_0", ids)
        keys_msg1 = self._generate_keys("msg_1", ids)
        assert set(keys_msg0).isdisjoint(set(keys_msg1))

    def test_chat_vs_history_keys_disjoint(self):
        """Chat message keys (msg_*) and history keys (hist_*) never collide."""
        ids = ["chart_1", "chart_2"]
        chat_keys = self._generate_keys("msg_0", ids)
        hist_keys = self._generate_keys("hist_output_20260228_100913", ids)
        assert set(chat_keys).isdisjoint(set(hist_keys))

    def test_ten_messages_all_unique(self):
        """10 chat messages all rendering the same 5-component dashboard
        should produce 50 unique keys."""
        ids = ["k1", "k2", "b1", "b2", "t1"]
        all_keys = []
        for msg_idx in range(10):
            all_keys.extend(self._generate_keys(f"msg_{msg_idx}", ids))
        assert len(all_keys) == 50
        assert len(set(all_keys)) == 50  # all unique

    def test_key_with_special_component_id(self):
        """Component IDs with unusual characters still produce valid keys."""
        ids = ["chart-1", "chart 2", "chart_3!", ""]
        keys = self._generate_keys("msg_0", ids)
        assert len(keys) == 4
        assert len(set(keys)) == 4


# ============================================================================
# _get_data HELPER RESILIENCE
# ============================================================================

class TestGetDataHelper:
    """The _get_data helper extracts data from execution results.
    It must handle all shapes without crashing."""

    def _get_data(self, comp_result):
        """Mirror the app.py helper."""
        if isinstance(comp_result, dict):
            return comp_result.get("data", [])
        elif isinstance(comp_result, list):
            return comp_result
        return []

    def test_normal_success_result(self):
        data = self._get_data({
            "status": "success",
            "data": [{"region": "North", "cnt": 10}],
            "row_count": 1,
        })
        assert len(data) == 1
        assert data[0]["region"] == "North"

    def test_error_result(self):
        data = self._get_data({
            "status": "error",
            "error": "Table not found",
            "row_count": 0,
        })
        assert data == []

    def test_empty_dict(self):
        assert self._get_data({}) == []

    def test_none_value(self):
        assert self._get_data(None) == []

    def test_raw_list(self):
        raw = [{"a": 1}, {"a": 2}]
        assert self._get_data(raw) == raw

    def test_empty_list(self):
        assert self._get_data([]) == []

    def test_string_value(self):
        assert self._get_data("unexpected") == []

    def test_integer_value(self):
        assert self._get_data(42) == []

    def test_dataframe_in_data(self):
        """Executor stores DataFrames — _get_data should return them as-is."""
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = self._get_data({"status": "success", "data": df, "row_count": 3})
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3


# ============================================================================
# VALIDATION ACROSS REPEATED DASHBOARDS
# ============================================================================

class TestValidationRepeatedDashboards:
    """Validator should produce consistent results when the same
    app_definition is validated multiple times (as happens in chat history)."""

    def test_validate_same_app_twice_consistent(self, conn):
        app_def = _make_app([
            {"id": "kpi1", "type": "kpi_card", "title": "Total Orders",
             "sql_query": "SELECT COUNT(*) as total FROM supply_chain",
             "config": {"value_column": "total"}},
            {"id": "bar1", "type": "bar_chart", "title": "By Region",
             "sql_query": "SELECT region, COUNT(*) as cnt FROM supply_chain GROUP BY region",
             "config": {"x_axis": "region", "y_axis": "cnt"}},
        ])
        results = execute_app_components(conn, app_def)
        v1 = validate_and_explain(app_def, results)
        v2 = validate_and_explain(app_def, results)
        assert v1["overall_status"] == v2["overall_status"]
        assert len(v1["components"]) == len(v2["components"])

    def test_validate_all_chart_types(self, conn):
        """Every chart type should validate without errors when executed
        back-to-back (the scenario that triggers duplicate keys)."""
        app_def = _make_app([
            {"id": "kpi1", "type": "kpi_card", "title": "KPI",
             "sql_query": "SELECT COUNT(*) as v FROM supply_chain",
             "config": {"value_column": "v"}},
            {"id": "bar1", "type": "bar_chart", "title": "Bar",
             "sql_query": "SELECT region, COUNT(*) as c FROM supply_chain GROUP BY region",
             "config": {"x_axis": "region", "y_axis": "c"}},
            {"id": "line1", "type": "line_chart", "title": "Line",
             "sql_query": "SELECT shipping_mode, AVG(delivery_days) as d FROM supply_chain GROUP BY shipping_mode",
             "config": {"x_axis": "shipping_mode", "y_axis": "d"}},
            {"id": "pie1", "type": "pie_chart", "title": "Pie",
             "sql_query": "SELECT region, SUM(total_cost) as cost FROM supply_chain GROUP BY region",
             "config": {"x_axis": "region", "y_axis": "cost"}},
            {"id": "scatter1", "type": "scatter_plot", "title": "Scatter",
             "sql_query": "SELECT defect_rate, delivery_days FROM supply_chain LIMIT 50",
             "config": {"x_axis": "defect_rate", "y_axis": "delivery_days"}},
            {"id": "area1", "type": "area_chart", "title": "Area",
             "sql_query": "SELECT shipping_mode, SUM(shipping_cost) as sc FROM supply_chain GROUP BY shipping_mode",
             "config": {"x_axis": "shipping_mode", "y_axis": "sc"}},
            {"id": "table1", "type": "table", "title": "Table",
             "sql_query": "SELECT supplier, region, product FROM supply_chain LIMIT 10",
             "config": {}},
        ])
        # Execute twice to simulate two dashboards in chat
        r1 = execute_app_components(conn, app_def)
        r2 = execute_app_components(conn, app_def)
        for cid in ["kpi1", "bar1", "line1", "pie1", "scatter1", "area1", "table1"]:
            assert r1[cid]["status"] == "success", f"{cid} failed on first execution"
            assert r2[cid]["status"] == "success", f"{cid} failed on second execution"

    def test_mixed_success_and_error_repeated(self, conn):
        """App with one good and one bad component, executed twice."""
        app_def = _make_app([
            {"id": "good", "type": "kpi_card", "title": "Good",
             "sql_query": "SELECT COUNT(*) as total FROM supply_chain",
             "config": {"value_column": "total"}},
            {"id": "bad", "type": "bar_chart", "title": "Bad",
             "sql_query": "SELECT nonexistent_col FROM supply_chain",
             "config": {"x_axis": "x", "y_axis": "y"}},
        ])
        r1 = execute_app_components(conn, app_def)
        r2 = execute_app_components(conn, app_def)
        assert r1["good"]["status"] == "success"
        assert r1["bad"]["status"] == "error"
        assert r2["good"]["status"] == "success"
        assert r2["bad"]["status"] == "error"
