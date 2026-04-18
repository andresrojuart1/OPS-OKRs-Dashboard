"""Objective card — Ultra-Minimalist Fintech Edition."""

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

MUTED = "#94A3B8"

def _pct_indicator(pct: float) -> str:
    color = "#2DD4BF" if pct >= 70 else ("#f8c56a" if pct >= 40 else "#e35276")
    return f"""<div style="display:flex; align-items:center; gap:8px;">
<span style="font-size:2.2rem; font-weight:800; color:{color}; letter-spacing:-0.05em;">{pct:.0f}%</span>
<div style="font-size:0.65rem; font-weight:700; color:{color}; background:rgba(255,255,255,0.03); padding:2px 6px; border-radius:3px; border:1px solid rgba(255,255,255,0.08); text-transform:uppercase;">Trend</div>
</div>"""

def _progress_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.02); border-radius:999px; height:5px; margin-top:8px; overflow:hidden;">
<div style="height:100%; width:{pct:.1f}%; background:linear-gradient(90deg, #7c73f7, #2DD4BF); box-shadow:0 0 6px rgba(124,115,247,0.2);"></div>
</div>"""

def render_objective_card(obj_row, krs_df, active_kr: str) -> None:
    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")
    obj_krs = krs_df[krs_df["objective_id"] == obj_id] if not krs_df.empty else krs_df
    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    # Wrap in specific container to trigger CSS
    with st.container():
        st.markdown('<div class="fintech-card-trigger"></div>', unsafe_allow_html=True)
        
        # Header
        st.markdown(f"""<div class="objective-section">
<div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
<span style="font-size:0.65rem; font-weight:700; color:#7c73f7; text-transform:uppercase; letter-spacing:0.05em;">{sub_team}</span>
<span style="height:12px; width:1px; background:rgba(255,255,255,0.1);"></span>
<span style="font-size:0.65rem; color:{MUTED}; font-weight:600; text-transform:uppercase;">Performance Index</span>
</div>
{_pct_indicator(avg_pct)}
<div style="font-size:1.2rem; font-weight:700; color:white; margin-top:0.8rem; line-height:1.4;">{obj_title}</div>
</div>""", unsafe_allow_html=True)

        # Subtle Actions for Objective
        c1, c2, c3, _ = st.columns([0.4, 0.4, 1.2, 8])
        with c1:
            if st.button("✏️", key=f"eobj_{obj_id}"): _edit_obj_dialog(obj_id, obj_title)
        with c2:
            if st.button("🗑️", key=f"dobj_{obj_id}"): _confirm_delete_obj_dialog(obj_id, obj_title)
        with c3:
            if st.button("+ KR", key=f"akr_{obj_id}"): add_kr_dialog(obj_id, obj_title)

        st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)

        if not obj_krs.empty:
            for _, kr in obj_krs.iterrows():
                _render_kr_row(kr, active_kr)
        else:
            st.markdown(f'<div style="color:{MUTED}; font-size:0.8rem; padding:0.5rem;">No Key Results.</div>', unsafe_allow_html=True)


def _render_kr_row(kr, active_kr: str) -> None:
    kr_id = str(kr["id"])
    title = kr["title"]
    pct = compute_progress(kr)
    val_str = format_value(float(kr.get("current_value",0)), float(kr.get("target",0)), str(kr.get("unit","")))

    st.markdown(f"""<div class="kr-row-fintech">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
<div style="flex:1; padding-right:1rem;">
<div style="font-size:0.9rem; font-weight:600; color:white; margin-bottom:2px;">{title}</div>
<div style="font-size:0.75rem; color:{MUTED};">{val_str}</div>
</div>
<div style="text-align:right;">
<div style="font-size:0.95rem; font-weight:700; color:#2DD4BF;">{pct:.0f}%</div>
<div style="font-size:0.55rem; color:{MUTED}; text-transform:uppercase; font-weight:700; letter-spacing:0.04em;">Status</div>
</div>
</div>
{_progress_bar(pct)}
</div>""", unsafe_allow_html=True)

    # Minimalist Action Row
    c_upd, c_hist, c_ed, c_del, _ = st.columns([1.5, 0.8, 0.4, 0.4, 6.9])
    with c_upd:
        label = "Close" if active_kr == kr_id else "Update"
        if st.button(label, key=f"uk_{kr_id}", type="secondary" if active_kr != kr_id else "primary", use_container_width=True):
            st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
            st.rerun()
    with c_hist:
        if st.button("Logs", key=f"sh_{kr_id}"):
            st.session_state[f"h_{kr_id}"] = not st.session_state.get(f"h_{kr_id}", False)
            st.rerun()
    with c_ed:
        if st.button("✏️", key=f"ek_{kr_id}"): _edit_kr_dialog(kr_id, title, float(kr['target']), str(kr['unit']))
    with c_del:
        if st.button("🗑️", key=f"dk_{kr_id}"): _confirm_delete_kr_dialog(kr_id, title)

    if active_kr == kr_id: _render_update_form(kr)
    if st.session_state.get(f"h_{kr_id}"): _render_history(kr_id)


def _render_update_form(kr) -> None:
    kr_id = str(kr["id"])
    st.markdown('<div style="background:rgba(255,255,255,0.01); padding:0.8rem; border-radius:8px; border:1px solid rgba(255,255,255,0.04); margin:6px 0;">', unsafe_allow_html=True)
    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1: new_val = st.number_input("Value", value=float(kr.get("current_value",0)))
        with c2: st.slider("Conf", 1, 5, 3, key=f"conf_{kr_id}")
        notes = st.text_input("Notes")
        if st.form_submit_button("Save", use_container_width=True):
            from sheets import update_kr_value
            update_kr_value(kr_id=kr_id, new_value=float(new_val), week_notes=notes, updated_by=st.session_state.get("user",{}).get("email","?"))
            st.session_state["updating_kr"] = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def _render_history(kr_id: str) -> None:
    from sheets import load_updates_for_kr, delete_update_by_id
    upds = load_updates_for_kr(kr_id)
    for _, row in upds.iterrows():
        st.markdown(f'<div style="font-size:10px; color:#94A3B8; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.03);"><b>{row["new_value"]}</b> · {row["week_notes"]}</div>', unsafe_allow_html=True)
        if st.button("🗑️", key=f"delu_{row['id']}"):
            delete_update_by_id(str(row["id"]))
            st.rerun()

@st.dialog("Editar Objetivo")
def _edit_obj_dialog(obj_id: str, title: str) -> None:
    nt = st.text_area("Nuevo Título", value=title, height=80)
    if st.button("Guardar", type="primary"):
        update_objective(obj_id, nt.strip())
        st.rerun()

@st.dialog("Eliminar")
def _confirm_delete_obj_dialog(obj_id: str, title: str) -> None:
    st.error("¿Eliminar?")
    if st.button("Confirmar", type="primary"):
        delete_objective(obj_id)
        st.rerun()

@st.dialog("Editar KR")
def _edit_kr_dialog(kr_id: str, title: str, target: float, unit: str) -> None:
    st.text_input("Name", value=title)
    st.button("Update", type="primary")

@st.dialog("Eliminar KR")
def _confirm_delete_kr_dialog(kr_id: str, title: str) -> None:
    if st.button("Eliminar", type="primary"):
        delete_kr_by_id(kr_id)
        st.rerun()

@st.dialog("Nuevo KR")
def add_kr_dialog(obj_id: str, title: str) -> None:
    t = st.text_input("Nombre")
    if st.button("Crear", type="primary"):
        create_kr(obj_id, t, 100, "%")
        st.rerun()
