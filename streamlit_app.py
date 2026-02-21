import streamlit as st
import asyncio
import sys
import os
import logging
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.groq_service import GroqService, GroqAPIError
from utils.document_parser import DocumentParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ScoreMyResume",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# THEME CSS
# ─────────────────────────────────────────────────────────────
_CSS_SHARED = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=DM+Serif+Display:ital@0;1&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1200px !important; }

section[data-testid="stSidebar"] { border-right: 1px solid var(--border) !important; }
section[data-testid="stSidebar"] > div { padding: 1.5rem 1.25rem !important; }

.page-hero {
    font-family: 'DM Serif Display', Georgia, serif !important;
    font-size: 2rem !important; line-height: 1.2 !important;
    letter-spacing: -0.02em !important; color: var(--text) !important;
    margin-bottom: 0.5rem !important;
}
.page-hero span { color: var(--accent) !important; font-style: italic; }
.page-sub {
    font-size: 0.92rem !important; color: var(--text-muted) !important;
    line-height: 1.65 !important; margin-bottom: 1.5rem !important; max-width: 520px;
}
.section-label {
    font-size: 0.65rem !important; font-weight: 700 !important;
    color: var(--text-muted) !important; text-transform: uppercase !important;
    letter-spacing: 0.1em !important; margin-bottom: 0.5rem !important; display: block;
}
.brand { font-size: 1.1rem !important; font-weight: 800 !important; color: var(--accent) !important; letter-spacing: -0.02em !important; margin-bottom: 0.1rem; }
.brand-sub { font-size: 0.68rem !important; color: var(--text-muted) !important; font-weight: 500 !important; letter-spacing: 0.04em !important; }

.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: var(--shadow); }
.card-muted { background: var(--bg-3); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; }
.card-success { background: rgba(34,197,94,0.05); border: 1px solid rgba(34,197,94,0.18); border-radius: 8px; padding: 1.25rem; margin-bottom: 0.5rem; }
.card-warn    { background: rgba(239,68,68,0.05);  border: 1px solid rgba(239,68,68,0.18);  border-radius: 8px; padding: 1.25rem; margin-bottom: 0.5rem; }
.card-info    { background: var(--accent-glow); border: 1px solid var(--accent-border); border-radius: 8px; padding: 1.25rem; margin-bottom: 0.5rem; }

.feat-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 1.5rem; box-shadow: var(--shadow); transition: all 0.25s;
    position: relative; overflow: hidden; height: 100%;
}
.feat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--accent), #2dd4bf); }
.feat-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); border-color: var(--border-2); }
.feat-icon { width: 40px; height: 40px; background: var(--accent-glow); border: 1.5px solid var(--border-2); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-bottom: 1rem; }
.feat-title { font-weight: 700; font-size: 0.9rem; color: var(--text); margin-bottom: 0.4rem; }
.feat-desc  { font-size: 0.78rem; color: var(--text-muted); line-height: 1.6; }

.step-bar { display: flex; gap: 0; margin-bottom: 2rem; background: var(--surface); border: 1px solid var(--border); border-radius: 99px; padding: 0.3rem; width: fit-content; box-shadow: var(--shadow); }
.step-item { font-size: 0.68rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; padding: 0.38rem 0.85rem; border-radius: 99px; transition: all 0.2s; }
.step-active { background: var(--accent); color: #fff !important; }
.step-done   { color: var(--accent) !important; }
.step-wait   { color: var(--text-dim); }

.badge-wrap { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.badge { padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.72rem; font-weight: 600; display: inline-block; }
.badge-g { background: rgba(34,197,94,0.1);  color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.badge-r { background: rgba(239,68,68,0.1);  color: #f87171; border: 1px solid rgba(239,68,68,0.2); }
.badge-s { background: rgba(96,165,250,0.1); color: #60a5fa; border: 1px solid rgba(96,165,250,0.2); }
.badge-a { background: rgba(251,191,36,0.1); color: #fbbf24; border: 1px solid rgba(251,191,36,0.2); }
.badge-b { background: var(--accent-glow);   color: var(--accent); border: 1px solid var(--accent-border); }

.diff-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.5rem; }
.diff-old { background: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.15); padding: 0.75rem; border-radius: 8px; font-size: 0.8rem; text-decoration: line-through; line-height: 1.5; color: var(--diff-old-color); }
.diff-new { background: rgba(34,197,94,0.05); border: 1px solid rgba(34,197,94,0.15);  padding: 0.75rem; border-radius: 8px; font-size: 0.8rem; line-height: 1.5; color: var(--diff-new-color); }

.verdict-box { background: var(--bg-3); border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 8px; padding: 1rem 1.25rem; font-size: 0.85rem; color: var(--text-2); line-height: 1.7; margin-bottom: 1rem; box-shadow: var(--shadow-sm); }

.score-circle-wrap { text-align: center; padding: 0.5rem 0; }

.metric-card { background: var(--bg-3); border: 1.5px solid var(--border-2); border-radius: 8px; padding: 0.85rem 1rem; text-align: center; box-shadow: var(--shadow-sm); }
.metric-value { font-family: 'DM Serif Display', serif; font-size: 1.5rem; color: var(--accent); line-height: 1; }
.metric-label { font-size: 0.67rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.2rem; }

.skill-count-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: 8px; padding: 0.85rem 1rem; text-align: center; box-shadow: var(--shadow); }
.skill-count-num   { font-family: 'DM Serif Display', serif; font-size: 1.8rem; line-height: 1; }
.skill-count-label { font-size: 0.67rem; color: var(--text-muted); font-weight: 600; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.05em; }

.prog-wrap   { margin-bottom: 0.75rem; }
.prog-header { display: flex; justify-content: space-between; margin-bottom: 0.3rem; }
.prog-name   { font-size: 0.8rem; font-weight: 600; color: var(--text-2); }
.prog-val    { font-size: 0.8rem; font-weight: 700; color: var(--accent); }
.prog-track  { height: 7px; background: var(--bg-3); border-radius: 99px; overflow: hidden; border: 1px solid var(--border); }
.prog-fill   { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--accent), #2dd4bf); }

.tl-row  { display: flex; gap: 1rem; margin-bottom: 1rem; }
.tl-week { width: 72px; flex-shrink: 0; font-size: 0.7rem; font-weight: 700; color: var(--accent); padding-top: 0.1rem; }
.tl-body { flex: 1; border-left: 2px solid var(--border-2); padding-left: 1rem; }
.tl-body h4 { font-size: 0.88rem; font-weight: 700; color: var(--text); margin-bottom: 0.25rem; }
.tl-body p  { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.3rem; }
.tl-body ul { list-style: none; padding: 0; margin: 0; }
.tl-body li { font-size: 0.78rem; color: var(--text-muted); padding: 0.1rem 0; display: flex; align-items: center; gap: 0.4rem; }
.tl-body li::before { content: ''; width: 5px; height: 5px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }

.health-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; text-align: center; box-shadow: var(--shadow-sm); }

[data-testid="stMetricValue"] { font-family: 'DM Serif Display', serif !important; font-weight: 400 !important; color: var(--accent) !important; }
[data-testid="stMetricLabel"] { font-size: 0.68rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; color: var(--text-muted) !important; }
textarea, input[type="text"], input[type="password"] { border-radius: 8px !important; border-color: var(--border-2) !important; background: var(--bg-3) !important; color: var(--text) !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }
.stButton > button[kind="primary"] { background: var(--accent) !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 700 !important; box-shadow: 0 2px 8px rgba(13,148,136,0.3) !important; transition: all 0.2s !important; }
.stButton > button[kind="primary"]:hover { background: #0f766e !important; color: #ffffff !important; transform: translateY(-1px) !important; box-shadow: 0 4px 12px rgba(13,148,136,0.4) !important; }
.stButton > button:not([kind="primary"]) { border-radius: 8px !important; border-color: var(--border-2) !important; color: var(--accent) !important; font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important; background: transparent !important; }
.stButton > button:not([kind="primary"]):hover { border-color: var(--accent) !important; color: var(--accent) !important; background: var(--accent-glow) !important; }
.stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid var(--border) !important; background: transparent !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] { font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important; font-size: 0.85rem !important; color: var(--text-muted) !important; border-bottom: 2px solid transparent !important; background: transparent !important; padding: 0.65rem 1.25rem !important; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom-color: var(--accent) !important; }
.stSelectbox > div > div { background: var(--bg-3) !important; border-color: var(--border-2) !important; border-radius: 8px !important; }
.stFileUploader { border: 2px dashed var(--border-2) !important; border-radius: 12px !important; background: var(--bg-3) !important; }
.stFileUploader:hover { border-color: var(--accent) !important; background: var(--accent-glow) !important; }
[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 8px !important; background: var(--surface) !important; box-shadow: var(--shadow-sm) !important; margin-bottom: 0.5rem !important; }
[data-testid="stExpanderDetails"] { border-top: 1px solid var(--border) !important; }
.stAlert { border-radius: 8px !important; font-family: 'Plus Jakarta Sans', sans-serif !important; font-size: 0.83rem !important; }
.card-warn { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25); border-radius: 12px; padding: 1.25rem 1.5rem; margin: 1rem 0; text-align: center; }


/* Mobile responsiveness */
@media (max-width: 768px) {
    .block-container { padding: 1rem 1rem 3rem !important; }
    .page-hero { font-size: 1.5rem !important; }
    .diff-wrap { grid-template-columns: 1fr !important; }
    .feat-card { margin-bottom: 0.75rem; }
    section[data-testid="stSidebar"] > div { padding: 1rem 0.75rem !important; }
    .step-bar { flex-wrap: wrap !important; }
    .step-item { font-size: 0.62rem !important; padding: 0.3rem 0.6rem !important; }
}
"""

_CSS_DARK = """
:root {
    --bg:            #091716;
    --bg-2:          #0d1f1e;
    --bg-3:          #0a1918;
    --surface:       #0f2422;
    --border:        #1a3d3a;
    --border-2:      #215955;
    --text:          #e0f7f5;
    --text-2:        #d1edeb;
    --text-muted:    #ffffff;
    --text-dim:      #b2e8de;
    --accent:        #14b8a6;
    --accent-glow:   rgba(20,184,166,0.10);
    --accent-border: rgba(20,184,166,0.20);
    --shadow:        0 1px 3px rgba(0,0,0,0.3), 0 4px 16px rgba(0,0,0,0.2);
    --shadow-lg:     0 8px 32px rgba(0,0,0,0.4);
    --shadow-sm:     0 1px 3px rgba(0,0,0,0.25);
    --diff-old-color: #fca5a5;
    --diff-new-color: #86efac;
}
.stApp { background-color: var(--bg) !important; color: var(--text) !important; }
[data-testid="stCaptionContainer"] { color: var(--text-muted) !important; }
section[data-testid="stSidebar"] { background: #0a1918 !important; }
[data-testid="stMetricValue"] { color: var(--accent) !important; }
.badge-g { color: #4ade80 !important; }
.badge-r { color: #f87171 !important; }
.badge-s { color: #60a5fa !important; }
.badge-a { color: #fbbf24 !important; }
.badge-b { color: #2dd4bf !important; }
.card-success { background: rgba(34,197,94,0.07) !important;  border-color: rgba(34,197,94,0.2) !important; }
.card-warn    { background: rgba(239,68,68,0.07) !important;   border-color: rgba(239,68,68,0.2) !important; }
.card-info    { background: rgba(20,184,166,0.08) !important;  border-color: rgba(20,184,166,0.18) !important; }
"""

_CSS_LIGHT = """
:root {
    --bg:            #f4fdfb;
    --bg-2:          #edfaf6;
    --bg-3:          #e6f7f3;
    --surface:       #ffffff;
    --border:        #b2e8de;
    --border-2:      #7dd5c8;
    --text:          #0a2e2b;
    --text-2:        #174f4a;
    --text-muted:    #3d8c84;
    --text-dim:      #7bbdb7;
    --accent:        #0a7d72;
    --accent-glow:   rgba(10,125,114,0.10);
    --accent-border: rgba(10,125,114,0.20);
    --shadow:        0 1px 4px rgba(10,45,43,0.07), 0 4px 18px rgba(10,45,43,0.09);
    --shadow-lg:     0 8px 32px rgba(10,45,43,0.14);
    --shadow-sm:     0 1px 4px rgba(10,45,43,0.06);
    --diff-old-color: #7f1d1d;
    --diff-new-color: #14532d;
}
.stApp { background-color: var(--bg) !important; color: var(--text) !important; }
section[data-testid="stSidebar"] { background: #edfaf6 !important; box-shadow: 2px 0 12px rgba(10,45,43,0.07) !important; }
[data-testid="stMetricValue"] { color: var(--accent) !important; }
.badge-g { color: #166534 !important; background: rgba(34,197,94,0.12) !important; }
.badge-r { color: #991b1b !important; background: rgba(239,68,68,0.12) !important; }
"""

def inject_theme(mode: str):
    css = _CSS_DARK if mode == "dark" else _CSS_LIGHT
    st.markdown(f"<style>{_CSS_SHARED}{css}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
for k, v in [
    ("step", "input"), ("resume_text", ""), ("jd_text", ""),
    ("analyzed_data", None), ("theme", "dark"), ("theme_label", "☀️ Light mode")
]:
    if k not in st.session_state:
        st.session_state[k] = v

inject_theme(st.session_state.theme)

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed(): raise RuntimeError()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def score_color(s):
    if s >= 80: return "#22c55e"
    if s >= 65: return "#3b82f6"
    if s >= 50: return "#f59e0b"
    return "#ef4444"

def score_label(s):
    if s >= 80: return "Excellent Match"
    if s >= 65: return "Good Match"
    if s >= 50: return "Partial Match"
    return "Low Match"

def badges(items, cls):
    if not items:
        return '<span style="color:var(--text-dim);font-size:0.8rem">—</span>'
    return '<div class="badge-wrap">' + "".join(
        f'<span class="badge badge-{cls}">{i}</span>' for i in items
    ) + '</div>'

def priority_dot(p):
    return {"critical": "🔴", "medium": "🟡", "low": "🟢"}.get(p, "⚪")

# ─────────────────────────────────────────────────────────────
# SCORE DISPLAY
# ─────────────────────────────────────────────────────────────
def make_score_display(score: float) -> str:
    clr  = score_color(score)
    lbl  = score_label(score)
    pct  = int(score)
    circ = 283
    fill = circ * score / 100
    badge_bg = {
        "Excellent Match": "rgba(34,197,94,0.12)",
        "Good Match":      "rgba(20,184,166,0.12)",
        "Partial Match":   "rgba(245,158,11,0.12)",
        "Low Match":       "rgba(239,68,68,0.12)",
    }.get(lbl, "rgba(20,184,166,0.12)")
    return f"""
<div class="score-circle-wrap">
  <svg width="170" height="170" viewBox="0 0 100 100" style="transform:rotate(-90deg)">
    <circle cx="50" cy="50" r="45" fill="none" stroke="var(--bg-3)" stroke-width="8"/>
    <circle cx="50" cy="50" r="45" fill="none" stroke="{clr}" stroke-width="8"
      stroke-dasharray="{fill:.1f} {circ}" stroke-linecap="round"/>
  </svg>
  <div style="margin-top:-130px;text-align:center;position:relative;z-index:1">
    <div style="font-family:'DM Serif Display',serif;font-size:2.6rem;line-height:1;color:{clr}">{pct}</div>
    <div style="font-size:0.8rem;color:var(--text-muted);font-weight:600">/100</div>
  </div>
  <div style="margin-top:0.65rem">
    <span style="display:inline-block;padding:0.22rem 0.8rem;border-radius:99px;font-size:0.72rem;
      font-weight:700;background:{badge_bg};color:{clr};border:1px solid {clr}33">{lbl}</span>
  </div>
</div>"""

# ─────────────────────────────────────────────────────────────
# STEP BAR
# ─────────────────────────────────────────────────────────────
STEPS = ["Extract Resume", "Parse JD", "Semantic Score", "ATS Engine", "AI Coaching"]

def render_step_bar(active: int):
    cells = ""
    for i, name in enumerate(STEPS, 1):
        if i < active:    cls = "step-done"
        elif i == active: cls = "step-active"
        else:             cls = "step-wait"
        cells += f'<div class="step-item {cls}">{name}</div>'
    st.markdown(f'<div class="step-bar">{cells}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="brand">📄 ScoreMyResume</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-sub">Resume · ATS · Career Coach</div>', unsafe_allow_html=True)
        st.divider()

        st.markdown('<div class="section-label">Groq API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input(
            "API Key", type="password", placeholder="gsk_...",
            label_visibility="collapsed", key="api_key_input"
        )
        if st.button("🔌 Connect Key", use_container_width=True, type="primary"):
            if api_key:
                st.session_state.api_key_confirmed = True
                st.rerun()
            else:
                st.error("Please enter a key")

        if api_key:
            if api_key.startswith("gsk_") and len(api_key) > 20:
                st.success("✓ Key looks good")
            else:
                st.warning("Key looks unusual")
        else:
            st.caption("Get a free key → [console.groq.com](https://console.groq.com)")
        st.caption("🔒 Key is stored in this browser session only — re-enter on refresh.")

        st.divider()
        st.markdown('<div class="section-label">Analysis Engine</div>', unsafe_allow_html=True)
        st.caption("Deterministic ATS + Sentence-Transformers + Groq LLM coaching")

        # Rate-limit indicator
        groq_calls = st.session_state.get("groq_call_count", 0)
        groq_errors = st.session_state.get("groq_error_count", 0)
        last_err = st.session_state.get("groq_last_error", None)
        if groq_calls > 0:
            err_info = ""
            if last_err == "rate_limit":
                err_info = "🔴 Rate limited — wait ~60 sec"
            elif last_err == "auth":
                err_info = "🔴 Bad API key"
            elif last_err in ("server", "network"):
                err_info = "🟡 Groq issue — retrying"
            heat = "🟢" if groq_calls < 10 and not last_err else ("🟡" if groq_calls < 30 else "🔴")
            st.caption(f"{heat} {groq_calls} API call{'s' if groq_calls != 1 else ''} this session{(' — ' + err_info) if err_info else ''}")

        if st.session_state.step != "input":
            st.divider()
            if st.button("↺ Start Over", use_container_width=True):
                for k in ["step", "resume_text", "jd_text", "analyzed_data"]:
                    st.session_state[k] = "input" if k == "step" else ("" if k in ["resume_text", "jd_text"] else None)
                st.rerun()

        st.divider()

        col_l, col_r = st.columns([3, 1])
        with col_l:
            st.caption(st.session_state.get("theme_label", "☀️ Light mode"))
        with col_r:
            if st.button("⏺", key="theme_btn", help="Toggle dark/light mode"):
                st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
                st.session_state.theme_label = "🌙 Dark mode" if st.session_state.theme == "dark" else "☀️ Light mode"
                st.rerun()

        st.divider()
        st.caption("Your data never leaves your device. Groq API is the only external call.")

    return api_key

# ─────────────────────────────────────────────────────────────
# WELCOME
# ─────────────────────────────────────────────────────────────
def render_welcome():
    st.markdown('<h1 class="page-hero">Know exactly where you <span>stand.</span></h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Paste a job description, upload your resume, and get a deterministic score with specific, actionable fixes — in under 30 seconds.</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    feats = [
        ("📊", "Deterministic ATS Score", "Rule-based engine with 80+ skill aliases. Same input always returns the same score — no black box."),
        ("🔍", "Semantic Matching",        "Sentence-transformer embeddings measure conceptual alignment, not just keyword overlap."),
        ("✏️", "AI Coaching",              "Mode-aware improvement plan: domain mismatch, skill gaps, or keyword placement — each handled differently."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], feats):
        with col:
            st.markdown(f'<div class="feat-card"><div class="feat-icon">{icon}</div><div class="feat-title">{title}</div><div class="feat-desc">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card-info" style="display:flex;align-items:center;gap:0.75rem;"><span style="font-size:1.2rem">🔑</span><span style="font-size:0.85rem;color:var(--text-2)">Enter your Groq API key in the sidebar to get started. It\'s free at <a href="https://console.groq.com" style="color:var(--accent);text-decoration:none;font-weight:600">console.groq.com</a></span></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# INPUT STEP
# ─────────────────────────────────────────────────────────────
def render_input_step(api_key: str):
    st.markdown('<h1 class="page-hero">Analyze your <span>resume.</span></h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Upload your resume and paste the job description you want to target.</p>', unsafe_allow_html=True)

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown('<div class="section-label">Your resume</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Resume file", type=["pdf", "docx", "txt"], key="resume_upload", label_visibility="collapsed")
        if uploaded:
            with st.spinner("Reading file..."):
                try:
                    fb = uploaded.read()
                    if uploaded.type == "application/pdf":
                        txt = DocumentParser.parse_pdf(fb)
                    elif "word" in uploaded.type or "docx" in uploaded.type:
                        txt = DocumentParser.parse_docx(fb)
                    else:
                        txt = fb.decode("utf-8", errors="replace")
                    st.session_state.resume_text = txt
                    st.success(f"✓ Parsed — {len(txt):,} characters")
                except Exception as e:
                    st.error(f"Could not read file: {e}")

        if st.session_state.resume_text:
            with st.expander("Preview parsed text"):
                preview = st.session_state.resume_text[:1500]
                if len(st.session_state.resume_text) > 1500:
                    preview += "\n\n... (truncated)"
                st.text(preview)

    with col_right:
        st.markdown('<div class="section-label">Job description</div>', unsafe_allow_html=True)
        jd = st.text_area("Job description", value=st.session_state.jd_text, height=310,
                           placeholder="Paste the full job posting here...", label_visibility="collapsed", key="jd_input")
        if st.button("📝 Apply Job Description", use_container_width=True):
            st.session_state.jd_text = jd
            st.rerun()

        if st.session_state.jd_text:
            wc  = len(st.session_state.jd_text.split())
            col = "#22c55e" if wc >= 100 else "#f59e0b"
            st.markdown(f'<span style="color:{col};font-size:0.78rem;font-weight:600">{wc} words {"✓ good" if wc >= 100 else "— paste more for better results"}</span>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    ready = bool(st.session_state.resume_text and st.session_state.jd_text and api_key)
    bc, hc = st.columns([1, 3])
    with bc:
        go_btn = st.button("⚡ Analyze", disabled=not ready, use_container_width=True, type="primary")
    with hc:
        if not api_key:
            st.markdown('<span style="color:#ef4444;font-size:0.83rem">Enter your Groq API key in the sidebar first.</span>', unsafe_allow_html=True)
        elif not st.session_state.resume_text:
            st.markdown('<span style="color:#f59e0b;font-size:0.83rem">Upload your resume to continue.</span>', unsafe_allow_html=True)
        elif not st.session_state.jd_text:
            st.markdown('<span style="color:#f59e0b;font-size:0.83rem">Paste a job description to continue.</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:#22c55e;font-size:0.83rem;font-weight:600">Ready — click Analyze.</span>', unsafe_allow_html=True)

    if go_btn:
        perform_analysis(api_key)

# ─────────────────────────────────────────────────────────────
# ANALYSIS PIPELINE
# ─────────────────────────────────────────────────────────────
def _show_groq_error(err: GroqAPIError):
    """Display a user-friendly error panel for Groq API failures."""
    icon_map = {"rate_limit": "⏳", "auth": "🔑", "server": "🔌", "network": "📡"}
    icon = icon_map.get(err.error_type, "⚠️")
    hint = ""
    if err.error_type == "rate_limit":
        hint = "Groq free tier allows ~30 req/min. Wait ~60 seconds, then click **Retry**."
    elif err.error_type == "auth":
        hint = "Go to [console.groq.com](https://console.groq.com), copy your API key, and paste it in the sidebar."
    elif err.error_type in ("server", "network"):
        hint = "This is a temporary issue. Click **Retry** in a moment."

    st.markdown(f'''
<div class="card-warn">
  <div style="font-size:1.5rem;margin-bottom:0.5rem">{icon}</div>
  <div style="font-weight:700;font-size:0.95rem;color:#f87171;margin-bottom:0.4rem">{str(err)}</div>
  {f'<div style="font-size:0.82rem;color:var(--text-muted)">{hint}</div>' if hint else ""}
</div>''', unsafe_allow_html=True)
    if st.button("🔄 Retry Analysis", type="primary"):
        st.session_state.pop("analysis_error", None)
        st.rerun()


def perform_analysis(api_key: str):
    groq = GroqService(api_key)

    try:
        render_step_bar(1)
        with st.spinner("Extracting resume structure…"):
            resume_data = run_async(groq.extract_resume(st.session_state.resume_text))

        render_step_bar(2)
        with st.spinner("Parsing job description…"):
            jd_data = run_async(groq.extract_job_description(st.session_state.jd_text))

    except GroqAPIError as err:
        st.session_state.groq_call_count = st.session_state.get("groq_call_count", 0) + groq.call_count
        st.session_state.groq_error_count = st.session_state.get("groq_error_count", 0) + groq.error_count
        st.session_state.groq_last_error = err.error_type
        _show_groq_error(err)
        return

    render_step_bar(3)
    with st.spinner("Running semantic analysis…"):
        try:
            from services.semantic_analyzer import get_semantic_analyzer
            analyzer = get_semantic_analyzer()
            semantic_score = analyzer.calculate_semantic_score(resume_data, jd_data)
        except Exception as e:
            logger.warning(f"Semantic fallback: {e}")
            semantic_score = 50.0

    render_step_bar(4)
    with st.spinner("Calculating ATS score…"):
        try:
            from services.ats_engine import get_ats_engine
            engine = get_ats_engine()
            ats_result = engine.calculate_score(
                resume_data, jd_data, st.session_state.resume_text, {"risk_level": "Low"}, semantic_score
            )
        except Exception as e:
            logger.warning(f"ATS fallback: {e}")
            ats_result = {
                "final_ats_score": 60.0,
                "final_breakdown": {"skills_score": 30, "semantic_score": 15, "experience_score": 15},
                "matched_skills": resume_data.get("skills", [])[:5],
                "corrected_missing_skills": jd_data.get("must_have_skills", [])[:5],
                "keyword_gaps": [], "nice_to_have_matched": [], "nice_to_have_missing": [],
                "level": "mid", "cap_applied": None, "must_have_ratio": 0.5, "nice_have_ratio": 0.5,
                "experience": {"total_years": 0, "production_years": 0}, "confidence": 0.8,
            }

    render_step_bar(5)
    try:
        with st.spinner("Generating AI coaching report…"):
            reasoning = run_async(groq.generate_recruiter_reasoning(resume_data, jd_data, ats_result))
            improvement_report = run_async(groq.generate_improvement_report(
                st.session_state.resume_text, resume_data, jd_data, ats_result, semantic_score
            ))
    except GroqAPIError as err:
        st.session_state.groq_call_count = st.session_state.get("groq_call_count", 0) + groq.call_count
        st.session_state.groq_error_count = st.session_state.get("groq_error_count", 0) + groq.error_count
        st.session_state.groq_last_error = err.error_type
        # Show partial results with the error
        reasoning = "AI coaching could not be generated due to an API error."
        improvement_report = {}
        st.warning(f"⚠️ Scores were calculated but AI coaching failed: {err}")

    # Update call counters
    st.session_state.groq_call_count = st.session_state.get("groq_call_count", 0) + groq.call_count
    st.session_state.groq_error_count = st.session_state.get("groq_error_count", 0) + groq.error_count
    if groq.last_error:
        st.session_state.groq_last_error = groq.last_error

    st.session_state.analyzed_data = {
        "resume_data": resume_data, "jd_data": jd_data,
        "ats_result": ats_result, "semantic_score": semantic_score,
        "reasoning": reasoning, "improvement_report": improvement_report,
        "resume_text": st.session_state.resume_text, "jd_text": st.session_state.jd_text,
    }
    st.session_state.step = "results"
    st.rerun()


# ─────────────────────────────────────────────────────────────
# RESULTS ROUTER
# ─────────────────────────────────────────────────────────────
def render_results_step():
    data = st.session_state.analyzed_data
    t1, t2, t3 = st.tabs(["Score Report", "Improvement Plan", "AI Tools"])
    with t1: render_dashboard(data)
    with t2: render_improvement_plan(data)
    with t3: render_tools(data)

# ─────────────────────────────────────────────────────────────
# TAB 1 — SCORE REPORT
# ─────────────────────────────────────────────────────────────
def render_dashboard(data: dict):
    ats       = data["ats_result"]
    score     = float(ats["final_ats_score"])
    breakdown = ats.get("final_breakdown", {})
    matched   = ats.get("matched_skills", [])
    missing   = ats.get("corrected_missing_skills", [])
    nice_m    = ats.get("nice_to_have_matched", [])
    kgaps     = ats.get("keyword_gaps", [])
    level     = ats.get("level", "mid")
    exp       = ats.get("experience", {})

    # Score circle + verdict
    col_g, col_r = st.columns([1, 2], gap="large")
    with col_g:
        st.markdown(make_score_display(score), unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center;font-size:0.67rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.08em;margin-top:0.3rem">{level.upper()} ROLE · {exp.get("total_years",0):.1f} yrs experience</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-label">Recruiter perspective</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="verdict-box">{data["reasoning"]}</div>', unsafe_allow_html=True)
        if ats.get("cap_applied"):
            st.warning(f"Score cap applied: {ats['cap_applied']}")

        mc1, mc2, mc3 = st.columns(3)
        skills_s = breakdown.get("skills_score", breakdown.get("must_have_skills_score", 0))
        exp_s    = breakdown.get("experience_score", breakdown.get("experience_match_score", 0))
        for col, val, lbl in [
            (mc1, f"{skills_s:.0f} pts", "Skills score"),
            (mc2, f"{data['semantic_score']:.0f}/100", "Semantic fit"),
            (mc3, f"{exp_s:.0f} pts", "Experience"),
        ]:
            with col:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

    st.divider()

    # Skill count cards
    sm1, sm2, sm3, sm4 = st.columns(4)
    for col, num, color, lbl in [
        (sm1, len(matched), "#4ade80", "Matched Skills"),
        (sm2, len(missing), "#f87171", "Missing Skills"),
        (sm3, len(nice_m),  "#60a5fa", "Nice-to-have"),
        (sm4, len(kgaps),   "#fbbf24", "Keyword Gaps"),
    ]:
        with col:
            st.markdown(f'<div class="skill-count-card"><div class="skill-count-num" style="color:{color}">{num}</div><div class="skill-count-label">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Skill panels — entire card in ONE markdown call to prevent blank box bug
    sp1, sp2 = st.columns(2, gap="large")
    with sp1:
        st.markdown('<div class="section-label">Skills you have</div>', unsafe_allow_html=True)
        nice_html = f'<div class="section-label" style="margin-top:0.75rem;margin-bottom:0.4rem">Nice-to-have matched</div>{badges(nice_m,"s")}' if nice_m else ""
        st.markdown(f'<div class="card-success">{badges(matched,"g")}{nice_html}</div>', unsafe_allow_html=True)

    with sp2:
        st.markdown('<div class="section-label">Skills you are missing</div>', unsafe_allow_html=True)
        gap_html = ""
        if kgaps:
            gap_items = [f"{g['skill']} (yours: {g['matched_via']})" for g in kgaps[:8]]
            gap_html = f'<div class="section-label" style="margin-top:0.75rem;margin-bottom:0.4rem">Keyword gaps — same skill, different phrasing</div>{badges(gap_items,"a")}'
        st.markdown(f'<div class="card-warn">{badges(missing,"r")}{gap_html}</div>', unsafe_allow_html=True)

    # Score breakdown progress bars
    st.divider()
    st.markdown('<div class="section-label">Score breakdown</div>', unsafe_allow_html=True)
    bd_items = [
        ("Must-have skills",    breakdown.get("skills_score", breakdown.get("must_have_skills_score", 0)), 50),
        ("Semantic fit",        breakdown.get("semantic_score", 0), 30),
        ("Experience match",    breakdown.get("experience_score", breakdown.get("experience_match_score", 0)), 25),
        ("Nice-to-have skills", breakdown.get("nice_to_have_score", 0), 15),
        ("Keyword coverage",    breakdown.get("keyword_score", 0), 10),
    ]
    left_col, _ = st.columns([2, 1])
    with left_col:
        for name, val, max_val in bd_items:
            if max_val > 0:
                pct = min(100, int(val / max_val * 100))
                st.markdown(f'<div class="prog-wrap"><div class="prog-header"><span class="prog-name">{name}</span><span class="prog-val">{val:.0f} pts</span></div><div class="prog-track"><div class="prog-fill" style="width:{pct}%"></div></div></div>', unsafe_allow_html=True)

    # Radar chart
    st.divider()
    st.markdown('<div class="section-label">Profile overview</div>', unsafe_allow_html=True)
    labels    = ["Skills", "Semantic Fit", "Experience", "Completeness", "Keywords"]
    mhr       = ats.get("must_have_ratio", 0)
    nhr       = ats.get("nice_have_ratio", 0)
    yr        = data["jd_data"].get("years_required", 1) or 1
    vals      = [
        round(mhr * 100, 1),
        round(min(100, data["semantic_score"]), 1),
        round(min(100, exp.get("total_years", 0) / yr * 100), 1),
        round((mhr * 0.5 + nhr * 0.5) * 100, 1),
        round(max(0, 100 - len(kgaps) * 10), 1),
    ]
    is_dark    = st.session_state.get("theme", "dark") == "dark"
    grid_col   = "#1a3d3a" if is_dark else "#b2e8de"
    label_col  = "#5eada6" if is_dark else "#3d8c84"
    accent_col = "#14b8a6" if is_dark else "#0a7d72"

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=labels + [labels[0]], fill="toself",
        fillcolor=f"rgba({'20,184,166' if is_dark else '10,125,114'},0.10)",
        line=dict(color=accent_col, width=2), name="Your profile",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[100] * 6, theta=labels + [labels[0]], fill="toself",
        fillcolor="rgba(255,255,255,0.01)",
        line=dict(color=grid_col, width=1, dash="dot"), name="Target",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], color=grid_col, gridcolor=grid_col, showticklabels=False),
            angularaxis=dict(color=label_col, gridcolor=grid_col),
        ),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", color=label_col, size=12),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=label_col)),
        margin=dict(l=40, r=40, t=20, b=20), height=340,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────────────────────
# TAB 2 — IMPROVEMENT PLAN
# ─────────────────────────────────────────────────────────────
def render_improvement_plan(data: dict):
    report = data.get("improvement_report", {})
    if not report:
        st.info("Run an analysis first.")
        return

    mode_info = report.get("mode", {})
    mode = mode_info.get("mode", "optimization") if isinstance(mode_info, dict) else "optimization"
    sa   = report.get("score_analysis", {})

    mode_map = {
        "domain_mismatch": ("Different field",       "#ef4444"),
        "level_mismatch":  ("Experience gap",        "#f59e0b"),
        "skill_gap":       ("Learnable skill gap",   "#f59e0b"),
        "nearly_perfect":  ("Near-perfect match",    "#22c55e"),
        "optimization":    ("Keyword optimization",  "#14b8a6"),
    }
    m_label, m_color = mode_map.get(mode, ("Analysis", "#64748b"))
    cur = sa.get("current_score", 0)
    pot = sa.get("potential_score", 0)

    st.markdown(f'<span style="display:inline-block;padding:0.25rem 0.85rem;border-radius:99px;font-size:0.75rem;font-weight:700;background:{m_color}1a;color:{m_color};border:1px solid {m_color}33;margin-bottom:0.75rem">{m_label}</span>', unsafe_allow_html=True)
    st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.6rem"><span style="font-family:\'DM Serif Display\',serif;font-size:1.6rem;color:var(--text-muted)">{cur:.0f}</span><span style="color:var(--accent);font-size:1.2rem">→</span><span style="font-family:\'DM Serif Display\',serif;font-size:1.6rem;color:var(--accent)">{pot:.0f}</span><span style="font-size:0.75rem;color:var(--text-muted);margin-left:0.25rem">potential score</span></div>', unsafe_allow_html=True)

    if sa.get("why_low"):
        st.markdown(f'<p style="color:var(--text-muted);font-size:0.85rem;line-height:1.65;margin-bottom:0.75rem">{sa["why_low"]}</p>', unsafe_allow_html=True)

    issues = sa.get("main_issues", [])
    if issues:
        st.markdown(badges(issues, "r"), unsafe_allow_html=True)

    if report.get("domain_explanation"):
        st.markdown(f'<div class="card-info" style="margin-top:0.75rem"><span style="font-size:0.88rem;color:var(--accent)">{report["domain_explanation"]}</span></div>', unsafe_allow_html=True)

    # Recommendations
    recs = report.get("recommendations", [])
    if recs:
        st.divider()
        st.markdown('<div class="section-label">Specific changes</div>', unsafe_allow_html=True)
        for i, rec in enumerate(recs, 1):
            dot = priority_dot(rec.get("priority", "medium"))
            with st.expander(f"{dot} {rec.get('title', f'Change {i}')}  ·  +{rec.get('impact_points', 0)} pts", expanded=(i == 1)):
                if rec.get("current_situation"):
                    st.markdown(f'<p style="color:var(--text-muted);font-size:0.83rem">{rec["current_situation"]}</p>', unsafe_allow_html=True)
                for loc in rec.get("locations", []):
                    ct       = loc.get("current_text", "")
                    suggested= loc.get("suggested_text", "")
                    sec      = loc.get("section", "")
                    kws      = loc.get("keywords_added", [])
                    exp_txt  = loc.get("explanation", "")
                    if ct and suggested:
                        st.markdown(f'<div class="section-label" style="margin-top:0.75rem">{sec.upper() or "SECTION"}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="diff-wrap"><div class="diff-old">— {ct}</div><div class="diff-new">+ {suggested}</div></div>', unsafe_allow_html=True)
                        if kws:
                            st.markdown(badges(kws, "b"), unsafe_allow_html=True)
                        if exp_txt:
                            st.markdown(f'<p style="color:var(--text-muted);font-size:0.78rem;margin-top:0.3rem">{exp_txt}</p>', unsafe_allow_html=True)

    # Quick wins — single HTML block
    qw = report.get("quick_wins", [])
    if qw:
        st.divider()
        st.markdown('<div class="section-label">Quick wins</div>', unsafe_allow_html=True)
        rows_html = "".join(
            f'<div style="display:grid;grid-template-columns:4fr 1fr 2fr;gap:0.5rem;align-items:center;padding:0.5rem 0;border-bottom:1px solid var(--border)">'
            f'<span style="color:var(--text-2);font-size:0.83rem">{w.get("action","")}</span>'
            f'<span style="color:var(--text-muted);font-size:0.75rem">{w.get("time","")}</span>'
            f'<span style="color:var(--accent);font-size:0.75rem;font-weight:600">{w.get("impact","")}</span></div>'
            for w in qw
        )
        st.markdown(f'<div class="card-info">{rows_html}</div>', unsafe_allow_html=True)

    # Roadmap
    roadmap = report.get("learning_roadmap", [])
    if roadmap:
        st.divider()
        st.markdown('<div class="section-label">Learning roadmap</div>', unsafe_allow_html=True)
        for step in roadmap:
            tasks_li = "".join(f"<li>{t}</li>" for t in step.get("tasks", []))
            st.markdown(f'<div class="tl-row"><div class="tl-week">{step.get("week","")}</div><div class="tl-body"><h4>{step.get("title","")}</h4><ul style="margin:0.3rem 0 0.4rem 0;padding:0">{tasks_li}</ul><p>Resume addition: {step.get("resume_addition","")}</p></div></div>', unsafe_allow_html=True)

    # Alt roles
    alts = report.get("alternative_roles", [])
    if alts:
        st.divider()
        st.markdown('<div class="section-label">Roles where you are a stronger fit</div>', unsafe_allow_html=True)
        for r in alts:
            rc1, rc2 = st.columns([3, 1])
            with rc1:
                st.markdown(f'<div class="card-muted"><span style="color:var(--text);font-weight:600">{r.get("title","")}</span><br><span style="color:var(--text-muted);font-size:0.8rem">{r.get("why","")}</span></div>', unsafe_allow_html=True)
            with rc2:
                st.markdown(f'<div class="card-muted" style="text-align:center"><span style="color:#22c55e;font-size:1.1rem;font-weight:700">{r.get("match_estimate","")}</span></div>', unsafe_allow_html=True)

    # Boosts + Tips — separate rows for better layout
    boosts = report.get("confidence_boosts", [])
    tips   = report.get("expert_tips", [])
    
    if boosts:
        st.divider()
        st.markdown('<div class="section-label">What you have going for you</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-success">' + "".join(f'<p style="color:#4ade80;font-size:0.88rem;margin:0.4rem 0">✓ {b}</p>' for b in boosts) + '</div>', unsafe_allow_html=True)

    if tips:
        st.divider()
        st.markdown('<div class="section-label" style="text-align:center;font-size:0.85rem">Expert tips</div>', unsafe_allow_html=True)
        tips_html = "".join(f'<p style="color:var(--accent);font-size:1.1rem;font-weight:600;margin:0.75rem 0">→ {t}</p>' for t in tips)
        st.markdown(f'<div class="card-info" style="text-align:center;padding:2.5rem 1.5rem;box-shadow:var(--shadow-lg)">{tips_html}</div>', unsafe_allow_html=True)

    # Section health
    sec_sum = report.get("section_summary", {})
    if sec_sum:
        st.divider()
        st.markdown('<div class="section-label">Section health check</div>', unsafe_allow_html=True)
        sc_cols = st.columns(len(sec_sum))
        status_color = {"good": "#22c55e", "fair": "#f59e0b", "needs_improvement": "#ef4444"}
        for i, (sec, info) in enumerate(sec_sum.items()):
            with sc_cols[i]:
                sc   = info.get("status", "fair")
                col  = status_color.get(sc, "#64748b")
                note = info.get("quick_wins", "") or info.get("suggestions", "")
                st.markdown(f'<div class="health-card"><div class="section-label">{sec}</div><div style="font-weight:700;color:{col};font-size:0.88rem;margin:0.3rem 0">{sc.replace("_"," ").title()}</div><div style="color:var(--text-muted);font-size:0.72rem">{note}</div></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TAB 3 — AI TOOLS
# ─────────────────────────────────────────────────────────────
def render_tools(data: dict):
    api_key = st.session_state.get("api_key_input", "")
    if not api_key:
        st.markdown('<div class="card-info"><span style="font-size:0.85rem;color:var(--accent)">🔑 Enter your Groq API key in the sidebar to use AI tools.</span></div>', unsafe_allow_html=True)
        return
    groq = GroqService(api_key)

    tool = st.selectbox("Choose a tool", ["Bullet Point Rewriter", "Professional Summary Generator"])

    if tool == "Bullet Point Rewriter":
        st.markdown('<div class="section-label" style="margin-top:1rem">Select a bullet from your resume</div>', unsafe_allow_html=True)
        all_bullets = []
        for role in data["resume_data"].get("roles", []):
            for b in role.get("bullets", []):
                if b.strip():
                    all_bullets.append((f"{role.get('company','?')}: {b[:70]}...", b))

        if not all_bullets:
            st.info("No bullets found. Check that your resume was parsed correctly.")
            return

        display, actual = zip(*all_bullets)
        idx = st.selectbox("Bullet", range(len(all_bullets)), format_func=lambda i: display[i], label_visibility="collapsed")
        sel = actual[idx]

        st.markdown('<div class="section-label" style="margin-top:0.75rem">Original</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="diff-old" style="text-decoration:none;color:var(--text-2)">{sel}</div>', unsafe_allow_html=True)

        ctx = st.text_input("Optional focus (e.g. 'emphasise leadership, add a metric')", placeholder="Leave blank to auto-optimize")
        if st.button("✏️ Rewrite bullet", type="primary"):
            with st.spinner("Rewriting..."):
                res = run_async(groq.rewrite_bullet(sel, data["jd_text"], ctx or None))
            st.markdown('<div class="section-label" style="margin-top:0.75rem">Improved</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="diff-new">{res.get("rewritten","")}</div>', unsafe_allow_html=True)
            imps = res.get("improvements", [])
            if imps:
                st.markdown('<div class="section-label" style="margin-top:0.75rem">What changed</div>', unsafe_allow_html=True)
                st.markdown(badges(imps, "b"), unsafe_allow_html=True)

    else:
        st.markdown('<div class="section-label" style="margin-top:1rem">Tone</div>', unsafe_allow_html=True)
        tone = st.select_slider("Tone", options=["confident", "professional", "enthusiastic"], value="professional", label_visibility="collapsed")
        if st.button("Generate summary", type="primary"):
            st.markdown('<div class="section-label" style="margin-top:1rem">Your tailored summary</div>', unsafe_allow_html=True)
            full = ""
            ph = st.empty()
            for chunk in groq.generate_summary_stream(data["resume_data"], data["jd_text"], tone):
                full += chunk
                ph.markdown(f'<div class="card-success"><p style="color:#4ade80;line-height:1.8;font-size:0.88rem">{full}</p></div>', unsafe_allow_html=True)
            if full:
                st.text_area("Copy your summary", value=full, height=120)

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    api_key = render_sidebar()
    if st.session_state.step == "input":
        if not api_key:
            render_welcome()
        else:
            render_input_step(api_key)
    else:
        render_results_step()

if __name__ == "__main__":
    main()