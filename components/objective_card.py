"""Objective card — Fintech Edition (Stripe/Ramp Style)."""

import streamlit as st
from sheets import (
    compute_progress,
    create_kr,
    delete_kr_by_id,
    delete_update_by_id,
    format_value,
    load_updates_for_kr,
    update_kr_fields,
    update_kr_value,
    update_objective,
    delete_objective,
)

# Design System Tokens (Defined in app.py)
PURPLE  = "#7c73f7"
TEAL    = "#2DD4BF"
MUTED   = "#94A3B8"
BG_CARD = "#1A2330"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct_indicator(pct: float) -> str:
    color = "var(--accent-teal)" if pct >= 70 else ("#f8c56a" if pct >= 40 else "var(--accent-coral)")
    icon  = "↑" if pct >= 50 else "↓"
    return f"""
    <div style="display:flex; align-items:center; gap:6px;">
        <span style="font-size:2rem; font-weight:800; color:{color}; letter-spacing:-0.04em;">{pct:.0f}%</span>
        <div style="font-size:0.75rem; font-weight:600; color:{color}; background:rgba(255,255,255,0.05); 
                    padding:2px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.1);">
            {icon} TREND
        </div>
    </div>
    """

def _fintech_progress_bar(pct: float) -> str:
    return f"""
    <div class="progress-container-fintech">
        <div class="progress-bar-fintech" style="width:{pct:.1f}%;"></div>
    </div>"""

# ---------------------------------------------------------------------------
# Objective Card
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, active_kr: str) -> None:
    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")

    obj_krs = krs_df[krs_df["objective_id"] == obj_id] if not krs_df.empty else krs_df
    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    # Main Card Start
    st.markdown(f"""
    <div class="objective-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.5rem;">
            <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <span style="font-size:0.75rem; font-weight:700; color:var(--accent-purple); 
                                 background:rgba(124,115,247,0.1); padding:4px 10px; border-radius:6px; 
                                 text-transform:uppercase; letter-spacing:0.04em;">Performance Index</span>
                    <span style="font-size:0.75rem; color:var(--text-secondary); font-weight:600;">{sub_team}</span>
                </div>
                {_pct_indicator(avg_pct)}
                <div style="font-size:1.25rem; font-weight:700; color:white; margin-top:1rem; line-height:1.4;">
                    {obj_title}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Mini Actions for Objective
    c1, c2, c3, _ = st.columns([0.5, 0.5, 1.2, 8])
    with c1:
        if st.button("✏️", key=f"eobj_{obj_id}", help="Edit Objective"): _edit_obj_dialog(obj_id, obj_title)
    with c2:
        if st.button("🗑️", key=f"dobj_{obj_id}", help="Delete Objective"): _confirm_delete_obj_dialog(obj_id, obj_title)
    with c3:
        if st.button("+ Key Result", key=f"bak_{obj_id}"): add_kr_dialog(obj_id, obj_title)

    st.markdown('<div style="margin-top:2rem;"></div>', unsafe_allow_html=True)

    if not obj_krs.empty:
        for _, kr in obj_krs.iterrows():
            _render_kr_row(kr, active_kr)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# KR Row
# ---------------------------------------------------------------------------

def _render_kr_row(kr, active_kr: str) -> None:
    kr_id   = str(kr["id"])
    title   = kr["title"]
    pct     = compute_progress(kr)
    current = float(kr.get("current_value", 0))
    target  = float(kr.get("target", 0))
    unit    = str(kr.get("unit", ""))
    val_str = format_value(current, target, unit)

    st.markdown(f"""
    <div class="kr-row-fintech">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="flex:1; padding-right:2rem;">
                <div style="font-size:0.9375rem; font-weight:600; color:white; margin-bottom:4px; line-height:1.5;">{title}</div>
                <div style="font-size:0.8125rem; color:var(--text-secondary);">{val_str}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.125rem; font-weight:700; color:var(--accent-teal);">{pct:.0f}%</div>
                <div style="font-size:0.6875rem; color:var(--text-secondary); text-transform:uppercase; font-weight:600; letter-spacing:0.05em;">Completion</div>
            </div>
        </div>
        {_fintech_progress_bar(pct)}
    </div>
    """, unsafe_allow_html=True)

    # Actions Row
    c_upd, c_hist, c_edit, c_del, _ = st.columns([1.8, 1.2, 0.4, 0.4, 6])
    
    with c_upd:
        is_upd = active_kr == kr_id
        st.button("Update Status" if not is_upd else "Close Panel", key=f"uk_{kr_id}", 
                  type="secondary" if not is_upd else "primary", use_container_width=True,
                  on_click=lambda y=kr_id: st.session_state.update({"updating_kr": None if active_kr == y else y}))
    
    with c_hist:
        hist_key = f"h_{kr_id}"
        st.button("Activity", key=f"sh_{kr_id}", 
                  on_click=lambda k=hist_key: st.session_state.update({k: not st.session_state.get(k, False)}))

    with c_edit:
        if st.button("✏️", key=f"ek_{kr_id}"): _edit_kr_dialog(kr_id, title, target, unit)
    
    with c_del:
        if st.button("🗑️", key=f"dk_{kr_id}"): _confirm_delete_kr_dialog(kr_id, title)

    if active_kr == kr_id: _render_update_form(kr)
    if st.session_state.get(f"h_{kr_id}"): _render_history(kr_id)

# ---------------------------------------------------------------------------
# Dialogs & Updates (Reused from previous version but styled via app.py)
# ---------------------------------------------------------------------------

@st.dialog("Editar Objetivo")
def _edit_obj_dialog(obj_id: str, current_title: str) -> None:
    new_title = st.text_area("Título", value=current_title, height=100)
    if st.button("Update Objective", type="primary", use_container_width=True):
        update_objective(obj_id, new_title.strip())
        st.rerun()

@st.dialog("Confirmar eliminación")
def _confirm_delete_obj_dialog(obj_id: str, obj_title: str) -> None:
    st.warning(f"This will permanently delete this objective and all associated data.")
    st.caption(obj_title)
    if st.button("Delete Everything", type="primary", use_container_width=True):
        delete_objective(obj_id)
        st.rerun()

@st.dialog("Edit Key Result")
def _edit_kr_dialog(kr_id: str, current_title: str, current_target: float, current_unit: str) -> None:
    new_title  = st.text_input("Title", value=current_title)
    c1, c2 = st.columns(2)
    with c1: nt = st.number_input("Target", value=float(current_target))
    with c2: nu = st.text_input("Unit", value=current_unit)
    if st.button("Save Changes", type="primary", use_container_width=True):
        update_kr_fields(kr_id, new_title, nt, nu)
        st.rerun()

@st.dialog("Delete Key Result")
def _confirm_delete_kr_dialog(kr_id: str, kr_title: str) -> None:
    if st.button("Delete KR", type="primary", use_container_width=True):
        delete_kr_by_id(kr_id)
        st.rerun()

@st.dialog("New Key Result")
def add_kr_dialog(objective_id: str, objective_title: str) -> None:
    title = st.text_input("Key Result Name")
    c1, c2 = st.columns(2)
    with c1: target = st.number_input("Target Value", value=100.0)
    with c2: unit = st.text_input("Unit (e.g. $, %, users)", value="%")
    if st.button("Deploy KR", type="primary", use_container_width=True):
        create_kr(objective_id, title, target, unit)
        st.rerun()

def _render_update_form(kr) -> None:
    kr_id = str(kr["id"])
    st.markdown("""<div style="background:var(--bg-card); padding:1.5rem; border-radius:12px; border:1px solid var(--border-color); margin:1rem 0;">""", unsafe_allow_html=True)
    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1: new_val = st.number_input("New Data Point", value=float(kr.get("current_value",0)))
        with c2: conf = st.slider("Confidence Score", 1, 5, 3)
        notes = st.text_area("Narrative / Weekly Insights", placeholder="Explain the progress or blockers...")
        if st.form_submit_button("Register Update", use_container_width=True):
            from sheets import update_kr_value
            email = st.session_state.get("user",{}).get("email","unknown")
            update_kr_value(kr_id=kr_id, new_value=float(new_val), week_notes=notes, confidence=int(conf), updated_by=email)
            st.session_state["updating_kr"] = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def _render_history(kr_id: str) -> None:
    from sheets import load_updates_for_kr, delete_update_by_id
    upds = load_updates_for_kr(kr_id)
    if upds.empty: 
        st.caption("No historical records found.")
        return
    for _, row in upds.iterrows():
        st.markdown(f"""
        <div style="padding:1rem 0; border-bottom:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:0.9rem; font-weight:700; color:white;">{row["new_value"]}</div>
                <div style="font-size:0.75rem; color:var(--text-secondary);">{row["week_notes"]}</div>
            </div>
            <div style="font-size:0.75rem; color:var(--text-secondary);">{row.get("updated_at","")}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️", key=f"dur_{row['id']}"): 
            delete_update_by_id(str(row["id"]))
            st.rerun()
