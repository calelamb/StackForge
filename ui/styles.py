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
    min-height: 120px;
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
    padding: 1.25rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-height: 180px;
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
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}

.template-description {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin: 0;
    flex-grow: 1;
}

.template-governance {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
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

/* Streamlit overrides */
[data-testid="stMetric"] {
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

/* Tab styling */
.stTabs [data-baseweb="tab-list"] button {
    background-color: var(--secondary-bg);
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border-color);
}

.stTabs [aria-selected="true"] {
    background-color: var(--secondary-bg);
    color: var(--accent-indigo) !important;
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
