# PERSON 3 — THE SHIELD + STORY
## StackForge Governance, Demo & Pitch
### HackUSU 2026 (19-hour hackathon) — Koch/Databricks/AWS Data App Factory Track

---

## SECTION 1: CLAUDE CODE KICKOFF PROMPT

**Copy and paste this entire prompt into Claude Code to get started:**

```
I am part of a 3-person team building StackForge, an AI Data App Factory for HackUSU 2026
(Data App Factory track, sponsored by Koch, Databricks, and AWS).

I am Person 3, and I own:
1. engine/governance.py — the complete governance engine (deterministic Python, no AI, no database needed)
2. Demo mode logic (Step 0 → Step 1 → Step 2, triggered by a Demo button in the header)
3. Template library refinement (testing all 6 default templates and refining prompts if needed)
4. The presentation and pitch (10-minute demo + talking points for judges)
5. Audit logging enhancements throughout the app

I do NOT touch:
- intent_parser.py or executor.py (Person 1 owns the AI engine and SQL execution)
- dashboard.py or chart rendering logic (Person 2 owns the UI and Plotly visualizations)

What I CAN do immediately:
- Build governance.py with mock data — it's pure deterministic Python
- No dependencies on Person 1's AI or Person 2's UI
- I can start building and testing with hardcoded test app_definitions right now

Please follow the PRD below EXACTLY. Every function signature, every check, every response format matters
because Person 2 will integrate my governance checks into the dashboard, and the presentation depends
on this engine being rock-solid.

The PRD is in the message below.
```

---

## SECTION 2: THE PRD — GOVERNANCE ENGINE

### Core Module: `engine/governance.py`

**Location:** `/path/to/StackForge/engine/governance.py`

**Purpose:** Deterministic governance checks on data apps before execution or deployment. No AI calls, no database queries — pure Python.

**Key Principle:** Governance must be FAST (milliseconds), DETERMINISTIC (same input = same output every time), and TRANSPARENT (judges can see exactly why a check passed or failed).

---

### Function 1: `run_governance_checks(app_definition, role, execution_results=None)`

**Signature:**
```python
def run_governance_checks(app_definition: dict, role: str, execution_results: dict = None) -> dict:
    """
    Runs all governance checks on an app definition.

    Args:
        app_definition (dict): The parsed app definition with 'intent', 'sql_queries', 'components', etc.
        role (str): User role ('admin', 'analyst', 'viewer')
        execution_results (dict, optional): Results from query execution, if available

    Returns:
        dict: {
            "checks": [
                {
                    "rule": str,           # Name of the check (e.g., "PII Detection")
                    "status": str,         # "pass", "warning", or "fail"
                    "message": str,        # Human-readable message
                    "details": str         # Technical details
                },
                ...
            ],
            "requires_approval": bool,     # True if this app needs admin approval before deployment
            "pii_columns_detected": list,  # List of detected PII column names
            "overall_status": str,         # "compliant", "review_required", or "non_compliant"
            "timestamp": str,              # ISO 8601 timestamp
            "role": str                    # The role that was checked
        }
    """
```

**Return Example:**
```python
{
    "checks": [
        {
            "rule": "PII Detection",
            "status": "warning",
            "message": "PII patterns detected in SQL queries",
            "details": "Found patterns: email (1 match), phone (1 match)"
        },
        {
            "rule": "Access Control",
            "status": "pass",
            "message": "Role capabilities aligned with feature requests",
            "details": "Viewer role requesting aggregated data only"
        },
        {
            "rule": "Query Complexity",
            "status": "pass",
            "message": "Query complexity within role limits",
            "details": "Component count: 3, Limit: 4 (viewer)"
        },
        {
            "rule": "Data Quality",
            "status": "warning",
            "message": "SELECT * pattern detected",
            "details": "Found 1 SELECT * in query"
        },
        {
            "rule": "Export Control",
            "status": "pass",
            "message": "Export permission granted for this role",
            "details": "Analyst role can export"
        },
        {
            "rule": "Audit Trail",
            "status": "pass",
            "message": "Audit logging is active",
            "details": "All actions will be logged"
        }
    ],
    "requires_approval": True,
    "pii_columns_detected": ["email", "phone_number"],
    "overall_status": "review_required",
    "timestamp": "2026-02-28T14:30:45Z",
    "role": "analyst"
}
```

**Logic:**

1. Initialize empty `checks` list
2. Run all six checks in order (see below)
3. Determine `overall_status`:
   - If any check is "fail" → `"non_compliant"`
   - If any check is "warning" OR role is non-admin and component count > 6 → `"review_required"`
   - Otherwise → `"compliant"`
4. Set `requires_approval`:
   - `True` if `overall_status != "compliant"` and role != "admin"
   - `True` if role != "admin" and component_count > 6
   - Otherwise `False`
5. Extract PII columns from all queries
6. Return the complete dict with timestamp (use `datetime.utcnow().isoformat() + "Z"`)

---

### Function 2: `_check_pii_detection(app_definition, role)`

**Purpose:** Scan all SQL queries for personally identifiable information patterns.

**Implementation:**

```python
def _check_pii_detection(app_definition: dict, role: str) -> dict:
    """
    Detects PII patterns in SQL queries.

    Returns:
        {
            "rule": "PII Detection",
            "status": str,     # "pass", "warning", or "fail"
            "message": str,
            "details": str,
            "pii_columns": list
        }
    """

    # PII_PATTERNS from config
    PII_PATTERNS = {
        "email": r'\bemail\b',
        "phone": r'\b(phone|telephone|mobile|cell)\b',
        "ssn": r'\bssn\b|\bsocial_security\b',
        "birth_date": r'\b(birth_date|dob|date_of_birth)\b',
        "salary": r'\bsalary\b|\bwage\b',
        "address": r'\b(address|street|city|state|province)\b',
        "zip_code": r'\b(zip_code|postal_code|zipcode)\b',
        "credit_card": r'\b(credit_card|card_number|cc_number)\b',
        "passport": r'\bpassport\b',
        "driver_license": r'\b(driver_license|driver_lic|dl_number)\b',
        "name": r'\b(first_name|last_name|full_name)\b'
    }

    # Collect all SQL queries
    queries = []
    if "sql_queries" in app_definition:
        queries.extend(app_definition["sql_queries"])
    if "intent" in app_definition and "queries" in app_definition["intent"]:
        queries.extend(app_definition["intent"]["queries"])

    # Scan for PII
    pii_columns = []
    pattern_matches = {}

    for query in queries:
        query_upper = query.upper()
        for pii_type, pattern in PII_PATTERNS.items():
            import re
            matches = re.findall(pattern, query_upper, re.IGNORECASE)
            if matches:
                if pii_type not in pattern_matches:
                    pattern_matches[pii_type] = 0
                pattern_matches[pii_type] += len(matches)
                # Extract column names (rough heuristic: word before or after pattern)
                for match in matches:
                    if match not in pii_columns:
                        pii_columns.append(match.lower())

    if not pattern_matches:
        return {
            "rule": "PII Detection",
            "status": "pass",
            "message": "No PII patterns detected",
            "details": "Scanned all SQL queries",
            "pii_columns": []
        }

    # If admin, warning only. If non-admin, fail.
    details = "Found patterns: " + ", ".join([f"{k} ({v} match{'es' if v > 1 else ''})"
                                               for k, v in pattern_matches.items()])

    if role == "admin":
        return {
            "rule": "PII Detection",
            "status": "warning",
            "message": "PII patterns detected in SQL queries",
            "details": details,
            "pii_columns": pii_columns
        }
    else:
        return {
            "rule": "PII Detection",
            "status": "fail",
            "message": "PII access denied for this role",
            "details": f"Non-admin users cannot query: {', '.join(pii_columns)}. "
                       f"Contact admin for approval or request anonymized data.",
            "pii_columns": pii_columns
        }
```

---

### Function 3: `_check_access_control(app_definition, role)`

**Purpose:** Verify that the user's role has permission to perform requested operations.

**Implementation:**

```python
def _check_access_control(app_definition: dict, role: str) -> dict:
    """
    Checks if the role is authorized to access requested features.

    Role capabilities:
    - admin: all access, can deploy, can view raw data
    - analyst: can view aggregated data, can deploy (with approval), can't deploy without approval
    - viewer: aggregated data only, can't deploy, can't export
    """

    role_permissions = {
        "admin": {
            "view_raw_data": True,
            "view_aggregated_data": True,
            "deploy": True,
            "export": True
        },
        "analyst": {
            "view_raw_data": False,
            "view_aggregated_data": True,
            "deploy": False,  # Requires approval
            "export": True
        },
        "viewer": {
            "view_raw_data": False,
            "view_aggregated_data": True,
            "deploy": False,
            "export": False
        }
    }

    # Check if role exists
    if role not in role_permissions:
        return {
            "rule": "Access Control",
            "status": "fail",
            "message": f"Unknown role: {role}",
            "details": f"Valid roles are: {', '.join(role_permissions.keys())}"
        }

    # Check if app requests raw data access
    requests_raw_data = app_definition.get("requests_raw_data", False)
    if requests_raw_data and not role_permissions[role]["view_raw_data"]:
        return {
            "rule": "Access Control",
            "status": "fail",
            "message": f"Role '{role}' cannot access raw data",
            "details": "Only admin and analyst roles can query raw data tables"
        }

    # Check if app requests deployment
    requests_deploy = app_definition.get("requests_deploy", False)
    if requests_deploy and not role_permissions[role]["deploy"]:
        return {
            "rule": "Access Control",
            "status": "fail",
            "message": f"Role '{role}' cannot deploy apps",
            "details": "Only admins can deploy. Analysts can request approval."
        }

    # Passed
    return {
        "rule": "Access Control",
        "status": "pass",
        "message": "Role capabilities aligned with feature requests",
        "details": f"User role '{role}' has required permissions"
    }
```

---

### Function 4: `_check_query_complexity(app_definition, role)`

**Purpose:** Enforce component count limits per role to prevent runaway queries.

**Implementation:**

```python
def _check_query_complexity(app_definition: dict, role: str) -> dict:
    """
    Checks query complexity against role limits.

    Limits:
    - viewer: max 4 components
    - analyst: max 8 components
    - admin: unlimited

    "Components" = charts + tables + KPI cards
    """

    role_limits = {
        "viewer": 4,
        "analyst": 8,
        "admin": float('inf')
    }

    # Count components
    component_count = 0
    if "components" in app_definition:
        component_count = len(app_definition["components"])

    limit = role_limits.get(role, 0)

    if component_count > limit:
        return {
            "rule": "Query Complexity",
            "status": "warning" if role == "analyst" else "fail",
            "message": f"Component count exceeds limit for role '{role}'",
            "details": f"Requested: {component_count} components, Limit: {limit}"
        }

    return {
        "rule": "Query Complexity",
        "status": "pass",
        "message": "Query complexity within role limits",
        "details": f"Component count: {component_count}, Limit: {limit}"
    }
```

---

### Function 5: `_check_data_quality(app_definition, role)`

**Purpose:** Flag common SQL anti-patterns (SELECT *).

**Implementation:**

```python
def _check_data_quality(app_definition: dict, role: str) -> dict:
    """
    Checks for data quality anti-patterns.
    """

    queries = []
    if "sql_queries" in app_definition:
        queries.extend(app_definition["sql_queries"])
    if "intent" in app_definition and "queries" in app_definition["intent"]:
        queries.extend(app_definition["intent"]["queries"])

    select_star_count = 0
    for query in queries:
        import re
        # Look for SELECT * (roughly)
        if re.search(r'\bSELECT\s+\*\b', query, re.IGNORECASE):
            select_star_count += 1

    if select_star_count > 0:
        return {
            "rule": "Data Quality",
            "status": "warning",
            "message": "SELECT * pattern detected",
            "details": f"Found {select_star_count} SELECT * in queries. "
                       f"Best practice: explicitly select columns."
        }

    return {
        "rule": "Data Quality",
        "status": "pass",
        "message": "Data quality checks passed",
        "details": "No SELECT * anti-patterns detected"
    }
```

---

### Function 6: `_check_export_control(app_definition, role)`

**Purpose:** Enforce export permissions based on role.

**Implementation:**

```python
def _check_export_control(app_definition: dict, role: str) -> dict:
    """
    Checks if role is allowed to export data.

    Permissions:
    - admin: yes
    - analyst: yes
    - viewer: no
    """

    requests_export = app_definition.get("requests_export", False)

    if not requests_export:
        return {
            "rule": "Export Control",
            "status": "pass",
            "message": "No export requested",
            "details": "This app does not request data export"
        }

    if role == "viewer":
        return {
            "rule": "Export Control",
            "status": "fail",
            "message": "Export denied for viewer role",
            "details": "Viewers cannot export data. Contact admin for alternative access."
        }

    return {
        "rule": "Export Control",
        "status": "pass",
        "message": "Export permission granted for this role",
        "details": f"Role '{role}' can export data"
    }
```

---

### Function 7: `_check_audit_trail(app_definition, role)`

**Purpose:** Confirm audit logging is active.

**Implementation:**

```python
def _check_audit_trail(app_definition: dict, role: str) -> dict:
    """
    Confirms audit logging will be active for this app.
    """

    # In the real system, check if audit logging is enabled in config
    # For now, always pass (logging is built into the app)

    return {
        "rule": "Audit Trail",
        "status": "pass",
        "message": "Audit logging is active",
        "details": "All actions will be logged with timestamp, role, and details"
    }
```

---

### Function 8: `mask_pii_columns(df, role, pii_columns)`

**Purpose:** Helper for Person 2's dashboard to mask PII columns based on role.

**Implementation:**

```python
import pandas as pd

def mask_pii_columns(df: pd.DataFrame, role: str, pii_columns: list) -> pd.DataFrame:
    """
    Masks PII columns in a DataFrame based on role.

    - admin: no masking
    - analyst: mask PII columns
    - viewer: mask PII columns

    Args:
        df (pd.DataFrame): Original data
        role (str): User role
        pii_columns (list): List of PII column names to mask

    Returns:
        pd.DataFrame: DataFrame with masked columns (or original if admin)
    """

    if role == "admin" or not pii_columns:
        return df.copy()

    df_masked = df.copy()
    for col in pii_columns:
        if col in df_masked.columns:
            df_masked[col] = "[REDACTED]"

    return df_masked
```

---

### Integration Points

**Person 1 calls governance:**
```python
# In intent_parser.py or executor.py after executing a query
from engine.governance import run_governance_checks

governance_result = run_governance_checks(app_definition, role="analyst")
if governance_result["requires_approval"]:
    # Show approval UI (Person 2 handles this)
    pass
```

**Person 2 calls governance & masking:**
```python
# In dashboard.py when rendering data
from engine.governance import run_governance_checks, mask_pii_columns

governance_result = run_governance_checks(app_definition, role=current_user_role, execution_results=results)
pii_columns = governance_result.get("pii_columns_detected", [])
data_df = mask_pii_columns(results["data"], role=current_user_role, pii_columns=pii_columns)

# Display governance checks in UI
st.write("Governance Status:", governance_result["overall_status"])
for check in governance_result["checks"]:
    if check["status"] == "pass":
        st.success(f"{check['rule']}: {check['message']}")
    elif check["status"] == "warning":
        st.warning(f"{check['rule']}: {check['message']}")
    else:
        st.error(f"{check['rule']}: {check['message']}")
```

---

## SECTION 3: THE PRD — DEMO MODE & TEMPLATES

### Demo Mode: Feature Overview

**Goal:** Demonstrate StackForge's full workflow in 3 sequential steps, triggered by a "Demo" button in the app header.

**Architecture:**
- New Streamlit session state variables: `demo_mode` (bool), `demo_step` (int)
- Demo button in header toggles `demo_mode=True` and `demo_step=0`
- Each step advances automatically after the user sees results

---

### Demo Mode Implementation (app.py contributions)

**Step 0: Auto-send Supplier Performance Template**

```python
# In the main app.py, after the header and sidebar

import streamlit as st

# Initialize demo state
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False
    st.session_state.demo_step = 0

# Demo button in header
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("StackForge — AI Data App Factory")
with col3:
    if st.button("🎬 Demo", key="demo_btn"):
        st.session_state.demo_mode = True
        st.session_state.demo_step = 0
        st.rerun()

# DEMO STEP 0: Auto-send template prompt
if st.session_state.demo_mode and st.session_state.demo_step == 0:
    st.info("🎬 Demo Mode Active — Step 1/3: Building from template...")

    # Auto-populate the intent input with Supplier Performance template
    template_prompt = (
        "Create a data app for supplier performance analysis. "
        "Show me a dashboard with: (1) Top 10 suppliers by revenue, "
        "(2) Defect rates by supplier, (3) On-time delivery percentage, "
        "(4) A data table with supplier name, revenue, defect rate, and on-time %."
    )

    # Simulate user sending this prompt
    # (Person 1's intent parser will receive this)
    st.session_state.user_intent = template_prompt
    st.write(f"**Prompt:** {template_prompt}")
    st.write("*Building app from template...*")

    # Advance to step 1 after a brief pause
    import time
    time.sleep(1)
    st.session_state.demo_step = 1
    st.rerun()

# DEMO STEP 1: Auto-send refinement prompt
elif st.session_state.demo_mode and st.session_state.demo_step == 1:
    st.info("🎬 Demo Mode — Step 2/3: Conversational refinement...")

    # Show the initial dashboard (from step 0 — Person 2 has already rendered it)
    # Then show the refinement prompt

    refinement_prompt = (
        "Break down defect analysis by shipping mode and highlight suppliers with defect rates above 5%"
    )

    st.write("**Refinement:** " + refinement_prompt)
    st.write("*Updating dashboard with refinement...*")

    # Advance to step 2 after results are shown
    import time
    time.sleep(1)
    st.session_state.demo_step = 2
    st.rerun()

# DEMO STEP 2: Demo complete
elif st.session_state.demo_mode and st.session_state.demo_step == 2:
    st.success("🎬 Demo Complete!")
    st.write("Demo showcased: Template → Build → Refine → Governance Checks → Role Switching")

    if st.button("End Demo"):
        st.session_state.demo_mode = False
        st.session_state.demo_step = 0
        st.rerun()
```

**Key Points:**
- Step 0 is automatic — just select the template and hit Demo
- Step 1 shows the initial dashboard from Step 0, then applies refinement
- Step 2 marks completion and offers "End Demo" button
- The demo can be run multiple times without requiring setup

---

### Template Library: Six Default Templates

**Location:** `config.py` (Person 1 creates the structure, Person 3 refines the prompts)

**All six templates:**

```python
TEMPLATES = [
    {
        "name": "Supplier Performance",
        "description": "Analyze supplier metrics including revenue, defect rates, and on-time delivery",
        "default_prompt": (
            "Create a data app for supplier performance analysis. "
            "Show me a dashboard with: (1) Top 10 suppliers by revenue, "
            "(2) Defect rates by supplier, (3) On-time delivery percentage, "
            "(4) A data table with supplier name, revenue, defect rate, and on-time %."
        ),
        "icon": "📊"
    },
    {
        "name": "Inventory Optimization",
        "description": "Monitor inventory levels, stock movements, and reorder points",
        "default_prompt": (
            "Build an inventory management dashboard. Display: (1) Current stock levels by product, "
            "(2) Fast-moving vs slow-moving products, (3) Days supply on hand (DSOH), "
            "(4) Reorder point alerts, (5) Inventory turnover ratio by category."
        ),
        "icon": "📦"
    },
    {
        "name": "Supply Chain Cost Breakdown",
        "description": "Visualize cost distribution across procurement, transportation, and labor",
        "default_prompt": (
            "Create a supply chain cost analytics dashboard. Show: (1) Total cost by category (procurement, "
            "transportation, labor, storage), (2) Cost per unit by product, (3) Variance vs budget, "
            "(4) Cost trend over time, (5) Cost heatmap by supplier and region."
        ),
        "icon": "💰"
    },
    {
        "name": "Quality Control Monitor",
        "description": "Track defect rates, quality metrics, and compliance across the supply chain",
        "default_prompt": (
            "Build a quality control dashboard. Include: (1) Defect rate by supplier, "
            "(2) Defects by type (workmanship, material, specification), (3) Rework costs, "
            "(4) On-time delivery correlation with quality, (5) Trend analysis over 12 months."
        ),
        "icon": "✅"
    },
    {
        "name": "Logistics & Shipping Tracker",
        "description": "Monitor shipments, delivery times, and logistics costs in real-time",
        "default_prompt": (
            "Create a logistics tracking dashboard. Display: (1) Shipments in transit (count and value), "
            "(2) Average delivery time by route, (3) Cost per shipment, (4) On-time delivery %, "
            "(5) Bottleneck routes (top 10 delayed corridors)."
        ),
        "icon": "🚚"
    },
    {
        "name": "Executive KPI Summary",
        "description": "High-level view of key performance indicators for supply chain leadership",
        "default_prompt": (
            "Build an executive dashboard with KPIs: (1) Supplier quality score (avg defect rate), "
            "(2) On-time delivery %, (3) Inventory turnover, (4) Supply chain cost as % of revenue, "
            "(5) Procurement cycle time, (6) Customer wait time."
        ),
        "icon": "👨‍💼"
    }
]
```

**Person 3's Template Testing & Refinement Process:**

1. **Hour 10-12 (template testing phase):**
   - Load the app with the Supplier Performance template
   - Send the default prompt through the AI engine
   - Look at the rendered dashboard
   - Ask: Does it show what the prompt asked for? Are the charts correct? Is the data readable?
   - If the dashboard is poor, refine the `default_prompt` text and try again
   - Repeat for all 6 templates

2. **Refinement checklist:**
   - [ ] Supplier Performance: Shows top 10 suppliers, defect rates, on-time %, data table
   - [ ] Inventory Optimization: Shows stock levels, fast/slow movers, DSOH, reorder alerts, turnover
   - [ ] Supply Chain Cost: Shows cost breakdown by category, per unit, variance, trend, heatmap
   - [ ] Quality Control: Shows defect rates, defect types, rework costs, correlation, trends
   - [ ] Logistics & Shipping: Shows in-transit shipments, delivery time, cost, on-time %, bottlenecks
   - [ ] Executive KPI: Shows quality score, on-time %, turnover, cost %, cycle time, wait time

3. **Common issues and fixes:**
   - *Problem:* AI returns "SELECT * FROM table" instead of specific columns
     - *Fix:* Add to prompt: "Only select the columns you need, not SELECT *"
   - *Problem:* Dashboard shows raw numbers without formatting
     - *Fix:* Add to prompt: "Format percentages, currency, and dates clearly"
   - *Problem:* Too many or too few components
     - *Fix:* Adjust the prompt to ask for specific component types (charts, tables, KPI cards)

---

### Audit Logging Enhancement

**Requirement:** Every significant action in the app gets an audit log entry.

**Location:** `audit.py` (new file) or integrated into `app.py`

**Actions to log:**
1. Intent parsing started
2. Intent parsing completed
3. Query execution started
4. Query execution completed
5. Validation checks completed
6. Governance checks completed
7. Role switched
8. Demo mode triggered
9. App approved by admin
10. "Show Engine" toggled

**Audit log entry format:**
```python
{
    "timestamp": "2026-02-28T14:30:45.123Z",
    "action": "intent_parsing_completed",
    "role": "analyst",
    "user_id": "user_123",  # or "demo_user" if in demo mode
    "details": {
        "prompt": "Create a supplier dashboard...",
        "query_count": 3,
        "component_count": 4,
        "status": "success"
    },
    "session_id": "sess_abc123"
}
```

**Implementation:**
```python
# In app.py or audit.py

import json
from datetime import datetime
import streamlit as st

def log_audit(action: str, role: str, details: dict = None):
    """
    Logs an audit entry to both console and (optionally) file/database.

    Args:
        action: Name of the action (e.g., "intent_parsing_completed")
        role: User role (admin, analyst, viewer)
        details: Dictionary of additional details
    """

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "role": role,
        "details": details or {},
        "session_id": st.session_state.get("session_id", "unknown")
    }

    # Log to console
    print(f"[AUDIT] {json.dumps(entry)}")

    # Optionally log to file or database
    # with open("audit.log", "a") as f:
    #     f.write(json.dumps(entry) + "\n")

# Usage in app.py:
# log_audit("intent_parsing_started", role="analyst",
#           details={"prompt": user_intent})
```

**Audit log display in UI (Person 2 can add this to dashboard):**
```python
# Show audit trail in a sidebar or bottom section
st.subheader("Audit Trail")
audit_entries = st.session_state.get("audit_trail", [])
for entry in audit_entries[-10:]:  # Show last 10 entries
    st.write(f"**{entry['action']}** ({entry['role']}) — {entry['timestamp']}")
```

---

## SECTION 4: THE PRD — THE PITCH (PRESENTATION)

### Presentation Overview

**Duration:** 10 minutes
**Audience:** Judges (Koch Supply Chain, Databricks, AWS, tech industry experts)
**Goal:** Demonstrate StackForge as a breakthrough AI Data App Factory

---

### Demo Script (Minute by Minute)

#### [0:00–1:00] The Problem

**What you say:**

"Every day, supply chain teams face the same challenge: they need data-driven insights to optimize costs, improve quality, and accelerate delivery. But getting those insights takes weeks. They write requirements, hand them to IT, IT writes SQL queries, builds dashboards, deploys them, and by the time it's live, the business context has changed.

StackForge solves this by flipping the model: **describe what you want, and get a live, governed data app in seconds.**"

**What the judges should feel:** This is a real problem they or their customers face every day.

---

#### [1:00–2:00] The Solution

**What you say:**

"StackForge is an AI Data App Factory. Here's how it works:

1. **You describe your need.** 'Show me top suppliers by revenue and their defect rates.'
2. **AI parses your intent** and generates SQL queries.
3. **Queries execute** on your supply chain data (DuckDB in this demo, scales to Databricks Spark).
4. **AI renders a live Plotly dashboard** with interactive charts, KPI cards, and data tables.
5. **Governance checks run automatically** — PII detection, role-based access control, compliance checks.
6. **You can refine conversationally.** 'Break that down by shipping mode.' The dashboard updates live.

All without writing a single line of SQL. All with enterprise governance baked in."

**Visual:**
- Point to the five-stage pipeline on the screen (or have a diagram ready)

**What the judges should feel:** This is technically impressive and addresses a real business need.

---

#### [2:00–5:00] Live Demo — Build & Explore

**Setup before demo:**
- Have the StackForge app running in your browser
- Refresh to a clean state (no demo mode yet)

**What you do:**

1. **[2:00–2:30] Click "Demo" button**
   - "Let me show you this in action. I'll click the Demo button, and StackForge will automatically build a data app from a template."
   - Click the 🎬 Demo button
   - App auto-sends: "Create a data app for supplier performance analysis..."
   - The AI engine parses this intent

2. **[2:30–3:00] Show the initial dashboard**
   - First chart: Top 10 Suppliers by Revenue (bar chart)
   - Second chart: Defect Rate by Supplier (bar chart)
   - Third chart: On-Time Delivery % (gauge or KPI card)
   - Data table below with columns: Supplier, Revenue, Defect Rate, On-Time %
   - "Notice the charts are interactive — you can hover to see exact values, zoom, pan."
   - Hover over a bar in the Top 10 chart to show the tooltip

4. **[3:00–3:30] Show the "Show Engine" toggle**
   - Click "Show Engine" or a similar toggle
   - Display the SQL queries that generated the dashboard
   - "You can see exactly what queries the AI generated. No black box. Full transparency."
   - Point to three queries:
     - Query 1: SELECT supplier, revenue FROM suppliers ORDER BY revenue DESC LIMIT 10
     - Query 2: SELECT supplier, defect_rate FROM suppliers
     - Query 3: SELECT supplier, ontime_pct FROM suppliers
   - "All deterministic SQL, all auditable."

5. **[3:30–4:00] Click on the "Refine" input**
   - "Now let's refine this. The initial dashboard is great, but we want more insight. What if we add shipping mode?"
   - The demo auto-populates the refinement prompt (or you can type it)
   - Show: "Break down defect analysis by shipping mode and highlight suppliers with defect rates above 5%"

6. **[4:00–4:30] Watch the dashboard update**
   - The app processes the refinement
   - A new chart appears: Defect Rate by Shipping Mode (bar chart, color-coded by supplier)
   - The data table now includes a Shipping Mode column
   - "The dashboard updated live. No page reload, no waiting. This is the power of conversational AI applied to data."

7. **[4:30–5:00] Show KPI cards and interactivity**
   - Point to KPI cards at the top: "Avg Defect Rate: 2.3%", "On-Time %: 96.1%", etc.
   - Show one more chart interaction: click and drag to zoom into a date range (if there's a time series chart)
   - "All powered by Plotly. Full interactivity, no custom code."

**Backup plan:** If the demo is slow or the refinement doesn't work:
- Pre-cache the results of Step 0 and Step 1
- Show Step 0 result instantly, then do Step 1 refinement
- If Step 1 still fails, show a screenshot of the refined dashboard

---

#### [5:00–7:00] Show Engine + Governance + Role Switching

**What you do:**

1. **[5:00–5:30] Toggle "Show Engine" (if not already shown)**
   - Display the SQL queries, the data flow diagram, and the governance checks
   - Judges see:
     - Three SQL queries (readable, simple, correct)
     - A DAG showing: Intent → Parse → Execute → Validate → Render → Govern
     - Governance checks list (all passing):
       - ✅ PII Detection: pass
       - ✅ Access Control: pass
       - ✅ Query Complexity: pass
       - ✅ Data Quality: pass
       - ✅ Export Control: pass
       - ✅ Audit Trail: pass
   - "Every query, every transformation, every decision is logged and validated."

2. **[5:30–6:00] Switch to Admin role (toggle in top-right sidebar)**
   - "Let's switch roles. I'm now an Admin."
   - Refresh or re-run the governance checks
   - Governance status shows: "Compliant — Admin access to all features"
   - Show the "Approve" button becomes available
   - Click "Approve" to demonstrate the approval workflow
   - "Admins can see full data, approve apps for others, and manage governance."

3. **[6:00–6:30] Switch to Viewer role**
   - Switch role selector to "Viewer"
   - Re-run governance checks
   - Governance status shows: "Review Required — Limited feature access"
   - Point out: PII columns are now masked as [REDACTED]
   - "Viewers see aggregated data only, no raw tables, no exports. Governance is automatic."

4. **[6:30–7:00] Show audit trail**
   - Scroll down or open a panel showing the audit log
   - Show entries:
     - 14:35:22 — Intent parsing completed (analyst)
     - 14:35:25 — Query execution completed (analyst)
     - 14:35:26 — Governance checks passed (analyst)
     - 14:35:28 — Role switched to Admin
     - 14:35:30 — App approved by Admin
     - 14:35:32 — Role switched to Viewer
     - 14:35:35 — Governance checks run with Viewer restrictions
   - "Every action is logged with timestamp, role, and details. Full compliance and traceability."

**What the judges should feel:** This is enterprise-grade governance, not a toy. Compliance and transparency are baked in.

---

#### [7:00–8:30] Technical Depth: The Five-Stage Engine

**What you say (don't show code, just explain):**

"Behind the scenes, StackForge runs a five-stage AI compiler:

**Stage 1: Intent Parsing**
The user says 'Show me top suppliers by revenue.' Our AI parses this into a structured format:
- Entity: Supplier
- Metric: Revenue
- Operation: Top 10
- Aggregation: Sum

**Stage 2: Query Execution**
From that structure, we generate SQL and execute it:
```
SELECT supplier, SUM(revenue) as total_revenue
FROM suppliers
GROUP BY supplier
ORDER BY total_revenue DESC
LIMIT 10
```

**Stage 3: Validation**
We validate: Does the query reference valid columns? Are there any SQL errors? Is the schema correct?

**Stage 4: Rendering**
We take the results and render an interactive Plotly dashboard. We choose the chart type (bar chart for this comparison), set colors, add interactivity.

**Stage 5: Governance**
Finally, governance runs. We check: Is there PII? Is the user's role allowed to see this? Do we need approval? All automatic.

**The secret sauce:** We use function calling to constrain the AI's output at every stage. At parsing, the AI can only output recognized intents. At SQL generation, it can only call our SQL builder functions. This is not a raw LLM talking to your data — it's a governed, constrained AI engine.

**Why this matters:**
- **For Koch:** Your supply chain data stays safe. Governance is automatic, not a manual process.
- **For Databricks:** This architecture scales to Spark. DuckDB is the demo; Spark SQL is production. Same governance, same parser, just a different execution backend.
- **For AWS:** This is API-ready. Streamlit deploys to ECS, EC2, or Lambda. The governance engine is just Python — it runs anywhere."

**Visual aids:**
- Have a diagram of the five-stage pipeline (hand-drawn is fine)
- Show the function calling constraint (optional, only if judges ask)

**What the judges should feel:** This is thoughtful architecture, not just prompt injection. We've built something real.

---

#### [8:30–10:00] Why This Matters + Call to Action

**What you say:**

"Let me tie this back to your business. Koch, you have supply chain teams that need insights. Databricks, you're in the business of turning data into insights. AWS, you power the infrastructure. StackForge is the bridge.

**Why it works:**

1. **It's fast.** Instead of weeks, insights in seconds. Your teams can iterate, explore, and make decisions in real-time.

2. **It's governed.** Enterprise-grade PII detection, role-based access, audit logs. You sleep at night knowing your data is safe.

3. **It's open.** The Show Engine feature means no black-box AI. Judges can see the SQL, the governance checks, the audit trail. Full transparency.

4. **It scales.** This demo runs on DuckDB. Production runs on Databricks or Snowflake. The governance layer is data-source agnostic.

5. **It's conversational.** Not a new tool to learn. Users describe what they want in English, they get a dashboard. No SQL, no dashboard design skills needed.

**The six templates shipped in the box** cover the most common supply chain use cases. But users can create ANY data app from conversation. It's a factory, not a fixed set of dashboards.

**In the next hour, we're going to:**
- Finish testing the template library
- Add a few more refinements to the UI
- Package this for deployment

**And if you're interested in taking this forward,** we've built the foundation. Add more templates, connect to more data sources, integrate with your existing tools. The governance engine scales with you.

StackForge is not a demo. It's the start of a product."

**What the judges should feel:** This is serious, well-thought-out, and has real commercial potential.

---

### Talking Points for Judges

**If a judge asks about Koch (Supply Chain Partner):**

"We built this with your supply chain data in mind. Every template — Supplier Performance, Inventory Optimization, Quality Control — maps to real processes in your business. And the governance engine understands PII and compliance. Your teams can build data apps without IT overhead, and your security team knows exactly what data is being queried and who's accessing it."

**If a judge asks about Databricks (AI + Analytics):**

"DuckDB lets us prototype fast. But the architecture is built for Spark. When you run this on Databricks, the parser and governance stay the same — only the execution backend changes. The five-stage pipeline is data-source agnostic. Function calling constrains the LLM, so you get deterministic, auditable SQL. This is serious data engineering, not just LLM chat."

**If a judge asks about AWS (Infrastructure):**

"Streamlit deploys anywhere — EC2, ECS, or Lambda. The governance engine is just Python, so it's platform-agnostic. We use DuckDB for in-process analytics, which is lightweight and doesn't require a separate cluster. For production, you'd add RDS for audit logs, S3 for query caching, CloudWatch for monitoring. The foundation is here."

**If a judge asks about the AI quality:**

"The AI engine is constrained, not free-form. At every stage — parsing, SQL generation, rendering — we use function calling to limit the model's output. The parser can only return recognized intents. The SQL generator can only call our builder functions. This means the AI can't generate bad SQL, can't access data it shouldn't, can't bypass governance. It's deterministic."

**If a judge asks about security:**

"PII detection runs on every query. Role-based access control is automatic. Audit logs capture every action with timestamp, role, and details. If a user tries to export PII as a viewer, governance fails immediately. If a non-admin tries to deploy an app, it goes to approval queue. This is enterprise governance, not a feature we added as an afterthought."

**If a judge asks about the demo templates:**

"We tested all six with real supply chain data patterns. Supplier Performance, Inventory Optimization, Supply Chain Cost, Quality Control, Logistics & Shipping, and Executive KPI. Each template showcases a different type of query and visualization. Users can pick a template and refine from there, or start from scratch. The templates also serve as proof that the system can handle diverse queries and rendering."

---

### Judging Criteria Alignment

| Criterion | How StackForge Wins |
|-----------|-------------------|
| **Technical Impressiveness** | Five-stage AI compiler with function calling. Not just chat-to-dashboard, but a governed, auditable SQL engine. Show Engine proves it. |
| **Design / UX** | Dark professional theme (no comic sans). Interactive Plotly charts. Conversational refinement. Role switching and governance UI. Audit logs visible. |
| **Completeness** | Full end-to-end pipeline: intent parsing → SQL generation → execution → validation → rendering → governance. All six templates working. Demo mode from template to refinement. |
| **Learning / Knowledge** | Each team member can speak to their domain. Person 1: intent parser, function calling, SQL generation. Person 2: Plotly, Streamlit, responsive dashboard design. Person 3: governance, audit logs, demo preparation. |
| **Presentation** | 10-minute script with a live demo. Clear problem statement, solution explanation, and technical depth. Judges can see how this solves real business problems. |

---

### Backup Plans

**If API is slow or times out:**
1. Pre-cache the results of Step 0 (Supplier Performance template)
2. When you click Demo, instantly show the cached Step 0 dashboard
3. Then run Step 1 (refinement) in the background or skip to the Show Engine section

**If a query fails during demo:**
1. Switch to a different template (e.g., Inventory Optimization)
2. Run that template's demo mode
3. Explanation: "This showcases the same five-stage engine, just with different data"

**If the refinement doesn't work:**
1. Show the initial dashboard is already impressive
2. Skip the refinement step
3. Jump to Show Engine, Governance, and Role Switching
4. Explanation: "The core value is here — AI-generated dashboards with enterprise governance"

**If role switching breaks:**
1. Manually set the role in the Streamlit sidebar
2. Re-run governance checks
3. Show the role-based masking in the data table

**If time is running out:**
1. Skip the detailed five-stage pipeline explanation
2. Keep the demo and governance showcase
3. End with: "The foundation is solid. With more time, we'd add [X feature]."

---

## SECTION 5: ROLE-BASED ACCESS DEEP DIVE

### Access Control Matrix

| Feature | Admin | Analyst | Viewer |
|---------|-------|---------|--------|
| **View raw data tables** | ✅ | ✅ | ❌ (aggregated only) |
| **View PII columns** | ✅ (full) | ❌ (masked) | ❌ (masked) |
| **Deploy apps** | ✅ (instant) | ❌ (requires approval) | ❌ |
| **Export data** | ✅ | ✅ | ❌ |
| **Max components** | Unlimited | 8 | 4 |
| **Approval required** | No | >6 components | Always |
| **View governance detail** | Full checks + details | Summary only | Status only |
| **Approve other users' apps** | ✅ | ❌ | ❌ |
| **Access audit trail** | Full history | Own actions only | Own actions only |
| **Change role settings** | ✅ | ❌ | ❌ |

---

### What Each Role Sees in the UI

#### Admin

**Header:**
- Role badge: "ADMIN"
- All menu items enabled

**Data Area:**
- Can toggle between raw data and aggregated views
- No columns masked
- Full SQL queries visible in Show Engine

**Governance Panel:**
- Shows all checks (pass/warning/fail)
- Shows PII columns detected
- Shows "Overall Status: Compliant / Review Required / Non-Compliant"
- Can click "Approve" button to approve pending apps

**Audit Trail:**
- Sees all actions from all users
- Timestamp, action, role, details, session_id

**Demo Mode:**
- Can run demo mode
- Sees all steps

#### Analyst

**Header:**
- Role badge: "ANALYST"
- Limited menu items (no admin settings)

**Data Area:**
- Can only see aggregated views (no raw tables)
- PII columns show [REDACTED]
- SQL queries visible in Show Engine, but sensitive columns are hidden

**Governance Panel:**
- Shows summary of checks (pass/warning/fail)
- Shows which features require approval
- Does NOT show full details of failed checks
- Cannot approve

**Audit Trail:**
- Sees only own actions
- Timestamp, action, details (but not other users' actions)

**Export:**
- Can export to CSV (governance allows it for analysts)

**Approval Queue:**
- Sees "App requires approval" banner
- Cannot self-approve

#### Viewer

**Header:**
- Role badge: "VIEWER"
- Only "View Dashboard" and "Help" menu items

**Data Area:**
- Can only see aggregated views
- All PII columns masked as [REDACTED]
- SQL queries NOT visible in Show Engine (or heavily redacted)

**Governance Panel:**
- Shows basic status: "Compliant" or "Requires Approval"
- Does NOT show details of checks
- Message: "Contact admin for full governance details"

**Audit Trail:**
- Sees only own view history
- Cannot see when others accessed data

**Actions Disabled:**
- Export button is disabled (greyed out)
- Deploy button is disabled
- Show Engine is disabled or heavily redacted

---

### Governance Enforcement in Code

**Person 2 uses these patterns in dashboard.py:**

```python
import streamlit as st
from engine.governance import run_governance_checks, mask_pii_columns

# Get current role from session state or sidebar
current_role = st.sidebar.selectbox("Role", ["admin", "analyst", "viewer"], key="user_role")

# Run governance checks
governance_result = run_governance_checks(
    app_definition=st.session_state.get("app_definition", {}),
    role=current_role,
    execution_results=st.session_state.get("execution_results", {})
)

# Enforce access control based on role
if current_role == "viewer":
    # Only show aggregated data
    st.info("⚠️ Viewer mode — aggregated data only")

    # Mask PII columns
    pii_cols = governance_result.get("pii_columns_detected", [])
    data = mask_pii_columns(data_df, role=current_role, pii_columns=pii_cols)

    # Hide raw data view
    st.write(data.head(10))

    # Disable Show Engine
    if st.button("Show Engine"):
        st.error("Show Engine is not available for Viewer role")

    # Disable export
    st.button("Export", disabled=True)

elif current_role == "analyst":
    # Can see aggregated and filtered data, but not raw tables

    # Check approval requirement
    if governance_result["requires_approval"]:
        st.warning(f"⚠️ This app requires admin approval ({governance_result['overall_status']})")

        # Show approval summary
        for check in governance_result["checks"]:
            if check["status"] != "pass":
                st.info(f"{check['rule']}: {check['message']}")
    else:
        st.success(f"✅ Governance passed ({governance_result['overall_status']})")

    # Show partial Show Engine
    if st.checkbox("Show Engine (Summary)"):
        for check in governance_result["checks"]:
            status_emoji = "✅" if check["status"] == "pass" else "⚠️" if check["status"] == "warning" else "❌"
            st.write(f"{status_emoji} {check['rule']}: {check['message']}")

    # Allow export
    if st.button("Export"):
        st.download_button(
            label="Download CSV",
            data=data_df.to_csv(index=False),
            file_name="data.csv",
            mime="text/csv"
        )

elif current_role == "admin":
    # Full access

    st.success(f"✅ Governance: {governance_result['overall_status']}")

    # Show full governance
    if st.checkbox("Show Engine (Full)"):
        st.json(governance_result)

        # Show SQL queries
        if "sql_queries" in st.session_state.get("app_definition", {}):
            st.subheader("SQL Queries")
            for i, query in enumerate(st.session_state["app_definition"]["sql_queries"]):
                st.code(query, language="sql")

    # Show raw data option
    if st.checkbox("Show Raw Data"):
        st.write(data_df)

    # Allow export
    if st.button("Export"):
        st.download_button(
            label="Download CSV",
            data=data_df.to_csv(index=False),
            file_name="data.csv",
            mime="text/csv"
        )

    # Approval controls
    if governance_result["requires_approval"]:
        st.warning("This app requires admin approval")
        if st.button("✅ Approve App"):
            st.session_state["app_approved"] = True
            log_audit("app_approved", role=current_role, details={"app_id": st.session_state.get("app_id")})
            st.rerun()
```

---

## SECTION 6: TIMELINE

### Hour 0–2: Build governance.py

**Deliverables:**
- `engine/governance.py` complete with all six check functions
- `run_governance_checks()` working with mock app_definitions
- All return formats correct

**Checklist:**
- [ ] PII Detection function finds email, phone, ssn, birth_date, salary, address, zip, cc, passport, driver_license, name
- [ ] Access Control function validates role permissions
- [ ] Query Complexity function counts components and enforces limits
- [ ] Data Quality function flags SELECT *
- [ ] Export Control function blocks viewer exports
- [ ] Audit Trail function confirms logging active
- [ ] `mask_pii_columns()` function masks columns for non-admin roles
- [ ] All return formats match spec exactly

**Test with mock data:**
```python
# Example test
mock_app_definition = {
    "intent": "Show suppliers with emails",
    "sql_queries": ["SELECT supplier, email FROM suppliers"],
    "components": [{"type": "chart", "name": "Top Suppliers"}],
}

result = run_governance_checks(mock_app_definition, role="analyst")
assert result["overall_status"] == "review_required"
assert "email" in result["pii_columns_detected"]
```

---

### Hour 2–4: Test governance against all 6 templates

**Deliverables:**
- Governance tested against Supplier Performance template
- Governance tested against Inventory Optimization template
- Governance tested against Supply Chain Cost template
- Governance tested against Quality Control template
- Governance tested against Logistics & Shipping template
- Governance tested against Executive KPI template

**For each template:**
1. Create a mock `app_definition` based on the template prompt
2. Run `run_governance_checks()` with admin role → should be "compliant"
3. Run with analyst role → should be "review_required" or "compliant" depending on complexity
4. Run with viewer role → should be "review_required" (viewers need approval)
5. Check that PII detection works if template queries involve PII

---

### Hour 4–6: Audit logging + demo mode

**Deliverables:**
- `audit.py` or audit logging integrated into `app.py`
- Log entry function working
- Demo mode Step 0, Step 1, Step 2 implemented
- Demo button in header triggers demo mode

**Checklist:**
- [ ] `log_audit()` function creates properly formatted entries
- [ ] Timestamps are ISO 8601 + Z
- [ ] Actions being logged: intent_parsing_started, intent_parsing_completed, query_execution_completed, governance_checks_completed, role_switched, demo_mode_triggered, app_approved, show_engine_toggled
- [ ] Demo Step 0: Auto-sends Supplier Performance template prompt
- [ ] Demo Step 1: Shows initial dashboard, auto-sends refinement prompt
- [ ] Demo Step 2: Shows "Demo Complete" message

---

### Hour 6–8: Integration with Person 1 & Person 2

**Deliverables:**
- `governance.py` called from Person 1's engine after intent parsing
- `governance.py` called from Person 2's dashboard before rendering
- `mask_pii_columns()` integrated into Person 2's data rendering
- End-to-end governance flow working

**Integration checklist:**
- [ ] Person 1's executor calls `run_governance_checks()` after executing a query
- [ ] If `requires_approval=True`, show approval UI to Person 2
- [ ] Person 2's dashboard calls `mask_pii_columns()` before displaying data
- [ ] Governance checks displayed in UI with status badges (✅ pass, ⚠️ warning, ❌ fail)
- [ ] Role switching re-triggers governance checks automatically

---

### Hour 8–10: Template testing & refinement

**Deliverables:**
- All 6 templates tested with the AI engine
- Prompts refined if necessary
- Each template produces a valid, useful dashboard

**Testing process for each template:**
1. Open StackForge app
2. Click "Demo"
3. App auto-sends template prompt
4. Observe the rendered dashboard
5. Ask: Does it match the template description? Are the charts readable? Is the data correct?
6. If NO, refine the template's `default_prompt` in `config.py` and retry
7. If YES, move to next template

**Refinement examples:**
- **Supplier Performance:** If chart doesn't show defect rates, add "Include defect rate per supplier as a separate bar chart"
- **Inventory Optimization:** If DSOH is missing, add "Calculate days supply on hand (DSOH) as inventory divided by daily usage"
- **Quality Control:** If rework costs are missing, add "Show rework costs and their trend over 12 months"

---

### Hour 10–12: Demo script + presentation prep

**Deliverables:**
- Minute-by-minute demo script written (see Section 4)
- Presentation talking points written
- Backup plans documented
- Practice run-through completed

**Checklist:**
- [ ] Problem statement (1 min) — conveys real business pain
- [ ] Solution explanation (1 min) — describes five-stage pipeline
- [ ] Live demo script (3 min) — step-by-step actions for demo
- [ ] Show Engine + Governance demo (2 min) — shows transparency
- [ ] Technical depth explanation (1.5 min) — explains why architecture matters
- [ ] Judging criteria alignment (1.5 min) — addresses Koch, Databricks, AWS angles
- [ ] Backup plans documented (failover for slow API, broken queries, etc.)

---

### Hour 12–14: Demo rehearsal + backup plan testing

**Deliverables:**
- 3 full run-throughs of the 10-minute demo
- Backup plan tested (pre-cached results, fallback template)
- Timing locked in (10 min exactly, or slightly under)
- Presentation smooth and confident

**Rehearsal checklist:**
1. First run-through: Full demo, no interruptions, measure time
2. If > 10 min, cut content (probably the technical depth section)
3. Second run-through: Practice with backup plan (e.g., fallback template if demo is slow)
4. Third run-through: Full presentation (problem + solution + demo + talking points)
5. Ask a teammate to "be a judge" and ask hard questions

**Timing targets:**
- [0:00–1:00] Problem statement (60 sec)
- [1:00–2:00] Solution explanation (60 sec)
- [2:00–5:00] Live demo build & explore (180 sec)
- [5:00–7:00] Show Engine + Governance (120 sec)
- [7:00–8:30] Technical depth (90 sec)
- [8:30–10:00] Why it matters + call to action (90 sec)
- **Total: 600 sec = 10 min**

---

### Hour 14–17: Final polish + presentation delivery

**Deliverables:**
- Final CSS/theming polish (dark professional theme)
- Last-minute bug fixes
- Backup plan dry-run
- Team fully prepared for presentation

**Final polish checklist:**
- [ ] Streamlit app theme is dark and professional (no comic sans, readable fonts)
- [ ] Governance checks display cleanly (color-coded status badges)
- [ ] Audit trail is readable and timestamps are visible
- [ ] Demo mode buttons are prominent and easy to click
- [ ] Role switching works smoothly without lag
- [ ] Charts are interactive (hover, zoom, pan)
- [ ] KPI cards are visually distinct from charts

**Presentation day:**
- Hour 14–16: Final rehearsals, troubleshooting
- Hour 16–17: Setup in presentation room, final tests
- Hour 17: Present to judges!

---

## SECTION 7: TESTING CHECKLIST

### Governance Engine Tests

- [ ] `run_governance_checks()` returns "compliant" for simple app with admin role
- [ ] `run_governance_checks()` returns "review_required" for app with PII as analyst
- [ ] `run_governance_checks()` returns "non_compliant" for PII access as viewer
- [ ] `run_governance_checks()` response includes all fields: checks[], requires_approval, pii_columns_detected, overall_status, timestamp, role
- [ ] PII Detection finds email, phone, ssn, birth_date, salary, address, zip, cc, passport, driver_license, name patterns (case-insensitive regex)
- [ ] PII Detection returns "pass" when no PII found
- [ ] PII Detection returns "warning" for admin with PII
- [ ] PII Detection returns "fail" for non-admin with PII
- [ ] Access Control validates admin/analyst/viewer roles
- [ ] Access Control fails if role unknown
- [ ] Query Complexity warning for viewer at 5+ components
- [ ] Query Complexity warning for analyst at 9+ components
- [ ] Query Complexity pass for admin with unlimited components
- [ ] Data Quality flags SELECT * patterns
- [ ] Data Quality pass when no SELECT * found
- [ ] Export Control pass for admin and analyst
- [ ] Export Control fail for viewer export requests
- [ ] Audit Trail always passes
- [ ] `requires_approval` is True when overall_status != "compliant" and role != "admin"
- [ ] `requires_approval` is True when role != "admin" and component_count > 6
- [ ] `mask_pii_columns()` returns original df for admin
- [ ] `mask_pii_columns()` masks columns as [REDACTED] for non-admin

### Demo Mode Tests

- [ ] Demo button appears in header
- [ ] Clicking Demo sets demo_mode=True, demo_step=0
- [ ] Step 0 auto-sends Supplier Performance template prompt
- [ ] Step 1 auto-sends refinement prompt: "Break down defect analysis by shipping mode and highlight suppliers with defect rates above 5%"
- [ ] Step 2 shows "Demo Complete" message
- [ ] "End Demo" button resets demo_mode=False, demo_step=0
- [ ] Demo can be run multiple times in one session
- [ ] Demo mode does not interfere with normal app usage

### Template Tests

- [ ] Supplier Performance template builds dashboard with top 10 suppliers, defect rates, on-time %, data table
- [ ] Inventory Optimization template shows stock levels, fast/slow movers, DSOH, reorder alerts, turnover
- [ ] Supply Chain Cost template shows cost breakdown by category, per unit, variance, trend, heatmap
- [ ] Quality Control template shows defect rates by supplier, defect types, rework costs, correlation, trends
- [ ] Logistics & Shipping template shows in-transit shipments, delivery time, cost, on-time %, bottlenecks
- [ ] Executive KPI template shows quality score, on-time %, turnover, cost %, cycle time, wait time
- [ ] Each template renders without errors
- [ ] Each template's charts are interactive (hover, zoom, pan)
- [ ] Each template's data table has correct columns and values

### Audit Logging Tests

- [ ] Audit entry created for intent_parsing_started
- [ ] Audit entry created for intent_parsing_completed
- [ ] Audit entry created for query_execution_completed
- [ ] Audit entry created for governance_checks_completed
- [ ] Audit entry created for role_switched
- [ ] Audit entry created for demo_mode_triggered
- [ ] Audit entry created for app_approved
- [ ] Audit entry created for show_engine_toggled
- [ ] Each audit entry has: timestamp (ISO 8601 + Z), action, role, details, session_id
- [ ] Timestamps are accurate and in correct format

### Role-Based Access Tests

- [ ] Admin can view raw data tables
- [ ] Admin can see PII columns (not masked)
- [ ] Admin can deploy apps (no approval required)
- [ ] Admin can export data
- [ ] Admin can approve other users' apps
- [ ] Admin sees full governance detail
- [ ] Analyst can view aggregated data (not raw tables)
- [ ] Analyst sees PII columns masked as [REDACTED]
- [ ] Analyst cannot deploy without approval (governance shows requires_approval=True)
- [ ] Analyst can export data
- [ ] Analyst cannot approve apps
- [ ] Analyst sees governance summary only
- [ ] Viewer can view aggregated data only (not raw tables)
- [ ] Viewer sees all PII columns masked as [REDACTED]
- [ ] Viewer cannot deploy (governance shows requires_approval=True)
- [ ] Viewer cannot export (button disabled)
- [ ] Viewer cannot approve
- [ ] Viewer sees governance status only (not details)
- [ ] Role switching re-triggers governance checks
- [ ] Switching to viewer role masks data immediately

### Integration Tests

- [ ] Person 1's intent parser calls `run_governance_checks()` after intent parsing
- [ ] Person 2's dashboard displays governance checks with status badges
- [ ] Person 2's dashboard calls `mask_pii_columns()` before rendering data
- [ ] Approval flow works: non-admin app → requires_approval=True → approval UI shown → admin approves → app enabled
- [ ] Show Engine toggle displays SQL queries and governance checks
- [ ] Role switching in sidebar updates UI immediately (no page reload needed)

### Presentation Tests

- [ ] Problem statement (1 min) is clear and compelling
- [ ] Solution explanation (1 min) describes the five-stage pipeline
- [ ] Live demo runs without crashing (10 min total)
- [ ] Show Engine feature works and displays queries/governance
- [ ] Role switching demo works in front of judges
- [ ] Backup plan (pre-cached demo) is tested and ready
- [ ] Technical talking points (Koch, Databricks, AWS angles) are practiced
- [ ] Presentation fits in 10 minutes (or slightly under)
- [ ] All three team members can answer questions about their domain

---

## FINAL SUMMARY FOR PERSON 3

You are the **Shield** (governance) and the **Story** (presentation). Here's your mission:

1. **Build governance.py (hours 0–4):** Pure Python, no dependencies. This is your domain. Get it right.

2. **Test everything (hours 4–8):** Make sure governance works with all templates and both Person 1's engine and Person 2's dashboard.

3. **Polish the demo (hours 8–12):** Run each template, refine prompts that produce poor results. Write the demo script. Practice the pitch.

4. **Own the presentation (hours 12–17):** 10 minutes, three people, one story. You tell it. You demo it. You answer the governance and architecture questions.

**The judges are looking for:**
- A real solution to a real problem (supply chain teams need dashboards fast)
- Serious technology (five-stage AI compiler, not just chat-to-SQL)
- Enterprise governance (PII detection, role-based access, audit logs)
- A team that knows their stuff (each person owns their domain)

**Your governance engine proves this.** It's not a feature bolted on at the end. It's baked in from the start. Governance is Person 3's superpower.

**Go build something great.**

---

**Document Version:** 1.0
**Last Updated:** 2026-02-28
**Prepared for:** HackUSU 2026, Koch/Databricks/AWS Data App Factory Track
**Team:** StackForge (Person 1, Person 2, Person 3)
