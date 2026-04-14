"""
Ontop OPS OKRs Dashboard — Q2 2026
Entry point: streamlit run app.py
"""

import os
import secrets

import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

st.set_page_config(
    page_title="Ontop OKRs — Q2 2026",
    page_icon="🔺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Ontop global theme (ported from shared.py)
# ---------------------------------------------------------------------------

st.markdown("""
<style>
:root {
    --ontop-purple: #261C94;
    --ontop-coral:  #E35276;
    --bg-primary:   #000000;
    --bg-card:      #060609;
    --bg-input:     #1A1A24;
    --text-primary: #FFFFFF;
    --text-secondary: #B8B8C8;
    --text-muted:   #6B6B7E;
    --border-color: #2A2A3E;
}

.stApp {
    background:
        radial-gradient(circle at top left,  rgba(38,28,148,0.35), transparent 32%),
        radial-gradient(circle at top right, rgba(227,82,118,0.20), transparent 28%),
        linear-gradient(180deg, #050507 0%, #000000 100%);
    color: var(--text-primary);
}

[data-testid="stHeader"] { background: rgba(0,0,0,0); }

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(38,28,148,0.18), rgba(6,6,9,0.94) 26%),
        #060609;
    border-right: 1px solid var(--border-color);
}

[data-testid="stSidebar"] * { color: var(--text-primary); }
[data-testid="stSidebarNav"]          { display: none; }
[data-testid="stSidebarNavSeparator"] { display: none; }

.block-container {
    padding-top: 1.75rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}

h1,h2,h3 { color: var(--text-primary); letter-spacing: -0.02em; }
p, li, label, .stMarkdown, .stCaption { color: var(--text-secondary); }

/* Inputs */
.stTextInput input,
.stTextArea textarea,
.stSelectbox [data-baseweb="select"] > div,
.stNumberInput input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    border-radius: 14px !important;
}

/* Primary button: purple→coral gradient, pill */
.stButton > button {
    background: linear-gradient(135deg, var(--ontop-purple), var(--ontop-coral));
    color: var(--text-primary);
    border: 0;
    border-radius: 999px;
    font-weight: 600;
    box-shadow: 0 10px 24px rgba(38,28,148,0.28);
}
.stButton > button:hover { filter: brightness(1.07); }

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(124,115,247,0.28) !important;
    box-shadow: none !important;
}

/* Tertiary */
.stButton > button[kind="tertiary"] {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: rgba(6,6,9,0.82);
    border: 1px solid var(--border-color);
    border-radius: 18px;
    padding: 1rem;
}
[data-testid="stMetricValue"] { color: #E35276 !important; }
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; }

/* Alerts */
.stAlert { border-radius: 16px; border: 1px solid var(--border-color); }

/* Slider */
[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {
    background: var(--ontop-coral) !important;
}

hr { border-color: var(--border-color) !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #000; }
::-webkit-scrollbar-thumb { background: #2A2A3E; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--ontop-coral); }

/* Sidebar brand */
.ontop-sidebar-brand { padding: 0.1rem 0 0.75rem; }
.ontop-sidebar-brand h1 { margin: 0.15rem 0 0; font-size: 1.45rem; line-height: 1; }
.ontop-sidebar-brand p  { margin: 0.3rem 0 0; color: var(--text-muted); font-size: 0.8rem; }

.ontop-sidebar-badge {
    display: inline-flex; align-items: center; gap: .35rem;
    padding: .28rem .55rem; border-radius: 999px;
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
    color: #FFFFFF; font-size: .72rem; font-weight: 700;
    letter-spacing: .08em; text-transform: uppercase;
}

.ontop-sidebar-section-label {
    margin: .9rem 0 .4rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: .08em;
    font-size: .72rem; font-weight: 700;
}

.ontop-sidebar-user {
    padding: .85rem; border-radius: 18px;
    border: 1px solid var(--border-color);
    background:
        radial-gradient(circle at top right, rgba(227,82,118,0.14), transparent 36%),
        linear-gradient(180deg, rgba(26,26,36,.96), rgba(6,6,9,.96));
    margin-top: .75rem; margin-bottom: .5rem;
    display: grid; grid-template-columns: 2.5rem 1fr; gap: .75rem; align-items: center;
}
.ontop-sidebar-avatar {
    width:2.5rem; height:2.5rem; border-radius:999px;
    display:flex; align-items:center; justify-content:center;
    background: linear-gradient(135deg,rgba(38,28,148,.95),rgba(227,82,118,.8));
    color:#fff; font-size:.9rem; font-weight:800;
}
.ontop-sidebar-user strong { display:block; color:#fff; font-size:.95rem; margin-bottom:.15rem; }
.ontop-sidebar-user span   { color:var(--text-secondary); font-size:.82rem; word-break:break-word; }
.ontop-sidebar-user-label  {
    display:block; color:var(--text-muted); font-size:.7rem;
    text-transform:uppercase; letter-spacing:.08em; margin-bottom:.18rem;
}

/* Nav link buttons in sidebar */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid transparent !important;
    border-radius: 16px !important;
    color: var(--text-secondary) !important;
    font-size: .95rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: .55rem .82rem !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
    width: 100% !important;
    min-height: 2.4rem !important;
    transition: all .12s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: rgba(124,115,247,0.35) !important;
    background: rgba(255,255,255,0.05) !important;
    color: #fff !important;
    filter: none !important;
}

/* Objective / KR cards */
.okr-card {
    padding: 1.1rem 1.25rem .9rem;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background:
        radial-gradient(circle at top right, rgba(227,82,118,0.10), transparent 35%),
        linear-gradient(180deg, rgba(26,26,36,.92), rgba(6,6,9,.92));
    margin-bottom: .75rem;
}
.okr-card-purple {
    background:
        radial-gradient(circle at top right, rgba(124,115,247,0.18), transparent 35%),
        linear-gradient(180deg, rgba(27,24,57,.96), rgba(10,10,22,.96));
    border-color: rgba(124,115,247,0.22);
}

.ontop-status-badge {
    display:inline-flex; align-items:center; gap:.35rem;
    padding:.22rem .65rem; border-radius:999px;
    font-size:.76rem; font-weight:700; letter-spacing:.03em; white-space:nowrap;
}
.status-coral {
    background:rgba(227,82,118,.12); color:#ff9ab0;
    border:1px solid rgba(227,82,118,.32);
}
.status-green {
    background:rgba(34,197,94,.12); color:#7ee2a8;
    border:1px solid rgba(34,197,94,.30);
}
.status-amber {
    background:rgba(245,158,11,.12); color:#f8c56a;
    border:1px solid rgba(245,158,11,.28);
}

.progress-track {
    background: rgba(42,42,62,0.8);
    border-radius: 999px;
    height: 5px;
    overflow: hidden;
    margin: 6px 0 2px;
}
.progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--ontop-purple), var(--ontop-coral));
}

.kr-row {
    padding: .85rem 1.1rem .5rem;
    border-radius: 14px;
    border: 1px solid var(--border-color);
    background: rgba(6,6,9,0.85);
    margin: .45rem 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
from auth import handle_oauth_callback, build_authorization_url
from sheets import seed_if_empty, load_objectives, load_key_results, compute_progress
from components.sidebar import render_sidebar
from components.objective_card import render_objective_card

# ---------------------------------------------------------------------------
for key, default in [
    ("authenticated", False),
    ("oauth_state",   secrets.token_urlsafe(16)),
    ("updating_kr",   None),
    ("auth_error",    None),
    ("selected_team", "All"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if not DEV_MODE:
    handle_oauth_callback()

# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def render_login_page() -> None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:80px 0 48px;">
            <div style="margin-bottom:24px;">
                <span style="font-size:38px;">🔺</span>
                <span style="font-size:38px;font-weight:900;color:#fff;letter-spacing:-1px;"> ontop</span>
                <span style="font-size:11px;font-weight:700;
                             background:linear-gradient(135deg,#261C94,#E35276);
                             padding:3px 9px;border-radius:999px;color:#fff;margin-left:6px;">AI</span>
            </div>
            <div style="font-size:22px;font-weight:700;color:#fff;margin-bottom:6px;">
                Q2 2026 — Operations OKRs
            </div>
            <div style="font-size:14px;color:#6B6B7E;margin-bottom:44px;">
                Sign in with your @getontop.com account
            </div>
        </div>
        """, unsafe_allow_html=True)

        if DEV_MODE:
            st.warning("DEV MODE — OAuth bypassed")
            if st.button("Enter as mrojas@getontop.com", use_container_width=True):
                st.session_state.update({
                    "authenticated": True,
                    "user": {"email":"mrojas@getontop.com","name":"Andrés Rojas",
                             "given_name":"Andrés","picture":""},
                })
                st.rerun()
            return

        auth_url = build_authorization_url(st.session_state["oauth_state"])
        st.markdown(f"""
        <div style="text-align:center;">
            <a href="{auth_url}" target="_self" style="text-decoration:none;">
                <div style="display:inline-flex;align-items:center;gap:12px;
                            background:linear-gradient(135deg,#261C94,#E35276);
                            color:#fff;font-weight:700;font-size:15px;
                            padding:14px 36px;border-radius:999px;
                            box-shadow:0 10px 28px rgba(38,28,148,0.32);cursor:pointer;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get("auth_error"):
            st.error(st.session_state["auth_error"])


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def render_header(krs_df, selected_team: str) -> None:
    col_l, col_r = st.columns([3, 2])
    with col_l:
        sub = f" · {selected_team}" if selected_team != "All" else ""
        st.markdown(f"""
        <div style="margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:17px;">🔺</span>
                <span style="font-size:17px;font-weight:900;color:#fff;letter-spacing:-.5px;">ontop</span>
                <span style="font-size:9px;font-weight:700;
                             background:linear-gradient(135deg,#261C94,#E35276);
                             padding:2px 7px;border-radius:999px;color:#fff;">AI</span>
                <span style="font-size:11px;color:#6B6B7E;margin-left:2px;">
                    Global Workforce, powered by AI
                </span>
            </div>
            <div style="font-size:24px;font-weight:800;color:#fff;line-height:1.1;">
                Operations OKRs{sub}
            </div>
            <div style="font-size:12px;color:#6B6B7E;margin-top:3px;">Q2 2026</div>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("⬇ Template",       key="hdr_tmpl",   use_container_width=True, type="secondary")
        with c2:
            st.button("✨ Generate OKRs", key="hdr_gen",    use_container_width=True)
        with c3:
            st.button("🤖 AI Update",     key="hdr_ai",     use_container_width=True, type="secondary")

    if not krs_df.empty:
        all_pct = krs_df.apply(compute_progress, axis=1)
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Objectives",   len(krs_df["objective_id"].unique()))
        c2.metric("Key Results",  len(krs_df))
        c3.metric("Avg Progress", f"{all_pct.mean():.0f}%")
        c4.metric("On Track ✅",  int((all_pct >= 70).sum()))
        c5.metric("At Risk",      int((all_pct < 70).sum()))

    st.markdown("<hr style='margin:14px 0 22px;'>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def render_dashboard() -> None:
    try:
        seed_if_empty()
    except Exception as exc:
        import traceback
        st.error(f"[{type(exc).__name__}] {exc}")
        st.code(traceback.format_exc())
        st.stop()

    objectives_df = load_objectives()
    krs_df        = load_key_results()
    selected_team = render_sidebar()

    render_header(krs_df, selected_team or "All")

    display_objs = objectives_df
    if selected_team and not objectives_df.empty and "sub_team" in objectives_df.columns:
        display_objs = objectives_df[objectives_df["sub_team"] == selected_team]

    if display_objs.empty:
        st.info(f"No objectives for **{selected_team}** yet.")
        return

    active_kr = st.session_state.get("updating_kr") or ""
    for _, obj_row in display_objs.iterrows():
        render_objective_card(obj_row, krs_df, active_kr=active_kr)


# ---------------------------------------------------------------------------
if st.session_state.get("authenticated"):
    render_dashboard()
else:
    render_login_page()
