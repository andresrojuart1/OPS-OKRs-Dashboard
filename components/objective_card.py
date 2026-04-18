"""Objective card — Tight High Density version."""

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

CORAL  = "#ff9ab0"
PURPLE = "#7c73f7"
BORDER = "rgba(255,255,255,0.05)"
TEXT1  = "#FFFFFF"
TEXT2  = "#B8B8C8"
MUTED  = "#6B6B7E"

# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Editar Objetivo")
def _edit_obj_dialog(obj_id: str, current_title: str) -> None:
    new_title = st.text_area("Título", value=current_title, height=80)
    if st.button("Guardar", type="primary", use_container_width=True):
        update_objective(obj_id, new_title.strip())
        st.rerun()

@st.dialog("Confirmar eliminación de Objetivo")
def _confirm_delete_obj_dialog(obj_id: str, obj_title: str) -> None:
    st.error(f"¿Eliminar Objetivo y KRs?")
    st.caption(obj_title)
    if st.button("Eliminar Todo", type="primary", use_container_width=True):
        delete_objective(obj_id)
        st.rerun()

@st.dialog("Editar KR")
def _edit_kr_dialog(kr_id: str, current_title: str, current_target: float, current_unit: str) -> None:
    new_title  = st.text_input("Título", value=current_title)
    new_target = st.number_input("Target", value=float(current_target))
    new_unit   = st.text_input("Unidad", value=current_unit)
    if st.button("Guardar", type="primary", use_container_width=True):
        update_kr_fields(kr_id, new_title, new_target, new_unit)
        st.rerun()

@st.dialog("Confirmar eliminación de KR")
def _confirm_delete_kr_dialog(kr_id: str, kr_title: str) -> None:
    st.warning(f"¿Eliminar KR?")
    st.caption(kr_title)
    if st.button("Eliminar", type="primary", use_container_width=True):
        delete_kr_by_id(kr_id)
        st.rerun()

@st.dialog("New KR")
def add_kr_dialog(objective_id: str, objective_title: str) -> None:
    title = st.text_input("Name")
    c1, c2 = st.columns(2)
    with c1: target = st.number_input("Target", value=100.0)
    with c2: unit = st.text_input("Unit", value="%")
    if st.button("Create", type="primary", use_container_width=True):
        create_kr(objective_id, title, target, unit)
        st.rerun()

@st.dialog("Confirmar eliminación de update")
def _confirm_delete_update_dialog(update_id: str) -> None:
    if st.button("Confirmar Eliminar", type="primary", use_container_width=True):
        delete_update_by_id(update_id)
        st.rerun()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct_badge(pct: float) -> str:
    color = "#7ee2a8" if pct >= 70 else ("#f8c56a" if pct >= 40 else "#ff9ab0")
    bg = "rgba(255,255,255,0.05)"
    return f'<span class="ontop-status-badge" style="color:{color}; background:{bg};">{pct:.0f}%</span>'

def _progress_bar(pct: float) -> str:
    return f'<div class="progress-track"><div class="progress-fill" style="width:{pct:.1f}%;"></div></div>'

# ---------------------------------------------------------------------------
# Objective Card
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, active_kr: str) -> None:
    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")

    obj_krs = krs_df[krs_df["objective_id"] == obj_id] if not krs_df.empty else krs_df
    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    st.markdown(f"""
    <div class="okr-card">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            {_pct_badge(avg_pct)}
            <span style="font-size:10px; color:{MUTED}; text-transform:uppercase;">{sub_team}</span>
        </div>
        <div class="objective-title">{obj_title}</div>
    </div>
    """, unsafe_allow_html=True)

    # Ultra compact action icons for Objective
    c1, c2, c3, _ = st.columns([0.4, 0.4, 1.2, 8])
    with c1: 
        if st.button("✏️", key=f"eo_{obj_id}", type="tertiary"): _edit_obj_dialog(obj_id, obj_title)
    with c2: 
        if st.button("🗑️", key=f"do_{obj_id}", type="tertiary"): _confirm_delete_obj_dialog(obj_id, obj_title)
    with c3: 
        if st.button("+ KR", key=f"ak_{obj_id}", type="tertiary"): add_kr_dialog(obj_id, obj_title)

    if not obj_krs.empty:
        for _, kr in obj_krs.iterrows():
            _render_kr_row(kr, active_kr)
    
    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# KR Row
# ---------------------------------------------------------------------------

def _render_kr_row(kr, active_kr: str) -> None:
    kr_id   = str(kr["id"])
    title   = kr["title"]
    pct     = compute_progress(kr)
    val_str = format_value(float(kr.get("current_value",0)), float(kr.get("target",0)), str(kr.get("unit","")))

    st.markdown(f"""
    <div class="kr-row">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div class="kr-title">{title}</div>
            <div style="font-size:11px; font-weight:700; color:{CORAL};">{pct:.0f}%</div>
        </div>
        <div style="font-size:10px; color:{MUTED}; margin-bottom:2px;">{val_str}</div>
        {_progress_bar(pct)}
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([0.4, 0.4, 2, 5, 2])
    with c1:
        if st.button("✏️", key=f"ek_{kr_id}", type="tertiary"): _edit_kr_dialog(kr_id, title, float(kr['target']), str(kr['unit']))
    with c2:
        if st.button("🗑️", key=f"dk_{kr_id}", type="tertiary"): _confirm_delete_kr_dialog(kr_id, title)
    with c3:
        hist_key = f"h_{kr_id}"
        st.button("Updates" if not st.session_state.get(hist_key) else "Hide", key=f"sh_{kr_id}", type="tertiary", 
                  on_click=lambda k=hist_key: st.session_state.update({k: not st.session_state.get(k, False)}))
    with c5:
        is_upd = active_kr == kr_id
        st.button("Update" if not is_upd else "Close", key=f"uk_{kr_id}", type="secondary" if not is_upd else "primary", use_container_width=True,
                  on_click=lambda: st.session_state.update({"updating_kr": None if active_kr == kr_id else kr_id}))

    if active_kr == kr_id: _render_update_form(kr)
    if st.session_state.get(f"h_{kr_id}"): _render_history(kr_id)

# ---------------------------------------------------------------------------
# Forms & History (Optimized for density)
# ---------------------------------------------------------------------------

def _render_update_form(kr) -> None:
    kr_id = str(kr["id"])
    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1: new_val = st.number_input("Value", value=float(kr['current_value']))
        with c2: conf = st.slider("Conf", 1, 5, 3)
        notes = st.text_input("Notes", placeholder="What happened?")
        if st.form_submit_button("Save Update", use_container_width=True):
            from sheets import update_kr_value
            update_kr_value(kr_id=kr_id, new_value=float(new_val), week_notes=notes, confidence=int(conf), updated_by=st.session_state.get("user",{}).get("email","?"))
            st.session_state["updating_kr"] = None
            st.rerun()

def _render_history(kr_id: str) -> None:
    from sheets import load_updates_for_kr
    upds = load_updates_for_kr(kr_id)
    for _, row in upds.iterrows():
        st.markdown(f'<div style="font-size:11px; padding:4px 1rem; border-bottom:1px solid rgba(255,255,255,0.05);"><b>{row["new_value"]}</b> · {row["week_notes"]}</div>', unsafe_allow_html=True)
        if st.button("🗑️", key=f"du_{row['id']}", type="tertiary"): _confirm_delete_update_dialog(row['id'])
