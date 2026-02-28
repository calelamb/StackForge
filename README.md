# StackForge — HackUSU 2026
## AI Data App Factory

This folder contains the complete PRD and code for the StackForge hackathon project.

### 📋 Files

- **PERSON-2-THE-INTERFACE.md** — Complete UI Layer PRD and code (2,286 lines)
  - Section 1: Claude Code kickoff prompt
  - Section 2: Complete code for 5 UI files (styles.py, chat.py, dashboard.py, engine_view.py, app.py)
  - Section 3: Mock data for development
  - Section 4: Integration contract (app_definition schema)
  - Section 5: 19-hour timeline
  - Section 6: Testing checklist

### 🏗️ Project Structure

```
stackforge/
├── app.py (600+ lines)
├── ui/
│   ├── __init__.py
│   ├── styles.py (500+ lines)
│   ├── chat.py (200 lines)
│   ├── dashboard.py (600+ lines)
│   └── engine_view.py (250+ lines)
```

### 👥 Team Breakdown

- **Person 1:** Engine layer (intent parsing, SQL generation, query execution)
- **Person 2:** UI layer (Streamlit, Plotly charts, dashboard rendering) — USE PERSON-2-THE-INTERFACE.md
- **Person 3:** Governance layer (policy checks, compliance validation)

### 🚀 Quick Start (Person 2)

1. Read Section 1 of PERSON-2-THE-INTERFACE.md
2. Paste the prompt into Claude Code
3. Follow the timeline in Section 5
4. Copy code from Section 2 into your files
5. Start with mock data (Section 3)
6. Test against checklist (Section 6)

### 🔗 Integration Contract

The `app_definition` JSON schema (Section 4) is the contract between:
- **Person 1 (Engine) → Person 2 (UI)**
- **Person 2 (UI) + Person 3 (Governance) → Final App**

### 📊 What Person 2 Builds

- ✅ 8 chart types (KPI, bar, line, pie, scatter, area, table, metric)
- ✅ Responsive dashboard layout with grid grouping
- ✅ Chat interface with 6 template cards
- ✅ Engine view (SQL, data flow, governance, audit tabs)
- ✅ Role selector (admin/analyst/viewer)
- ✅ Filter sidebar (multiselect, date range, number range)
- ✅ Dark theme CSS (Streamlit dark + custom styling)
- ✅ Demo mode (2 auto-prompts)

### 🎨 Design

- **Dark theme:** #0f172a background, #6366f1 indigo accent
- **Responsive:** Works on desktop and tablet
- **Fast:** Renders with mock data immediately
- **Accessible:** Semantic HTML, proper contrast

### ⏱️ Timeline

- Hours 0-1: Setup & styles
- Hours 1-3: Dashboard renderer
- Hours 3-5: Chat & templates
- Hours 5-6: Integration prep
- Hours 6-8: Engine view
- Hours 8-10: Role & demo
- Hours 10-12: Filters & refinement
- Hours 12-14: Polish & testing
- Hours 14-19: Integration with Person 1 & 3

### ✨ Key Principle

**Start with mock data.** Don't wait for Person 1's engine. Build beautiful charts first, plug in real data later. All rendering code is self-contained in Section 2.

---

**Person 2 — Good luck! 🏭**
