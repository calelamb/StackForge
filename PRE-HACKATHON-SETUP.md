# Pre-Hackathon Setup Prompt: StackForge — Data App Factory
# Feed this to Claude Code BEFORE the event (or as first step during build)

## INSTRUCTIONS

You are setting up a Python project for a hackathon. You are ONLY doing scaffolding and data preparation. Do NOT write any application logic, AI engine code, or UI components. All of that will be written during the hackathon using the CLAUDE-CODE-PRD.md.

---

## STEP 1: CREATE THE PROJECT

```bash
mkdir stackforge
cd stackforge
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

Create `requirements.txt`:

```
streamlit>=1.30.0
openai>=1.12.0
pandas>=2.0.0
plotly>=5.18.0
duckdb>=0.9.0
python-dotenv>=1.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## STEP 2: CREATE DIRECTORY STRUCTURE

```bash
mkdir -p data engine ui utils
touch engine/__init__.py ui/__init__.py utils/__init__.py
```

---

## STEP 3: CREATE ENVIRONMENT VARIABLE TEMPLATE

Create `.env.example`:

```
# OpenAI — get your key at https://platform.openai.com/api-keys
# Needs GPT-5.1 access
OPENAI_API_KEY=sk-your-key-here
```

Create `.env` from the template and add your actual key:

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Create `.gitignore`:

```
.env
venv/
__pycache__/
*.pyc
.streamlit/
```

---

## STEP 4: DOWNLOAD SUPPLY CHAIN DATASET

If the Koch-provided Supply Chain dataset CSV is available, place it at `data/supply_chain.csv`.

If not available yet, the app will generate synthetic data automatically (500 rows of supply chain data with columns: order_id, order_date, supplier, region, product, category, quantity, unit_cost, total_cost, defect_rate, delivery_days, on_time_delivery, shipping_mode, shipping_cost, warehouse_cost).

---

## STEP 5: CREATE MINIMAL STREAMLIT APP (PLACEHOLDER)

Create `app.py`:

```python
import streamlit as st

st.set_page_config(
    page_title="StackForge — Data App Factory",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 StackForge")
st.caption("AI-Powered Data App Factory · HackUSU 2026")
st.info("Application code will be built during the hackathon. See CLAUDE-CODE-PRD.md for the full specification.")
```

---

## STEP 6: INITIALIZE GIT

```bash
git init
git add -A
git commit -m "chore: initial scaffold with dependencies and placeholder app"
```

Connect to GitHub:

```bash
git remote add origin https://github.com/[YOUR-TEAM]/stackforge.git
git push -u origin main
```

---

## STEP 7: VERIFY

1. Run `streamlit run app.py` — should open browser with placeholder page
2. Verify `.env` is in `.gitignore`
3. Verify all dependencies install cleanly
4. Verify all team members can clone and run

---

## WHAT YOU SHOULD HAVE WHEN DONE

```
stackforge/
├── app.py                      # Placeholder Streamlit app
├── requirements.txt            # All dependencies
├── .env.example                # Environment variable template
├── .env                        # Your actual API key (gitignored)
├── .gitignore                  # Ignores .env, venv, __pycache__
├── data/
│   └── supply_chain.csv        # Koch dataset (or will be generated)
├── engine/
│   └── __init__.py             # Empty
├── ui/
│   └── __init__.py             # Empty
└── utils/
    └── __init__.py             # Empty
```

NO application code. NO AI engine. NO UI components. NO prompts. Just the scaffold, data, and dependencies.

When the hackathon starts, feed `CLAUDE-CODE-PRD.md` to Claude Code and it will build everything step by step.
