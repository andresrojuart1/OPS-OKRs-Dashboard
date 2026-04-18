"""Objective card — Fintech Edition (Fixed Rendering)."""

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

# Design System Tokens
MUTED   = "#94A3B8"
CORAL   = "#ff9ab0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct_indicator(pct: float) -> str:
    color = "#2DD4BF" if pct >= 70 else ("#f8c56a" if pct >= 40 else "#e35276")
    return f"""
    <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:2rem; font-weight:800; color:{color}; letter-spacing:-0.04em;">{pct:.0f}%</span>
        <div style="font-size:0.7rem; font-weight:700; color:{color}; background:rgba(255,255,255,0.05); 
                    padding:2px 8px; border-radius:4px; border:1px solid rgba(255,255,255,0.1); 
                    text-transform:uppercase; letter-spacing:0.05em;">
            Trend Status
        </div>
    </div>
    """

def _fintech_progress_bar(pct: float) -> str:
    return f"""
    <div style="background:rgba(255,255,255,0.03); border-radius:999px; height:6px; margin-top:12px; position:relative; overflow:hidden;">
        <div style="height:100%; width:{pct:.1f}%; border-radius:999px; 
                    background:linear-gradient(90deg, #7c73f7, #2DD4BF); 
                    box-shadow:0 0 10px rgba(124,115,247,0.3);"></div>
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

    # Header section (Unified HTML call to avoid breaking Streamlit flow)
    st.markdown(f"""
    <div class="objective-card">
        <div style="margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">
                <span style="font-size:0.7rem; font-weight:700; color:#7c73f7; 
                             background:rgba(124,115,247,0.1); padding:3px 8px; border-radius:4px; 
                             text-transform:uppercase; letter-spacing:0.05em;">Performance</span>
                <span style="font-size:0.75rem; color:{MUTED}; font-weight:600;">{sub_team}</span>
            </div>
            {_pct_indicator(avg_pct)}
            <div style="font-size:1.15rem; font-weight:700; color:white; margin-top:12px; line-height:1.4;">
                {obj_title}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Actions Row (Streamlit buttons outside HTML tags)
    c1, c2, c3, _ = st.columns([0.4, 0.4, 1.2, 8])
    with c1:
        if st.button("✏️", key=f"eobj_{obj_id}", type="tertiary"): _edit_obj_dialog(obj_id, obj_title)
    with c2:
        if st.button("🗑️", key=f"dobj_{obj_id}", type="tertiary"): _confirm_delete_obj_dialog(obj_id, obj_title)
    with c3:
        if st.button("+ KR", key=f"akr_{obj_id}", type="tertiary"): add_kr_dialog(obj_id, obj_title)

    st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)

    if not obj_krs.empty:
        for _, kr in obj_krs.iterrows():
            _render_kr_row(kr, active_kr)
    
    st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR Row
# ---------------------------------------------------------------------------

def _render_kr_row(kr, active_kr: str) -> None:
    kr_id   = str(kr["id"])
    title   = kr["title"]
    pct     = compute_progress(kr)
    val_str = format_value(float(kr.get("current_value",0)), float(kr.get("target",0)), str(kr.get("unit","")))

    st.markdown(f"""
    <div class="kr-row-fintech">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="flex:1; padding-right:1rem;">
                <div style="font-size:0.9rem; font-weight:600; color:white; margin-bottom:4px;">{title}</div>
                <div style="font-size:0.8rem; color:{MUTED};">{val_str}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1rem; font-weight:700; color:#2DD4BF;">{pct:.0f}%</div>
            </div>
        </div>
        {_fintech_progress_bar(pct)}
    </div>
    """, unsafe_allow_html=True)

    c_upd, c_hist, c_edit, c_del, _ = st.columns([1.6, 1.2, 0.4, 0.4, 6])
    
    with c_upd:
        label = "Close" if active_kr == kr_id else "Update"
        if st.button(label, key=f"uk_{kr_id}", type="secondary" if active_kr != kr_id else "primary", use_container_width=True):
            st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
            st.rerun()
    
    with c_hist:
        if st.button("Logs", key=f"sh_{kr_id}", type="tertiary"):
            st.session_state[f"h_{kr_id}"] = not st.session_state.get(f"h_{kr_id}", False)
            st.rerun()

    with c_edit:
        if st.button("✏️", key=f"ek_{kr_id}", type="tertiary"):
            _edit_kr_dialog(kr_id, title, float(kr['target']), str(kr['unit']))
    
    with c_del:
        if st.button("🗑️", key=f"dk_{kr_id}", type="tertiary"):
            _confirm_delete_kr_dialog(kr_id, title)

    if active_kr == kr_id: _render_update_form(kr)
    if st.session_state.get(f"h_{kr_id}"): _render_history(kr_id)


# ---------------------------------------------------------------------------
# Form & History
# ---------------------------------------------------------------------------

def _render_update_form(kr) -> None:
    kr_id = str(kr["id"])
    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1: new_val = st.number_input("Nuevo Valor", value=float(kr.get("current_value",0)))
        with c2: st.slider("Confianza", 1, 5, 3, key=f"conf_{kr_id}")
        notes = st.text_input("Comentarios")
        if st.form_submit_button("Guardar", use_container_width=True):
            from sheets import update_kr_value
            update_kr_value(kr_id=kr_id, new_value=float(new_val), week_notes=notes, updated_by=st.session_state.get("user",{}).get("email","?"))
            st.session_state["updating_kr"] = None
            st.rerun()

def _render_history(kr_id: str) -> None:
    from sheets import load_updates_for_kr, delete_update_by_id
    upds = load_updates_for_kr(kr_id)
    for _, row in upds.iterrows():
        st.markdown(f'<div style="font-size:11px; color:#94A3B8; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05);"><b>{row["new_value"]}</b> · {row["week_notes"]}</div>', unsafe_allow_html=True)
        if st.button("🗑️", key=f"delu_{row['id']}", type="tertiary"):
            delete_update_by_id(str(row["id"]))
            st.rerun()

# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Editar Objetivo")
def _edit_obj_dialog(obj_id: str, current_title: str) -> None:
    new_title = st.text_area("Nuevo Título", value=current_title, height=100)
    if st.button("Guardar Cambios", type="primary", use_container_width=True):
        update_objective(obj_id, new_title.strip())
        st.rerun()

@st.dialog("Eliminar Objetivo")
def _confirm_delete_obj_dialog(obj_id: str, obj_title: str) -> None:
    st.error(f"¿Eliminar definitivamente?")
    st.caption(obj_title)
    if st.button("Eliminar Todo", type="primary", use_container_width=True):
        delete_objective(obj_id)
        st.rerun()

@st.dialog("Editar KR")
def _edit_kr_dialog(kr_id: str, title: str, target: float, unit: str) -> None:
    nt = st.text_input("Título", value=title)
    nv = st.number_input("Target", value=target)
    nu = st.text_input("Unidad", value=unit)
    if st.button("Guardar", type="primary", use_container_width=True):
        update_kr_fields(kr_id, nt, nv, nu)
        st.rerun()

@st.dialog("Eliminar KR")
def _confirm_delete_kr_dialog(kr_id: str, title: str) -> None:
    st.warning(f"¿Eliminar {title}?")
    if st.button("Eliminar", type="primary", use_container_width=True):
        delete_kr_by_id(kr_id)
        st.rerun()

@st.dialog("Nuevo KR")
def add_kr_dialog(obj_id: str, obj_title: str) -> None:
    t = st.text_input("Nombre del KR")
    val = st.number_input("Target", value=100.0)
    u = st.text_input("Unidad", value="%")
    if st.button("Crear", type="primary", use_container_width=True):
        create_kr(obj_id, t, val, u)
        st.rerun()
