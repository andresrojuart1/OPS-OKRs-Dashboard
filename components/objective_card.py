"""Objective card — Ontop Ghost Edition."""

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

MUTED = "#A1A1AA"
PURPLE = "#7A50F7"
GREEN = "#2DD4BF"

def _pct_indicator(pct: float) -> str:
    color = GREEN if pct >= 70 else ("#f8c56a" if pct >= 40 else "#ff4b4b")
    return f"""<div style="display:flex; align-items:center; gap:8px;">
<span style="font-size:2.2rem; font-weight:800; color:white; letter-spacing:-0.05em;">{pct:.0f}%</span>
<div style="font-size:0.65rem; font-weight:700; color:{color}; background:rgba(255,255,255,0.03); padding:2px 6px; border-radius:4px; text-transform:uppercase;">Trend</div>
</div>"""

def _progress_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.03); border-radius:999px; height:5px; margin:10px 0; overflow:hidden;">
<style>
@keyframes fillProgress {{
  0% {{ transform: scaleX(0); transform-origin: left; }}
  100% {{ transform: scaleX(1); transform-origin: left; }}
}}
</style>
<div style="height:100%; width:{pct:.1f}%; background:{PURPLE}; box-shadow:0 0 8px rgba(122, 80, 247, 0.3); animation: fillProgress 1s cubic-bezier(0.4, 0, 0.2, 1);"></div>
</div>"""

def render_objective_card(obj_row, krs_df, active_kr: str, is_primary: bool = False) -> None:
    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")
    obj_krs = krs_df[krs_df["objective_id"] == obj_id] if not krs_df.empty else krs_df
    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    with st.container():
        # Clean trigger to avoid layout shift
        trigger_class = "fintech-card-trigger-primary" if is_primary else "fintech-card-trigger"
        st.markdown(f'<div class="{trigger_class}" style="display:none;"></div>', unsafe_allow_html=True)
        
        # Header - Synchronized sizes as requested
        # Sub-team label is 1.2rem, Objective is 1.15rem, KRs are 1.05rem
        sub_team_size = "1.2rem"
        obj_title_size = "1.15rem"
        
        st.markdown(f"""
        <div class="objective-section" style="border:none; margin-bottom: 1.5rem;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                <span style="font-size:{sub_team_size}; font-weight:800; color:{PURPLE}; text-transform:uppercase; letter-spacing:0.04em;">{sub_team}</span>
            </div>
            <div style="font-size:{obj_title_size}; font-weight:800; color:white; margin-top:0.4rem; margin-bottom:1.2rem; line-height:1.4;">{obj_title}</div>
            {_pct_indicator(avg_pct)}
        </div>
        """, unsafe_allow_html=True)

        # GHOST TOOLBAR for Objective
        c1, c2, c3, _ = st.columns([0.4, 0.4, 0.5, 9])
        with c1:
            if st.button(" ", icon=":material/edit:", key=f"eobj_{obj_id}", type="tertiary", help="Edit Objective"): _edit_obj_dialog(obj_id, obj_title)
        with c2:
            if st.button(" ", icon=":material/delete:", key=f"dobj_{obj_id}", type="tertiary", help="Delete Objective"): _confirm_delete_obj_dialog(obj_id, obj_title)
        with c3:
            if st.button(" ", icon=":material/add:", key=f"akr_{obj_id}", type="tertiary", help="Add KR"): add_kr_dialog(obj_id, obj_title)

        # KRs list
        if not obj_krs.empty:
            for _, kr in obj_krs.iterrows():
                _render_kr_row(kr, active_kr)
        else:
            st.markdown(f'<div style="color:{MUTED}; padding:1rem 0; font-size:0.8rem;">No results tracked yet.</div>', unsafe_allow_html=True)


def _render_kr_row(kr, active_kr: str) -> None:
    kr_id = str(kr["id"])
    title = kr["title"]
    pct = compute_progress(kr)
    val_str = format_value(float(kr.get("current_value",0)), float(kr.get("target",0)), str(kr.get("unit","")))

    st.markdown(f"""<div class="kr-row-fintech">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
<div style="flex:1; padding-right:1rem;">
<div style="font-size:1.05rem; font-weight:600; color:white; margin-bottom:2px;">{title}</div>
<div style="font-size:0.85rem; color:{MUTED};">{val_str}</div>
</div>
<div style="text-align:right;">
<div style="font-size:1.05rem; font-weight:700; color:{GREEN};">{pct:.0f}%</div>
<div style="font-size:0.6rem; color:{MUTED}; text-transform:uppercase; font-weight:700;">Status</div>
</div>
</div>
{_progress_bar(pct)}
</div>""", unsafe_allow_html=True)

    # Added spacing between KR list item and action buttons
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # GHOST ACTION ROW for KR
    c_upd, c_hist, c_ed, c_del, _ = st.columns([0.35, 0.35, 0.35, 0.35, 8.6])
    with c_upd:
        icon = ":material/refresh:" if active_kr != kr_id else ":material/close:"
        if st.button(" ", icon=icon, key=f"uk_{kr_id}", type="tertiary", help="Update"):
            st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
            st.rerun()
    with c_hist:
        if st.button(" ", icon=":material/description:", key=f"sh_{kr_id}", type="tertiary", help="Logs"):
            st.session_state[f"h_{kr_id}"] = not st.session_state.get(f"h_{kr_id}", False)
            st.rerun()
    with c_ed:
        if st.button(" ", icon=":material/edit:", key=f"ek_{kr_id}", type="tertiary", help="Edit"): _edit_kr_dialog(kr_id, title)
    with c_del:
        if st.button(" ", icon=":material/delete:", key=f"dk_{kr_id}", type="tertiary", help="Delete"): _confirm_delete_kr_dialog(kr_id, title)

    if active_kr == kr_id: _render_update_form(kr)
    if st.session_state.get(f"h_{kr_id}"): _render_history(kr_id)


def _render_update_form(kr) -> None:
    kr_id = str(kr["id"])
    st.markdown(f'<div style="background:rgba(255,255,255,0.01); padding:0.8rem; border-radius:10px; border:1px solid {PURPLE}22; margin:0.5rem 0;">', unsafe_allow_html=True)
    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1: new_val = st.number_input("Value", value=float(kr.get("current_value",0)))
        with c2: st.slider("Conf", 1, 5, 3, key=f"cv_{kr_id}")
        notes = st.text_input("Narrative")
        if st.form_submit_button("Register", use_container_width=True):
            from sheets import update_kr_value
            update_kr_value(kr_id=kr_id, new_value=float(new_val), week_notes=notes, updated_by=st.session_state.get("user",{}).get("email","?"))
            st.session_state["updating_kr"] = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def _render_history(kr_id: str) -> None:
    from sheets import load_updates_for_kr, delete_update_by_id
    upds = load_updates_for_kr(kr_id)
    for _, row in upds.iterrows():
        st.markdown(f'<div style="font-size:10px; color:{MUTED}; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.02);"><b>{row["new_value"]}</b> · {row["week_notes"]}</div>', unsafe_allow_html=True)
        if st.button(" ", icon=":material/delete:", key=f"delu_{row['id']}", type="tertiary", help="Delete update"):
            delete_update_by_id(str(row["id"]))
            st.rerun()

@st.dialog("Edit Objective")
def _edit_obj_dialog(obj_id: str, title: str) -> None:
    nt = st.text_area("Title", value=title, height=80)
    if st.button("Save", type="primary"):
        update_objective(obj_id, nt.strip())
        st.rerun()

@st.dialog("Delete Objective")
def _confirm_delete_obj_dialog(obj_id: str, title: str) -> None:
    st.error("Delete this objective?")
    if st.button("Confirm", type="primary"):
        delete_objective(obj_id)
        st.rerun()

@st.dialog("Edit KR")
def _edit_kr_dialog(kr_id: str, title: str) -> None:
    st.text_input("Name", value=title)
    st.button("Update", type="primary")

@st.dialog("Delete KR")
def _confirm_delete_kr_dialog(kr_id: str, title: str) -> None:
    st.error(f"Delete KR: {title}?")
    if st.button("Delete", type="primary"):
        delete_kr_by_id(kr_id)
        st.rerun()

@st.dialog("New KR")
def add_kr_dialog(obj_id: str, title: str) -> None:
    name = st.text_input("Title")
    col1, col2 = st.columns(2)
    with col1: tgt = st.number_input("Target", min_value=1.0, value=100.0)
    with col2: unit = st.text_input("Unit", value="%")
    if st.button("Create", type="primary"):
        create_kr(obj_id, name.strip(), float(tgt), unit.strip())
        st.rerun()
