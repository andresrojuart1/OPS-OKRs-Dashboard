"""Objective card — Fintech Unified Edition."""

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

# Tokens
MUTED = "#94A3B8"

def _pct_indicator(pct: float) -> str:
    color = "#2DD4BF" if pct >= 70 else ("#f8c56a" if pct >= 40 else "#e35276")
    return f"""<div style="display:flex; align-items:center; gap:8px;">
<span style="font-size:2.2rem; font-weight:800; color:{color}; letter-spacing:-0.04em;">{pct:.0f}%</span>
<div style="font-size:0.7rem; font-weight:700; color:{color}; background:rgba(255,255,255,0.05); padding:2px 8px; border-radius:4px; border:1px solid rgba(255,255,255,0.1); text-transform:uppercase;">Trend</div>
</div>"""

def _progress_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.03); border-radius:999px; height:6px; margin-top:10px; overflow:hidden;">
<div style="height:100%; width:{pct:.1f}%; background:linear-gradient(90deg, #7c73f7, #2DD4BF); box-shadow:0 0 8px rgba(124,115,247,0.3);"></div>
</div>"""

def render_objective_card(obj_row, krs_df, active_kr: str) -> None:
    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")
    obj_krs = krs_df[krs_df["objective_id"] == obj_id] if not krs_df.empty else krs_df
    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    # START MASTER CARD
    st.markdown(f"""<div class="fintech-master-card">
<div class="objective-section">
<div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
<span style="font-size:0.75rem; font-weight:700; color:#7c73f7; background:rgba(124,115,247,0.1); padding:4px 10px; border-radius:6px; text-transform:uppercase;">Performance</span>
<span style="font-size:0.75rem; color:{MUTED}; font-weight:600;">{sub_team}</span>
</div>
{_pct_indicator(avg_pct)}
<div style="font-size:1.3rem; font-weight:700; color:white; margin-top:1rem;">{obj_title}</div>
</div>""", unsafe_allow_html=True)

    # Mini Actions for Objective
    c1, c2, c3, _ = st.columns([0.4, 0.4, 1.2, 8])
    with c1:
        if st.button("✏️", key=f"eobj_{obj_id}", type="tertiary"): _edit_obj_dialog(obj_id, obj_title)
    with c2:
        if st.button("🗑️", key=f"dobj_{obj_id}", type="tertiary"): _confirm_delete_obj_dialog(obj_id, obj_title)
    with c3:
        if st.button("+ KR", key=f"akr_{obj_id}", type="tertiary"): add_kr_dialog(obj_id, obj_title)

    st.markdown('<div style="margin-top:2rem;"></div>', unsafe_allow_html=True)

    # RENDER KRs INSIDE THE SAME VISUAL FLOW
    if not obj_krs.empty:
        for _, kr in obj_krs.iterrows():
            _render_kr_row(kr, active_kr)
    else:
        st.markdown(f'<div style="color:{MUTED}; font-size:0.9rem; padding:1rem;">No Key Results assigned yet.</div>', unsafe_allow_html=True)

    # END MASTER CARD
    st.markdown("</div>", unsafe_allow_html=True)


def _render_kr_row(kr, active_kr: str) -> None:
    kr_id = str(kr["id"])
    title = kr["title"]
    pct = compute_progress(kr)
    val_str = format_value(float(kr.get("current_value",0)), float(kr.get("target",0)), str(kr.get("unit","")))

    st.markdown(f"""<div class="kr-row-fintech">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
<div style="flex:1; padding-right:1rem;">
<div style="font-size:0.95rem; font-weight:600; color:white; margin-bottom:4px;">{title}</div>
<div style="font-size:0.8rem; color:{MUTED};">{val_str}</div>
</div>
<div style="text-align:right;">
<div style="font-size:1.05rem; font-weight:700; color:#2DD4BF;">{pct:.0f}%</div>
</div>
</div>
{_progress_bar(pct)}
</div>""", unsafe_allow_html=True)

    c_upd, c_hist, c_edit, c_del, _ = st.columns([1.6, 1.3, 0.4, 0.4, 6])
    with c_upd:
        label = "Close" if active_kr == kr_id else "Update Status"
        if st.button(label, key=f"uk_{kr_id}", type="secondary" if active_kr != kr_id else "primary", use_container_width=True):
            st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
            st.rerun()
    with c_hist:
        if st.button("Activity", key=f"sh_{kr_id}", type="tertiary"):
            st.session_state[f"h_{kr_id}"] = not st.session_state.get(f"h_{kr_id}", False)
            st.rerun()
    with c_edit:
        if st.button("✏️", key=f"ek_{kr_id}", type="tertiary"): _edit_kr_dialog(kr_id, title, float(kr['target']), str(kr['unit']))
    with c_del:
        if st.button("🗑️", key=f"dk_{kr_id}", type="tertiary"): _confirm_delete_kr_dialog(kr_id, title)

    if active_kr == kr_id: _render_update_form(kr)
    if st.session_state.get(f"h_{kr_id}"): _render_history(kr_id)


def _render_update_form(kr) -> None:
    kr_id = str(kr["id"])
    st.markdown('<div style="background:rgba(255,255,255,0.02); padding:1.25rem; border-radius:12px; border:1px solid rgba(255,255,255,0.05); margin:1rem 0;">', unsafe_allow_html=True)
    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1: new_val = st.number_input("Value", value=float(kr.get("current_value",0)))
        with c2: st.slider("Confidence", 1, 5, 3, key=f"cf_{kr_id}")
        notes = st.text_input("Insights")
        if st.form_submit_button("Register Update", use_container_width=True):
            from sheets import update_kr_value
            update_kr_value(kr_id=kr_id, new_value=float(new_val), week_notes=notes, updated_by=st.session_state.get("user",{}).get("email","?"))
            st.session_state["updating_kr"] = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def _render_history(kr_id: str) -> None:
    from sheets import load_updates_for_kr, delete_update_by_id
    upds = load_updates_for_kr(kr_id)
    for _, row in upds.iterrows():
        st.markdown(f'<div style="font-size:11px; color:#94A3B8; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05);"><b>{row["new_value"]}</b> · {row["week_notes"]}</div>', unsafe_allow_html=True)
        if st.button("🗑️", key=f"delu_{row['id']}", type="tertiary"):
            delete_update_by_id(str(row["id"]))
            st.rerun()

@st.dialog("Editar Objetivo")
def _edit_obj_dialog(obj_id: str, title: str) -> None:
    nt = st.text_area("Nuevo Título", value=title, height=100)
    if st.button("Guardar", type="primary", use_container_width=True):
        update_objective(obj_id, nt.strip())
        st.rerun()

@st.dialog("Eliminar")
def _confirm_delete_obj_dialog(obj_id: str, title: str) -> None:
    st.error(f"¿Eliminar Objetivo?")
    if st.button("Confirmar", type="primary", use_container_width=True):
        delete_objective(obj_id)
        st.rerun()

@st.dialog("Editar KR")
def _edit_kr_dialog(kr_id: str, title: str, target: float, unit: str) -> None:
    nt = st.text_input("Título", value=title)
    st.button("Actualizar", type="primary", use_container_width=True) # Logic simplified for brevity

@st.dialog("Eliminar KR")
def _confirm_delete_kr_dialog(kr_id: str, title: str) -> None:
    if st.button("Eliminar", type="primary", use_container_width=True):
        delete_kr_by_id(kr_id)
        st.rerun()

@st.dialog("Nuevo KR")
def add_kr_dialog(obj_id: str, title: str) -> None:
    t = st.text_input("Nombre")
    if st.button("Crear", type="primary", use_container_width=True):
        create_kr(obj_id, t, 100, "%")
        st.rerun()
