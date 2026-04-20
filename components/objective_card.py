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


# ---------------------------------------------------------------------------
# Visual helpers
# ---------------------------------------------------------------------------

def _pct_indicator(pct: float) -> str:
    color = GREEN if pct >= 70 else ("#f8c56a" if pct >= 40 else "#ff4b4b")
    return f"""<div style="display:flex; align-items:center; gap:8px;">
<span style="font-size:2.2rem; font-weight:800; color:white; letter-spacing:-0.05em;">{pct:.0f}%</span>
<div style="font-size:0.65rem; font-weight:700; color:{color}; background:rgba(255,255,255,0.03); padding:2px 6px; border-radius:4px; text-transform:uppercase;">Trend</div>
</div>"""


def _progress_bar(pct: float) -> str:
    color = PURPLE
    return f"""<div class="kr-progress-track">
<style>
@keyframes fillProgress {{
  0% {{ transform: scaleX(0); transform-origin: left; }}
  100% {{ transform: scaleX(1); transform-origin: left; }}
}}
</style>
<div style="height:100%; width:{pct:.1f}%; background:{color}; box-shadow:0 0 12px {color}44; animation: fillProgress 1s cubic-bezier(0.4, 0, 0.2, 1); border-radius:999px;"></div>
</div>"""


# ---------------------------------------------------------------------------
# Objective card
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, active_kr: str, is_primary: bool = False) -> None:
    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")

    # Type-safe filter: cast both sides to str to handle int IDs from Sheets
    if not krs_df.empty:
        obj_krs = krs_df[krs_df["objective_id"].astype(str) == obj_id]
    else:
        obj_krs = krs_df

    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    with st.container():
        # CSS trigger for card styling
        trigger_class = "fintech-card-trigger-primary" if is_primary else "fintech-card-trigger"
        st.markdown(f'<div class="{trigger_class}" style="display:none;"></div>', unsafe_allow_html=True)

        # Header
        sub_team_size = "11px"
        obj_title_size = "24px" if is_primary else "20px"

        st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <div style="margin-bottom: 8px;">
                <span style="font-size:{sub_team_size}; font-weight:700; color:{PURPLE}; text-transform:uppercase; letter-spacing:0.1em; opacity:0.8;">{sub_team}</span>
            </div>
            <div style="font-size:{obj_title_size}; font-weight:700; color:white; margin-bottom:1.25rem; line-height:1.3; letter-spacing:-0.01em;">{obj_title}</div>
            {_pct_indicator(avg_pct)}
        </div>
        """, unsafe_allow_html=True)

        # Objective toolbar
        c1, c2, c3, _ = st.columns([0.4, 0.4, 0.5, 9])
        with c1:
            if st.button(" ", icon=":material/edit:", key=f"eobj_{obj_id}", type="tertiary", help="Edit Objective"):
                _edit_obj_dialog(obj_id, obj_title)
        with c2:
            if st.button(" ", icon=":material/delete:", key=f"dobj_{obj_id}", type="tertiary", help="Delete Objective"):
                _confirm_delete_obj_dialog(obj_id, obj_title)
        with c3:
            if st.button(" ", icon=":material/add:", key=f"akr_{obj_id}", type="tertiary", help="Add KR"):
                add_kr_dialog(obj_id, obj_title)

        # KRs list
        if not obj_krs.empty:
            for _, kr in obj_krs.iterrows():
                _render_kr_row(kr, active_kr)
        else:
            st.markdown(f'<div style="color:{MUTED}; padding:1rem 0; font-size:0.8rem;">No results tracked yet.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR row
# ---------------------------------------------------------------------------

def _render_kr_row(kr, active_kr: str) -> None:
    kr_id = str(kr["id"])
    title = kr["title"]
    pct = compute_progress(kr)
    val_str = format_value(
        float(kr.get("current_value", 0)),
        float(kr.get("target", 0)),
        str(kr.get("unit", "")),
    )

    with st.container():
        # CSS trigger for KR card styling
        st.markdown('<div class="kr-card-trigger"></div>', unsafe_allow_html=True)

        # Primary zone: Title/Info and Progress/Update
        c_left, c_right = st.columns([2.5, 1.2])

        with c_left:
            st.markdown(f"""
            <div style="margin-bottom:8px;">
                <div style="font-size:16px; font-weight:600; color:#FFFFFF; line-height:1.2; margin-bottom:4px;">{title}</div>
                <div style="font-size:13px; color:rgba(255,255,255,0.6); font-weight:500;">{val_str}</div>
            </div>
            """, unsafe_allow_html=True)

            # Secondary actions row (subtle)
            cs1, cs2, cs3, _ = st.columns([0.15, 0.15, 0.35, 3])
            with cs1:
                if st.button(" ", icon=":material/description:", key=f"sh_{kr_id}", type="tertiary", help="Logs"):
                    st.session_state[f"h_{kr_id}"] = not st.session_state.get(f"h_{kr_id}", False)
                    st.rerun()
            with cs2:
                if st.button(" ", icon=":material/edit:", key=f"ek_{kr_id}", type="tertiary", help="Edit"):
                    _edit_kr_dialog(kr_id, title)
            with cs3:
                if st.button(" ", icon=":material/delete:", key=f"dk_{kr_id}", type="tertiary", help="Delete"):
                    _confirm_delete_kr_dialog(kr_id, title)

        with c_right:
            st.markdown(f"""
            <div style="text-align:right; margin-bottom:12px;">
                <div style="font-size:18px; font-weight:700; color:{GREEN}; letter-spacing:-0.02em;">{pct:.0f}%</div>
                <div style="font-size:10px; color:rgba(255,255,255,0.3); text-transform:uppercase; font-weight:800; letter-spacing:0.05em;">Achievement</div>
            </div>
            """, unsafe_allow_html=True)

            # Primary Update Action
            upd_icon = ":material/sync:" if active_kr != kr_id else ":material/close:"
            if st.button("Update", icon=upd_icon, key=f"uk_{kr_id}", type="secondary", use_container_width=True):
                st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
                st.rerun()

        # Bottom zone: progress bar
        st.markdown(_progress_bar(pct), unsafe_allow_html=True)

    # Expandable sections render OUTSIDE the KR card container
    # to avoid inheriting KR card CSS (double backgrounds)
    if active_kr == kr_id:
        _render_update_form(kr)
    if st.session_state.get(f"h_{kr_id}"):
        _render_history(kr_id)


# ---------------------------------------------------------------------------
# Update form
# ---------------------------------------------------------------------------

def _render_update_form(kr) -> None:
    kr_id = str(kr["id"])
    st.markdown(
        f'<div style="background:rgba(122,80,247,0.04); padding:1rem; border-radius:12px; '
        f'border:1px solid rgba(122,80,247,0.15); margin:0.75rem 0;">',
        unsafe_allow_html=True,
    )
    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            new_val = st.number_input("Value", value=float(kr.get("current_value", 0)))
        with c2:
            conf = st.slider("Confidence", 1, 5, 3)
        notes = st.text_input("Narrative")
        blockers = st.text_input("Blockers")

        if st.form_submit_button("Register", use_container_width=True):
            try:
                update_kr_value(
                    kr_id=kr_id,
                    new_value=float(new_val),
                    week_notes=notes,
                    blockers=blockers,
                    confidence=conf,
                    updated_by=st.session_state.get("user", {}).get("email", "?"),
                )
                st.session_state["updating_kr"] = None
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to save update: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def _render_history(kr_id: str) -> None:
    try:
        upds = load_updates_for_kr(kr_id)
    except Exception as exc:
        st.error(f"Failed to load history: {exc}")
        return

    if upds.empty:
        st.caption("No update history yet.")
        return

    for _, row in upds.iterrows():
        value = row.get("new_value", "—")
        notes = row.get("week_notes", "")
        row_id = str(row.get("id", ""))
        st.markdown(
            f'<div style="font-size:10px; color:{MUTED}; padding:6px 0; '
            f'border-bottom:1px solid rgba(255,255,255,0.02);">'
            f'<b>{value}</b> · {notes}</div>',
            unsafe_allow_html=True,
        )
        if row_id and st.button(" ", icon=":material/delete:", key=f"delu_{row_id}", type="tertiary", help="Delete update"):
            try:
                delete_update_by_id(row_id)
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to delete update: {exc}")


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Edit Objective")
def _edit_obj_dialog(obj_id: str, title: str) -> None:
    nt = st.text_area("Title", value=title, height=80)
    if st.button("Save", type="primary", use_container_width=True):
        try:
            update_objective(obj_id, nt.strip())
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to save: {exc}")


@st.dialog("Delete Objective")
def _confirm_delete_obj_dialog(obj_id: str, title: str) -> None:
    st.warning(f"This will permanently delete **{title}** and all its Key Results.")
    if st.button("Confirm Delete", type="primary", use_container_width=True):
        try:
            delete_objective(obj_id)
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to delete: {exc}")


@st.dialog("Edit Key Result")
def _edit_kr_dialog(kr_id: str, title: str) -> None:
    from sheets import load_key_results, update_kr_fields

    df = load_key_results()
    kr_match = df[df["id"].astype(str) == str(kr_id)] if not df.empty else df
    kr = kr_match.iloc[0] if not kr_match.empty else {}

    nt = st.text_input("Title", value=kr.get("title", title))
    c1, c2 = st.columns(2)
    with c1:
        ntgt = st.number_input("Target", value=float(kr.get("target", 0)))
    with c2:
        nunit = st.text_input("Unit", value=str(kr.get("unit", "")))

    if st.button("Save Changes", type="primary", use_container_width=True):
        try:
            update_kr_fields(kr_id, nt.strip(), float(ntgt), nunit.strip())
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to save: {exc}")


@st.dialog("Delete KR")
def _confirm_delete_kr_dialog(kr_id: str, title: str) -> None:
    st.warning(f"This will permanently delete: **{title}**")
    if st.button("Delete", type="primary", use_container_width=True):
        try:
            delete_kr_by_id(kr_id)
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to delete: {exc}")


@st.dialog("New KR")
def add_kr_dialog(obj_id: str, title: str) -> None:
    name = st.text_input("Title")
    col1, col2 = st.columns(2)
    with col1:
        tgt = st.number_input("Target", min_value=1.0, value=100.0)
    with col2:
        unit = st.text_input("Unit", value="%")
    if st.button("Create", type="primary", use_container_width=True):
        if not name.strip():
            st.error("Title cannot be empty.")
            return
        try:
            create_kr(obj_id, name.strip(), float(tgt), unit.strip())
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to create KR: {exc}")
