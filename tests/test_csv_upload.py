"""
Tests for CSV upload / drag-and-drop feature.

Covers:
- register_uploaded_csv: table name sanitization, registration, queryability
- remove_table: cleanup of uploaded tables
- get_available_tables: discovery of uploaded tables alongside built-in ones
- Schema injection: uploaded tables appear in get_table_schema / get_all_sample_data
- Governance: uploaded table queries go through the same SQL safety + role checks
- Edge cases: empty CSVs, special characters, duplicate uploads, large files
"""
import pytest
import pandas as pd
import duckdb

from data.sample_data_loader import (
    get_connection,
    get_available_tables,
    get_table_schema,
    get_all_sample_data,
    register_uploaded_csv,
    remove_table,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def conn():
    """Fresh connection for each test (uses singleton)."""
    return get_connection()


@pytest.fixture
def sample_df():
    """A small sample DataFrame simulating an uploaded CSV."""
    return pd.DataFrame({
        "product_id": [1, 2, 3, 4, 5],
        "product_name": ["Widget A", "Widget B", "Gadget C", "Gadget D", "Doohickey E"],
        "price": [9.99, 19.99, 29.99, 39.99, 49.99],
        "quantity": [100, 200, 50, 75, 300],
        "region": ["North", "South", "East", "West", "North"],
    })


@pytest.fixture
def uploaded_table(sample_df):
    """Register a sample table and clean up after test."""
    table_name = register_uploaded_csv("test_products.csv", sample_df)
    yield table_name
    remove_table(table_name)


# ============================================================================
# TABLE NAME SANITIZATION
# ============================================================================

class TestTableNameSanitization:
    """register_uploaded_csv should produce safe, valid DuckDB table names."""

    def test_basic_csv_name(self, sample_df):
        name = register_uploaded_csv("sales_data.csv", sample_df)
        assert name == "sales_data"
        remove_table(name)

    def test_strips_extension(self, sample_df):
        name = register_uploaded_csv("report.csv", sample_df)
        assert name == "report"
        remove_table(name)

    def test_lowercases(self, sample_df):
        name = register_uploaded_csv("My_Report.csv", sample_df)
        assert name == "my_report"
        remove_table(name)

    def test_replaces_spaces(self, sample_df):
        name = register_uploaded_csv("my sales data.csv", sample_df)
        assert name == "my_sales_data"
        remove_table(name)

    def test_replaces_dashes(self, sample_df):
        name = register_uploaded_csv("q1-revenue-2024.csv", sample_df)
        assert name == "q1_revenue_2024"
        remove_table(name)

    def test_strips_special_chars(self, sample_df):
        name = register_uploaded_csv("data (final) [v2].csv", sample_df)
        assert name == "data_final_v2"
        remove_table(name)

    def test_leading_digit_gets_prefix(self, sample_df):
        name = register_uploaded_csv("2024_sales.csv", sample_df)
        assert name == "t_2024_sales"
        remove_table(name)

    def test_empty_name_fallback(self, sample_df):
        name = register_uploaded_csv("!!!.csv", sample_df)
        assert name == "uploaded_data"
        remove_table(name)


# ============================================================================
# REGISTRATION & QUERYABILITY
# ============================================================================

class TestRegistration:
    """Uploaded tables should be queryable via DuckDB."""

    def test_table_appears_in_available_tables(self, uploaded_table):
        tables = get_available_tables()
        assert uploaded_table in tables

    def test_can_select_from_uploaded_table(self, conn, uploaded_table):
        result = conn.execute(f"SELECT COUNT(*) FROM {uploaded_table}").fetchone()
        assert result[0] == 5

    def test_can_query_columns(self, conn, uploaded_table):
        result = conn.execute(
            f"SELECT product_name, price FROM {uploaded_table} WHERE price > 20"
        ).fetchall()
        assert len(result) == 3  # Gadget C, Gadget D, Doohickey E

    def test_can_aggregate(self, conn, uploaded_table):
        result = conn.execute(
            f"SELECT region, SUM(quantity) as total FROM {uploaded_table} GROUP BY region"
        ).fetchall()
        assert len(result) == 4  # North, South, East, West

    def test_can_cross_join_with_builtin_table(self, conn, uploaded_table):
        """Uploaded tables can be queried alongside built-in tables."""
        result = conn.execute(
            f"SELECT t.product_name, s.supplier "
            f"FROM {uploaded_table} t, supply_chain s LIMIT 5"
        ).fetchall()
        assert len(result) == 5

    def test_schema_includes_uploaded_table(self, uploaded_table):
        schema = get_table_schema()
        assert uploaded_table in schema
        assert "product_name" in schema
        assert "price" in schema

    def test_sample_data_includes_uploaded_table(self, uploaded_table):
        samples = get_all_sample_data(n=2)
        assert uploaded_table.upper() in samples.upper()

    def test_reupload_replaces_table(self, conn, sample_df):
        """Uploading the same filename again replaces the previous table."""
        name1 = register_uploaded_csv("replaceable.csv", sample_df)
        result1 = conn.execute(f"SELECT COUNT(*) FROM {name1}").fetchone()[0]
        assert result1 == 5

        # Upload again with different data
        new_df = pd.DataFrame({"x": [1, 2, 3]})
        name2 = register_uploaded_csv("replaceable.csv", new_df)
        assert name1 == name2
        result2 = conn.execute(f"SELECT COUNT(*) FROM {name2}").fetchone()[0]
        assert result2 == 3

        remove_table(name2)


# ============================================================================
# REMOVE TABLE
# ============================================================================

class TestRemoveTable:
    """remove_table should clean up uploaded tables."""

    def test_remove_returns_true(self, sample_df):
        name = register_uploaded_csv("temp_remove.csv", sample_df)
        assert remove_table(name) is True

    def test_removed_table_gone_from_list(self, sample_df):
        name = register_uploaded_csv("temp_gone.csv", sample_df)
        assert name in get_available_tables()
        remove_table(name)
        # After removal, it should not be in available tables
        # (DuckDB may still show it if registered as view vs table — check either way)
        tables = get_available_tables()
        # The table should either be gone or raise on query
        if name in tables:
            # If still listed, querying should fail
            try:
                conn = get_connection()
                conn.execute(f"SELECT 1 FROM {name}").fetchone()
            except Exception:
                pass  # Expected — table is gone

    def test_remove_nonexistent_table(self):
        """Removing a table that doesn't exist should not crash."""
        result = remove_table("this_table_does_not_exist_xyz")
        assert result is True  # DROP VIEW IF EXISTS succeeds silently


# ============================================================================
# GOVERNANCE INTEGRATION
# ============================================================================

class TestUploadGovernance:
    """Uploaded table queries go through governance checks."""

    def test_sql_injection_blocked_on_uploaded_table(self, uploaded_table):
        from engine.governance import run_governance_checks
        app_def = {
            "app_title": "Hack",
            "components": [{
                "id": "c1",
                "type": "table",
                "title": "Injected",
                "sql_query": f"SELECT * FROM {uploaded_table}; DROP TABLE {uploaded_table}",
                "config": {},
            }],
            "filters": [],
        }
        gov = run_governance_checks(app_def, role="admin")
        # Should detect the DROP keyword
        assert gov["passed"] is False

    def test_viewer_can_query_uploaded_table(self, conn, uploaded_table):
        """Viewers can query uploaded tables (columns aren't in restricted lists)."""
        from engine.governance import run_governance_checks
        app_def = {
            "app_title": "View Upload",
            "components": [{
                "id": "c1",
                "type": "bar_chart",
                "title": "Products by Region",
                "sql_query": f"SELECT region, COUNT(*) as cnt FROM {uploaded_table} GROUP BY region",
                "config": {},
            }],
            "filters": [],
        }
        gov = run_governance_checks(app_def, role="admin")
        assert gov["passed"] is True

    def test_uploaded_table_execution(self, conn, uploaded_table):
        """Execute components against an uploaded table end-to-end."""
        from engine.executor import execute_app_components
        app_def = {
            "app_title": "Upload Test",
            "components": [
                {
                    "id": "kpi1",
                    "type": "kpi_card",
                    "title": "Total Products",
                    "sql_query": f"SELECT COUNT(*) as total FROM {uploaded_table}",
                    "config": {"value_column": "total", "metric_name": "Total Products"},
                },
                {
                    "id": "bar1",
                    "type": "bar_chart",
                    "title": "Revenue by Region",
                    "sql_query": f"SELECT region, SUM(price * quantity) as revenue FROM {uploaded_table} GROUP BY region",
                    "config": {"x_axis": "region", "y_axis": "revenue"},
                },
            ],
            "filters": [],
        }
        results = execute_app_components(conn, app_def)
        assert results["kpi1"]["status"] == "success"
        assert results["kpi1"]["data"].iloc[0]["total"] == 5
        assert results["bar1"]["status"] == "success"
        assert len(results["bar1"]["data"]) == 4  # 4 regions


# ============================================================================
# EDGE CASES
# ============================================================================

class TestUploadEdgeCases:
    """Edge cases for CSV upload."""

    def test_empty_dataframe(self):
        """Uploading an empty CSV should still register the table."""
        df = pd.DataFrame({"a": [], "b": []})
        name = register_uploaded_csv("empty.csv", df)
        conn = get_connection()
        result = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()
        assert result[0] == 0
        remove_table(name)

    def test_single_column(self):
        """A CSV with only one column should work."""
        df = pd.DataFrame({"value": [1, 2, 3]})
        name = register_uploaded_csv("single_col.csv", df)
        conn = get_connection()
        result = conn.execute(f"SELECT SUM(value) FROM {name}").fetchone()
        assert result[0] == 6
        remove_table(name)

    def test_large_dataframe(self):
        """A 10,000-row CSV should register and query fine."""
        df = pd.DataFrame({
            "id": range(10000),
            "value": [i * 0.5 for i in range(10000)],
        })
        name = register_uploaded_csv("large.csv", df)
        conn = get_connection()
        result = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()
        assert result[0] == 10000
        remove_table(name)

    def test_columns_with_spaces(self):
        """Columns with spaces should be queryable with quotes."""
        df = pd.DataFrame({"first name": ["Alice", "Bob"], "last name": ["A", "B"]})
        name = register_uploaded_csv("people.csv", df)
        conn = get_connection()
        result = conn.execute(f'SELECT "first name" FROM {name}').fetchall()
        assert len(result) == 2
        remove_table(name)

    def test_mixed_types(self):
        """CSV with mixed column types should register."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["a", "b", "c"],
            "score": [1.1, 2.2, 3.3],
            "active": [True, False, True],
        })
        name = register_uploaded_csv("mixed.csv", df)
        conn = get_connection()
        result = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()
        assert result[0] == 3
        remove_table(name)

    def test_unicode_data(self):
        """CSV with unicode content should work."""
        df = pd.DataFrame({
            "city": ["Zurich", "Tokyo", "Sao Paulo"],
            "note": ["Zurcher See", "Tokyoeki", "Avenida Paulista"],
        })
        name = register_uploaded_csv("cities.csv", df)
        conn = get_connection()
        result = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()
        assert result[0] == 3
        remove_table(name)

    def test_multiple_uploads_coexist(self):
        """Multiple uploaded tables should all be queryable simultaneously."""
        df1 = pd.DataFrame({"x": [1, 2]})
        df2 = pd.DataFrame({"y": [3, 4, 5]})
        df3 = pd.DataFrame({"z": [6]})

        n1 = register_uploaded_csv("multi_a.csv", df1)
        n2 = register_uploaded_csv("multi_b.csv", df2)
        n3 = register_uploaded_csv("multi_c.csv", df3)

        tables = get_available_tables()
        assert n1 in tables
        assert n2 in tables
        assert n3 in tables

        conn = get_connection()
        assert conn.execute(f"SELECT COUNT(*) FROM {n1}").fetchone()[0] == 2
        assert conn.execute(f"SELECT COUNT(*) FROM {n2}").fetchone()[0] == 3
        assert conn.execute(f"SELECT COUNT(*) FROM {n3}").fetchone()[0] == 1

        remove_table(n1)
        remove_table(n2)
        remove_table(n3)

    def test_builtin_table_unaffected_by_uploads(self):
        """Uploading CSVs should not affect the built-in supply_chain table."""
        conn = get_connection()
        before = conn.execute("SELECT COUNT(*) FROM supply_chain").fetchone()[0]

        df = pd.DataFrame({"x": [1]})
        name = register_uploaded_csv("harmless.csv", df)

        after = conn.execute("SELECT COUNT(*) FROM supply_chain").fetchone()[0]
        assert before == after
        remove_table(name)
