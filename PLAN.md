# Custom Schema Injection — CSV Drag & Drop

## What we're building
A sidebar drag-and-drop file uploader that lets users upload their own CSV files, which get registered as queryable DuckDB tables instantly. The LLM then sees the new schema and can generate queries against the user's data.

## Implementation Steps

### 1. Modify `data/sample_data_loader.py`
- Add `register_uploaded_csv(file_name, dataframe)` function that:
  - Takes a filename and pandas DataFrame
  - Derives table name from filename (strip .csv, sanitize)
  - Registers it in the global DuckDB connection via `conn.register(table_name, df)`
  - Returns the table name
- Add `remove_table(table_name)` function for cleanup
- Add `get_registered_tables()` to list all current tables

### 2. Modify `app.py` — Sidebar Upload Section
- Add `st.file_uploader` in sidebar (after templates, before Engine toggle)
  - Accept `.csv` files, allow multiple
  - `accept_multiple_files=True`
- On upload:
  - Read each CSV into a pandas DataFrame
  - Call `register_uploaded_csv()` for each
  - Store uploaded table names in `st.session_state.uploaded_tables`
  - Show success indicator with table name + row count
- Add a "Your Data" section showing currently loaded tables with remove buttons
- Reset `pipeline_result` and `current_app` when data sources change (schema changed)

### 3. Modify `engine/intent_parser.py` — Schema Freshness
- Already dynamically calls `get_table_schema()` and `get_all_sample_data()` per request
- No changes needed — the schema injection is already dynamic
- The LLM will automatically see new tables in the prompt

### 4. Modify `config.py` — Column Sensitivity for Dynamic Tables
- Add a default sensitivity level for unknown columns (default to "public")
- Update `COLUMN_SENSITIVITY_MAP` lookup to return "public" for unrecognized columns
- This ensures governance doesn't block queries on user-uploaded data

### 5. Modify `engine/governance.py` — Handle Unknown Columns
- Update `check_column_access()` to treat columns not in COLUMN_SENSITIVITY_MAP as "public"
- This way uploaded CSV columns pass governance without manual config

## Files to modify
1. `data/sample_data_loader.py` — register/remove table functions
2. `app.py` — sidebar upload UI + session state management
3. `engine/governance.py` — handle unknown columns gracefully
4. `config.py` — default sensitivity for unknown columns (optional, may just handle in governance.py)
