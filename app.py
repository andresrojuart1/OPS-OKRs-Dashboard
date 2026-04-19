"""
Ontop OPS OKRs Dashboard
Entry point: streamlit run app.py
"""

import io
import os

import openai
import openpyxl
import streamlit as st
from dotenv import load_dotenv
from openpyxl.styles import Alignment, Font, PatternFill

load_dotenv(override=True)

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

st.set_page_config(
    page_title="Ontop OKRs — Operations",
    page_icon="🔺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme CSS
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

/* Secondary button — glassmorphism */
.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(10px) !important;
    color: #FFFFFF !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.30) !important;
    filter: none !important;
}

/* Tertiary — pill style */
.stButton > button[kind="tertiary"] {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: none !important;
    border-radius: 20px !important;
    padding: 6px 16px !important;
}

/* Download button — match secondary glassmorphism */
[data-testid="stDownloadButton"] button {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(10px) !important;
    color: #FFFFFF !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.30) !important;
}

/* Destructive actions (Detects the delete material icon) */
div[data-testid="stButton"] button:has(span[data-testid="stIconMaterial"]:contains('delete')),
div[data-testid="stButton"] button:has(span[data-testid="stIconMaterial"]:contains('close')) {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid rgba(239, 68, 68, 0.2) !important;
    color: #ef4444 !important;
}
div[data-testid="stButton"] button:has(span[data-testid="stIconMaterial"]:contains('delete')):hover,
div[data-testid="stButton"] button:has(span[data-testid="stIconMaterial"]:contains('close')):hover {
    background: rgba(239, 68, 68, 0.2) !important;
    border-color: rgba(239, 68, 68, 0.4) !important;
    color: #f87171 !important;
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

/* --- ONTOP BRAND DESIGN SYSTEM --- */
:root {
    --bg-main: #000000;
    --bg-surface: #0B0B0B;
    --bg-card: #111111;
    --accent-purple: #7A50F7; /* Ontop Primary Purple */
    --accent-indigo: #281782; /* Ontop Indigo */
    --accent-teal: #2DD4BF;
    --text-primary: #FFFFFF;
    --text-secondary: #A1A1AA;
    --border-color: rgba(255, 255, 255, 0.08); /* Ultra-subtle border */
}

/* Global Ontop Layout */
.stApp {
    background-color: var(--bg-main);
    font-family: 'Inter', -apple-system, sans-serif;
}

.main-container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 3rem 1rem;
}

/* Typography */
h1, h2, h3 {
    color: var(--text-primary) !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
}

/* PRIMARY ACCENT CARD */
div[data-testid="stVerticalBlock"]:has(> div div.fintech-card-trigger-primary) {
    background: rgba(18, 18, 25, 0.95) !important;
    border: 1px solid rgba(122, 80, 247, 0.3) !important;
    border-radius: 20px !important;
    padding: 2rem !important;
    margin-bottom: 2.5rem !important;
    box-shadow: 0 8px 32px rgba(122, 80, 247, 0.12) !important;
}

div[data-testid="stVerticalBlock"]:has(> div div.fintech-card-trigger-primary) div[data-testid="stVerticalBlock"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* SECONDARY CARDS (Reduced visual weight) */
div[data-testid="stVerticalBlock"]:has(> div div.fintech-card-trigger) {
    background: rgba(11, 11, 16, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 16px !important;
    padding: 1.25rem !important;
    margin-bottom: 1.5rem !important;
    box-shadow: none !important;
    opacity: 0.95;
}

/* Ensure children don't inherit the card style */
div[data-testid="stVerticalBlock"]:has(> div div.fintech-card-trigger) div[data-testid="stVerticalBlock"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.objective-section {
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.kr-row-fintech {
    background: rgba(255, 255, 255, 0.01) !important;
    border: 1px solid rgba(255, 255, 255, 0.03) !important;
    border-radius: 10px !important;
    padding: 1rem !important;
    margin-top: 0.75rem !important;
}

/* --- GHOST CONTROL SYSTEM REMOVED ---
   We now rely on unified st.button types. */

div.stButton > button:hover {
    color: var(--accent-purple) !important;
    background: rgba(122, 80, 247, 0.08) !important;
    transform: scale(1.05); /* Added slight pop for hover feedback */
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
from auth import require_login, get_user, logout
from sheets import (
    seed_if_empty, load_objectives, load_key_results, load_updates,
    compute_progress, create_objective,
    get_week_number, get_weekly_note, save_weekly_note,
    undo_last_import,
    get_weekly_charts, upload_charts_to_drive, delete_chart_from_drive,
    download_drive_file,
)
from components.sidebar import render_sidebar, SUB_TEAMS
from components.objective_card import render_objective_card
from pdf_parser import parse_okr_pdf_with_ai, render_pdf_preview_and_confirm

# ---------------------------------------------------------------------------
for key, default in [
    ("updating_kr",       None),
    ("selected_team",     "All"),
    ("selected_quarter",  "Q2 2026"),
    ("ai_dialog_stale",   True),
]:
    if key not in st.session_state:
        st.session_state[key] = default

QUARTERS = ["Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"]

# ---------------------------------------------------------------------------
# Excel template
# ---------------------------------------------------------------------------

def _generate_template_excel(quarter: str) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = quarter

    headers = [
        "Objective",
        "Key Result",
        "Target",
        "Current Value",
        "Confidence (1–5)",
        "What happened this week?",
        "Blockers / Dependencies",
    ]

    hdr_fill = PatternFill(start_color="1E2140", end_color="1E2140", fill_type="solid")
    hdr_font = Font(color="FFFFFF", bold=True)

    ws.append(headers)
    for cell in ws[1]:
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(wrap_text=False)

    rows = [
        ["Scale Financial Products into Reliable ARR Contributors, Building a Second Revenue Engine Alongside Payroll",
         "Revenue from new initiatives reaches $20K/month", "20000 $", "", "", "", ""],
        ["", "Quick monthly disbursement volume reaches $500K/month", "500000 $/month", "", "", "", ""],
        ["", "Future Fund AUM reaches $8M between CD and MMF vault", "9000000 $", "", "", "", ""],
        ["Close the Margin Gap and Ensure Every Payment Rail Operates at Target Profitability",
         "Pay-ins gross margin reaches 20%", "20 %", "", "", "", ""],
        ["", "Payouts net margin reaches 85% range", "85 %", "", "", "", ""],
        ["", "JPM integration live and processing volume by Q2 close", "1 Launched", "", "", "", ""],
        ["Eliminate Human Intervention as Default in Support, with AI Resolving Most Volume at High CSAT",
         "AI-resolved tickets reach 250 per month", "250 tickets/month", "", "", "", ""],
        ["", "Automated CX resolution rate reaches 55%", "55 %", "", "", "", ""],
        ["", "Aura CSAT score reaches at least 80%", "80 %", "", "", "", ""],
        ["Achieve ISO 27001 Readiness and Pass Pre-Audit to Unlock Enterprise and Regulated Markets",
         "ISO 27001 pre-audit completed with PASS result", "1 PASS (binary)", "", "", "", ""],
        ["Launch Revenue-Generating AI Products That Create a New Direct Monetization Layer",
         "AI Lead Scraper MQL-to-SQL conversion rate reaches 50%", "50 %", "", "", "", ""],
        ["", "AI Money Manager reaches $10K MRR by Dec 2026", "10000 $/month", "", "", "", ""],
        ["Empower the Entire Ontop Organization with the AI Agentic Workflow Framework",
         "Core operational workflows migrated to AI Agentic Workflow framework and live in production",
         "5 workflows", "", "", "", ""],
    ]

    fill_a = PatternFill(start_color="13152A", end_color="13152A", fill_type="solid")
    fill_b = PatternFill(start_color="0D0E1A", end_color="0D0E1A", fill_type="solid")
    body_font = Font(color="FFFFFF")

    for i, row in enumerate(rows):
        ws.append(row)
        fill = fill_a if i % 2 == 0 else fill_b
        for cell in ws[ws.max_row]:
            cell.fill = fill
            cell.font = body_font

    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = max(12, min(max_len + 2, 60))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# AI Update dialog (OpenAI)
# ---------------------------------------------------------------------------

@st.dialog("AI Weekly Update")
def _ai_update_dialog() -> None:
    quarter   = st.session_state.get("selected_quarter", "Q2 2026")
    sub_team  = st.session_state.get("selected_team",    "All")
    krs_info  = st.session_state.get("_krs_for_ai",      [])
    cache_key = f"_ai_text_{quarter}_{sub_team}"

    if st.session_state.get("ai_dialog_stale", True) or cache_key not in st.session_state:
        team_label = sub_team if sub_team != "All" else "Operations (todos los equipos)"

        lines = []
        for kr in krs_info:
            lines.append(
                f"- {kr['title']}: {kr['current_value']}/{kr['target']} {kr['unit']} "
                f"({kr['pct']:.0f}%)"
            )
            if kr.get("last_notes"):
                lines.append(f"  Última semana: {kr['last_notes']}")
            if kr.get("last_blockers"):
                lines.append(f"  Bloqueos: {kr['last_blockers']}")
            if kr.get("last_confidence"):
                lines.append(f"  Confianza: {kr['last_confidence']}/5")
        krs_text = "\n".join(lines) or "No hay KRs disponibles."

        prompt = (
            f"Eres un asistente de operaciones de Ontop. Con base en el estado actual de los OKRs "
            f"del equipo {team_label} para {quarter}, genera un resumen ejecutivo en español de "
            f"máximo 300 palabras que incluya: 1) Estado general del quarter, "
            f"2) Logros destacados, 3) Riesgos y bloqueos críticos, "
            f"4) Recomendaciones concretas para la siguiente semana.\n\n"
            f"Datos actuales de los KRs:\n{krs_text}"
        )

        with st.spinner("Generando resumen con IA..."):
            try:
                client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                )
                st.session_state[cache_key] = response.choices[0].message.content
                st.session_state["ai_dialog_stale"] = False
            except Exception as exc:
                st.error(f"Error al llamar OpenAI API: {exc}")
                return

    text = st.session_state.get(cache_key, "")
    st.markdown(text)
    st.divider()
    st.caption("Copiar texto completo:")
    st.code(text, language=None)


# ---------------------------------------------------------------------------
# Add Objective dialog
# ---------------------------------------------------------------------------

@st.dialog("New Objective")
def add_objective_dialog(sub_team: str, quarter: str) -> None:
    _subteams = [t for t in SUB_TEAMS if t != "All"]

    if sub_team == "All":
        actual_team = st.selectbox("Sub-team", _subteams)
    else:
        actual_team = sub_team

    title = st.text_area(
        "Objective title",
        placeholder="Ex: Scale Financial Products into Reliable ARR Contributors…",
    )
    st.caption(f"Sub-team: **{actual_team}** · Quarter: **{quarter}**")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True, key="add_obj_cancel"):
            st.rerun()
    with c2:
        if st.button("Create Objective", type="primary", use_container_width=True, key="add_obj_create"):
            if title.strip():
                create_objective(title.strip(), actual_team, quarter)
                st.rerun()
            else:
                st.error("El título no puede estar vacío.")


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------

def render_login_page() -> None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:80px 0 48px;">
            <div style="margin-bottom:24px;">
                <span style="font-size:38px;">🔺</span>
                <span style="font-size:38px;font-weight:900;color:#fff;letter-spacing:-1px;"> ontop</span>
            </div>
            <div style="font-size:22px;font-weight:700;color:#fff;margin-bottom:6px;">
                Operations OKRs
            </div>
            <div style="font-size:14px;color:#6B6B7E;margin-bottom:44px;">
                Sign in with your @getontop.com account
            </div>
        </div>
        """, unsafe_allow_html=True)

        if DEV_MODE:
            st.warning("DEV MODE — OAuth bypassed")
            if st.button("Enter as mrojas@getontop.com", use_container_width=True):
                st.session_state["dev_authenticated"] = True
                st.session_state["user"] = {
                    "email": "mrojas@getontop.com", "name": "Andrés Rojas",
                    "given_name": "Andrés", "picture": "",
                }
                st.rerun()
            return

        if st.button("Sign in with Google", use_container_width=True):
            st.login("google")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def render_header(objectives_df, krs_df, selected_team: str) -> None:
    selected_quarter = st.session_state.get("selected_quarter", "Q2 2026")

    col_l, col_r = st.columns([3, 2])
    with col_l:
        sub = f" · {selected_team}" if selected_team != "All" else ""
        st.markdown(f"""
        <div style="margin-bottom:4px;">
            <div style="font-size:24px;font-weight:800;color:#fff;line-height:1.1;">
                Operations OKRs{sub}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.selectbox(
            "Quarter",
            QUARTERS,
            index=QUARTERS.index(selected_quarter) if selected_quarter in QUARTERS else 1,
            key="selected_quarter",
            label_visibility="collapsed",
        )

    with col_r:
        st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
        if selected_team == "All":
            c1, c2 = st.columns(2)
            with c1:
                excel_bytes = _generate_template_excel(selected_quarter)
                st.download_button(
                    label="Template",
                    icon=":material/download:",
                    data=excel_bytes,
                    file_name=f"Operations-OKR-Template-{selected_quarter}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="hdr_tmpl",
                    use_container_width=True,
                )
            with c2:
                if st.button("AI Update", icon=":material/smart_toy:", key="hdr_ai", use_container_width=True, type="secondary"):
                    st.session_state["ai_dialog_stale"] = True
                    _ai_update_dialog()
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                excel_bytes = _generate_template_excel(selected_quarter)
                st.download_button(
                    label="Template",
                    icon=":material/download:",
                    data=excel_bytes,
                    file_name=f"Operations-OKR-Template-{selected_quarter}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="hdr_tmpl",
                    use_container_width=True,
                )
            with c2:
                if st.button("AI Update", icon=":material/smart_toy:", key="hdr_ai", use_container_width=True, type="secondary"):
                    st.session_state["ai_dialog_stale"] = True
                    _ai_update_dialog()
            with c3:
                if st.button("Import from PDF", icon=":material/description:", use_container_width=True, key="pdf_import_btn_hdr", type="secondary"):
                    st.session_state["show_pdf_import"] = True

    # Metrics — filter by quarter + selected team
    filtered_objs = objectives_df
    if not objectives_df.empty and "quarter" in objectives_df.columns:
        filtered_objs = filtered_objs[filtered_objs["quarter"] == selected_quarter]
    if selected_team != "All" and not filtered_objs.empty and "sub_team" in filtered_objs.columns:
        filtered_objs = filtered_objs[filtered_objs["sub_team"] == selected_team]

    if not filtered_objs.empty and not krs_df.empty:
        obj_ids   = set(filtered_objs["id"].astype(str).tolist())
        team_krs  = krs_df[krs_df["objective_id"].astype(str).isin(obj_ids)]
    else:
        team_krs = krs_df.iloc[:0]

    num_objs = len(filtered_objs) if not filtered_objs.empty else 0
    total_krs = len(team_krs) if not team_krs.empty else 0

    if not team_krs.empty:
        all_pct = team_krs.apply(compute_progress, axis=1)
        at_risk_count = int((all_pct < 70).sum())
        on_track_count = int((all_pct >= 70).sum())
        avg_prog = all_pct.mean()
    else:
        at_risk_count = 0
        on_track_count = 0
        avg_prog = 0.0
        
    # Calculate status
    at_risk_ratio = at_risk_count / total_krs if total_krs > 0 else 0
    if total_krs == 0:
        status_color = "#6B6B7E"
        status_text = "No KRs Tracked"
        status_icon = "➖"
    elif at_risk_ratio > 0.5:
        status_color = "#ef4444"
        status_text = "Execution at Risk"
        status_icon = "⚠️"
    elif at_risk_ratio > 0:
        status_color = "#f59e0b"
        status_text = "Execution Needs Attention"
        status_icon = "🔔"
    else:
        status_color = "#10b981"
        status_text = "Execution Healthy"
        status_icon = "✨"
            
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin: 0 0 20px 0; background:rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 6px 16px; border-radius: 99px; width: fit-content;">
            <span style="font-size: 1rem;">{status_icon}</span>
            <span style="color: {status_color}; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.03em; text-transform: uppercase;">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # KPI Cards
        st.markdown(f"""
        <div style="display:flex; gap:16px; margin-bottom:10px; flex-wrap:wrap;">
            <div style="flex:1; min-width: 120px; background:rgba(6,6,9,0.82); border:1px solid #2A2A3E; border-radius:16px; padding:20px;">
                <div style="color:#A1A1AA; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Objectives</div>
                <div style="color:#FFFFFF; font-size:2.4rem; font-weight:800; line-height:1.2; margin-top:8px;">{num_objs}</div>
                <div style="color:#6B6B7E; font-size:0.7rem; font-weight:600; margin-top:8px;">Total Active</div>
            </div>
            <div style="flex:1; min-width: 120px; background:rgba(6,6,9,0.82); border:1px solid #2A2A3E; border-radius:16px; padding:20px;">
                <div style="color:#A1A1AA; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Key Results</div>
                <div style="color:#FFFFFF; font-size:2.4rem; font-weight:800; line-height:1.2; margin-top:8px;">{total_krs}</div>
                <div style="color:#6B6B7E; font-size:0.7rem; font-weight:600; margin-top:8px;">Tracked Items</div>
            </div>
            <div style="flex:1; min-width: 120px; background:rgba(6,6,9,0.82); border:1px solid #2A2A3E; border-radius:16px; padding:20px;">
                <div style="color:#A1A1AA; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Avg Progress</div>
                <div style="color:#FFFFFF; font-size:2.4rem; font-weight:800; line-height:1.2; margin-top:8px;">{avg_prog:.0f}%</div>
                <div style="color:#6B6B7E; font-size:0.7rem; font-weight:600; margin-top:8px;">Execution Progress</div>
            </div>
            <div style="flex:1; min-width: 120px; background:rgba(6,6,9,0.82); border:1px solid #2A2A3E; border-radius:16px; padding:20px; border-bottom:4px solid #10b981;">
                <div style="color:#A1A1AA; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">On Track</div>
                <div style="color:#10b981; font-size:2.4rem; font-weight:800; line-height:1.2; margin-top:8px;">{on_track_count}</div>
                <div style="color:#6B6B7E; font-size:0.7rem; font-weight:600; margin-top:8px;">KRs On Track</div>
            </div>
            <div style="flex:1; min-width: 120px; background:rgba(6,6,9,0.82); border:1px solid #2A2A3E; border-radius:16px; padding:20px; border-bottom:4px solid #ef4444;">
                <div style="color:#A1A1AA; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">At Risk</div>
                <div style="color:#ef4444; font-size:2.4rem; font-weight:800; line-height:1.2; margin-top:8px;">{at_risk_count}</div>
                <div style="color:#6B6B7E; font-size:0.7rem; font-weight:600; margin-top:8px;">KRs At Risk</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:14px 0 22px;'>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def render_dashboard() -> None:
    if not DEV_MODE and "user" not in st.session_state:
        st.session_state["user"] = get_user()

    try:
        seed_if_empty()
    except Exception as exc:
        import traceback
        st.error(f"[{type(exc).__name__}] {exc}")
        st.code(traceback.format_exc())
        st.stop()

    objectives_df = load_objectives()
    krs_df        = load_key_results()
    updates_df    = load_updates()
    selected_team = render_sidebar()
    team_label    = selected_team or "All"

    # Pre-compute KRs info for the AI Update dialog
    selected_quarter = st.session_state.get("selected_quarter", "Q2 2026")
    ai_objs = objectives_df
    if not objectives_df.empty:
        if "quarter" in objectives_df.columns:
            ai_objs = ai_objs[ai_objs["quarter"] == selected_quarter]
        if team_label != "All" and "sub_team" in ai_objs.columns:
            ai_objs = ai_objs[ai_objs["sub_team"] == team_label]

    if not ai_objs.empty and not krs_df.empty:
        ai_obj_ids = set(ai_objs["id"].astype(str).tolist())
        ai_krs     = krs_df[krs_df["objective_id"].astype(str).isin(ai_obj_ids)]
    else:
        ai_krs = krs_df.iloc[:0]

    krs_info = []
    for _, kr in ai_krs.iterrows():
        kr_upds = updates_df[updates_df["kr_id"] == str(kr["id"])].sort_values(
            "updated_at", ascending=False
        ) if not updates_df.empty else updates_df
        latest = kr_upds.iloc[0] if not kr_upds.empty else None
        krs_info.append({
            "id":             str(kr["id"]),
            "title":          str(kr["title"]),
            "target":         float(kr["target"]),
            "unit":           str(kr["unit"]),
            "current_value":  float(kr.get("current_value", 0)),
            "pct":            compute_progress(kr),
            "last_notes":     str(latest["week_notes"]) if latest is not None and latest.get("week_notes") else "",
            "last_blockers":  str(latest["blockers"])   if latest is not None and latest.get("blockers")   else "",
            "last_confidence": int(latest["confidence"]) if latest is not None and latest.get("confidence") else 0,
        })
    st.session_state["_krs_for_ai"] = krs_info

    render_header(objectives_df, krs_df, team_label)

    # PDF import section (sub-team views only)
    if team_label != "All":
        if st.session_state.get("show_pdf_import"):
            with st.container():
                col_title, col_exit = st.columns([3, 1])
                with col_title:
                    st.markdown("### 📄 Import OKR Update from PDF")
                with col_exit:
                    if st.button("Back to Dashboard", icon=":material/arrow_back:", use_container_width=True):
                        st.session_state["show_pdf_import"] = False
                        st.session_state.pop("parsed_pdf_data", None)
                        st.rerun()
                st.caption(
                    "Upload your OKR PDF report. The system will extract the data "
                    "and show you a preview before saving anything."
                )
                pdf_file = st.file_uploader(
                    "Upload PDF", type=["pdf"], key=f"pdf_uploader_{team_label}"
                )
                if pdf_file:
                    if st.button("Parse PDF", icon=":material/search:", type="primary", key=f"parse_pdf_btn_{team_label}"):
                        with st.spinner("Leyendo y analizando PDF con IA (esto puede tardar un momento)..."):
                            try:
                                parsed_data = parse_okr_pdf_with_ai(
                                    pdf_file, team_label, selected_quarter,
                                    st.secrets["OPENAI_API_KEY"],
                                )
                                st.session_state["parsed_pdf_data"] = parsed_data
                                st.toast("PDF analizado con éxito", icon="🔍")
                            except Exception as exc:
                                st.error(f"Error parsing PDF: {exc}")
                
                if st.session_state.get("parsed_pdf_data"):
                    render_pdf_preview_and_confirm(
                        st.session_state["parsed_pdf_data"], team_label, selected_quarter,
                    )

        # Undo button visible on main dashboard after import
        if "last_import_summary" in st.session_state:
            import time
            import_summary = st.session_state["last_import_summary"]
            import_time = import_summary.get("timestamp", 0)
            
            # Only show the button if it's less than 15 seconds old
            if time.time() - import_time < 60:
                st.warning("⏪ Recent import detected. You can revert it if needed.")
                c1, c2 = st.columns([1, 4])
                with c1:
                    if st.button("Undo", icon=":material/undo:", use_container_width=True, help="Revert the last PDF import changes"):
                        undo_last_import(import_summary)
                        st.session_state.pop("last_import_summary", None)
                        st.rerun()
                with c2:
                    if st.button("Dismiss", icon=":material/check:", use_container_width=True, help="Keep changes and hide this message"):
                        st.session_state.pop("last_import_summary", None)
                        st.rerun()
            else:
                st.session_state.pop("last_import_summary", None)

    # Filter display objectives by quarter + team
    display_objs = objectives_df
    if not objectives_df.empty and "quarter" in objectives_df.columns:
        display_objs = display_objs[display_objs["quarter"] == selected_quarter]
    if selected_team and not display_objs.empty and "sub_team" in display_objs.columns:
        display_objs = display_objs[display_objs["sub_team"] == selected_team]

    if display_objs.empty:
        st.info(
            f"No hay OKRs para **{selected_quarter}** · **{team_label}**. "
            f"Crea el primero con el botón de abajo."
        )
    else:
        active_kr = st.session_state.get("updating_kr") or ""
        for i, (_, obj_row) in enumerate(display_objs.iterrows()):
            render_objective_card(obj_row, krs_df, active_kr=active_kr, is_primary=(i == 0))

    if st.button("Add Objective", icon=":material/add:", key=f"add_obj_{team_label}", type="secondary"):
        add_objective_dialog(team_label, selected_quarter)

    # Weekly Notes + Charts section (sub-team views only)
    if team_label != "All":
        st.divider()
        st.subheader("📝 Additional Weekly Notes")
        st.caption("Document important updates, decisions or context not tied to specific KRs")

        week_number   = get_week_number()
        existing_note = get_weekly_note(team_label, selected_quarter, week_number)
        note_content  = existing_note.get("content", "")

        # Display Mode (Card)
        if note_content:
            st.markdown(f"""
            <div style="background-color: rgba(255,255,255,0.05); padding: 1.2rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 1rem; color: #e0e0e0; font-size: 0.95rem;">
                {note_content.replace('\n', '<br>')}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No narrative notes for this week yet.")

        # Edit Section
        with st.expander("✏️ Edit Weekly Note"):
            note_text = st.text_area(
                "Note Content",
                value=note_content,
                height=200,
                key=f"editor_{team_label}_{week_number}",
                label_visibility="collapsed"
            )
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("Save Changes", use_container_width=True, type="primary", key=f"btn_save_{team_label}_{week_number}"):
                    email = st.session_state.get("user", {}).get("email", "unknown")
                    with st.spinner("Saving..."):
                        save_weekly_note(team_label, selected_quarter, week_number, note_text, email)
                        st.cache_data.clear()
                        st.success("Changes saved!")
                        import time
                        time.sleep(1)
                        st.rerun()

        st.markdown("#### 📊 Charts & Screenshots")
        st.caption(
            "Upload dashboard screenshots for this week's session. "
            "Previous weeks' charts are archived but not shown here."
        )
        uploaded_files = st.file_uploader(
            "Upload charts",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key=f"chart_uploader_{team_label}_{week_number}",
        )
        if uploaded_files:
            if st.button("Upload to Drive", type="primary", key=f"upload_charts_{team_label}_{week_number}"):
                with st.spinner("Subiendo imágenes a Google Drive..."):
                    email = st.session_state.get("user", {}).get("email", "unknown")
                    upload_charts_to_drive(uploaded_files, team_label, selected_quarter, week_number, email)
                    st.toast("✅ Imágenes subidas correctamente", icon="📊")
                st.rerun()

        current_charts = get_weekly_charts(team_label, selected_quarter, week_number)
        if current_charts:
            st.markdown("**This week's charts:**")
            chart_cols = st.columns(min(len(current_charts), 2))
            for i, chart in enumerate(current_charts):
                with chart_cols[i % 2]:
                    try:
                        img_bytes = download_drive_file(chart["drive_file_id"])
                        st.image(img_bytes, caption=chart["filename"], use_container_width=True)
                    except Exception as e:
                        st.error(f"Error cargando imagen: {e}")
                    
                    if st.button("Remove", icon=":material/delete:", key=f"del_chart_{chart['id']}", type="secondary"):
                        with st.spinner("Eliminando imagen..."):
                            delete_chart_from_drive(str(chart["id"]))
                            st.toast("Imagen eliminada", icon="🗑️")
                        st.rerun()


# ---------------------------------------------------------------------------
if DEV_MODE:
    if st.session_state.get("dev_authenticated"):
        render_dashboard()
    else:
        render_login_page()
else:
    if require_login():
        render_dashboard()
    else:
        render_login_page()
