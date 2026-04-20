"""Objective card — Clean OKR layout.

Hierarchy: Sub-team → Objective → Key Results
Logic: Correct objective progress calculation (Average of KRs) & Time-Travel.
Design: Minimalist rows for boardroom scannability.
"""

import pandas as pd
import streamlit as st
from datetime import datetime, timezone

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
from observability import handle_error, track_action

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

MUTED = "rgba(255,255,255,0.4)"
PURPLE = "#7A50F7"
GREEN = "#2DD4BF"
YELLOW = "#f8c56a"
RED = "#ff4b4b"


def _pct_color(pct: float) -> str:
    # Use dynamic timeline threshold for executive status
    sel_week = st.session_state.get("selected_week", 1)
    sel_q = st.session_state.get("selected_quarter", "Q1 2026")
    q_starts = {"Q1 2026": 1, "Q2 2026": 14, "Q3 2026": 27, "Q4 2026": 40}
    start_wk = q_starts.get(sel_q, 1)
    weeks_elapsed = max(1, sel_week - start_wk + 1)
    expected_pct = (weeks_elapsed / 13.0) * 100
    
    if pct >= expected_pct: return GREEN
    if pct >= expected_pct * 0.6: return YELLOW
    return RED


def _get_week_from_ts(ts_str: str) -> int:
    try:
        dt = datetime.strptime(str(ts_str).strip(), "%Y-%m-%d %H:%M UTC")
        return dt.isocalendar()[1]
    except: return 0


def _obj_progress_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.06); border-radius:999px; height:8px; overflow:hidden; margin:8px 0 4px;">
<div style="height:100%; width:{max(pct, 0.5):.1f}%; border-radius:999px; background:linear-gradient(90deg, {PURPLE}, {GREEN}); transition: width 0.6s ease;"></div>
</div>"""


def _kr_progress_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.04); border-radius:999px; height:5px; overflow:hidden; margin:10px 0 0;">
<div style="height:100%; width:{max(pct, 0.5):.1f}%; border-radius:999px; background:{PURPLE}; transition: width 0.6s ease;"></div>
</div>"""


def _format_badge(value, unit: str) -> str:
    try: v = float(value)
    except: return str(value)
    u = unit.lower().strip()
    if u == "%": return f"{v:+.2f}%" if v != 0 else f"{v:.2f}%"
    if u in ("$", "$/month"):
        if v >= 1_000_000: return f"${v / 1_000_000:.1f}M"
        if v >= 1_000: return f"${v / 1_000:.0f}K"
        return f"${v:,.0f}"
    return f"{v:g} {unit}"


def _format_current_target(current: float, target: float, unit: str) -> str:
    u = unit.lower().strip()
    if u == "binary": return "Done ✓" if current >= 1 else "Pending"
    if u in ("$", "$/month"):
        def fmt(v):
            if v >= 1_000_000: return f"${v / 1_000_000:.1f}M"
            if v >= 1_000: return f"${v / 1_000:.0f}K"
            return f"${v:,.0f}"
        return f"Current: {fmt(current)} / Target: {fmt(target)}"
    return f"Current: {current:g} / Target: {target:g} {unit}"


def _get_hist_val(updates_df, kr_id: str, week: int):
    if updates_df.empty: return 0.0, None
    f = updates_df[updates_df["kr_id"].astype(str) == str(kr_id)].copy()
    
    # Normalize selected week to string for comparison
    sel_wk = str(week).strip()

    # Use explicit week_number column for filtering
    if "week_number" in f.columns:
        # Normalize column to string and strip
        f["week_number_str"] = f["week_number"].astype(str).str.strip()
        
        # For VALUE: we want latest up to this week
        val_res = f[f["week_number_str"].astype(float) <= float(sel_wk)].sort_values("updated_at", ascending=False)
        
        # For NARRATIVE: the user wants to see the update ONLY for the selected week
        # based on latest request "Show those updates ONLY when Week 14 is selected"
        narr_res = f[f["week_number_str"] == sel_wk].sort_values("updated_at", ascending=False)
    else:
        # Fallback to derivation
        f["wk"] = f["updated_at"].apply(_get_week_from_ts).astype(str).str.strip()
        val_res = f[f["wk"].astype(float) <= float(sel_wk)].sort_values("updated_at", ascending=False)
        narr_res = f[f["wk"] == sel_wk].sort_values("updated_at", ascending=False)

    effective_val = float(val_res.iloc[0].get("new_value", 0)) if not val_res.empty else 0.0
    latest_narrative = narr_res.iloc[0] if not narr_res.empty else None
    
    return effective_val, latest_narrative


# ---------------------------------------------------------------------------
# Main Component
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, updates_df, is_primary: bool = False) -> None:
    obj_id, obj_title = str(obj_row["id"]), obj_row["title"]
    sub_team = obj_row.get("sub_team", "")
    selected_week = st.session_state.get("selected_week", 1)
    active_kr = st.session_state.get("updating_kr") or ""

    # Logic: Filter KRs and compute historical/average progress
    obj_krs = krs_df[krs_df["objective_id"].astype(str) == obj_id] if not krs_df.empty else pd.DataFrame()
    effective_data = []
    
    for _, kr in obj_krs.iterrows():
        val, latest = _get_hist_val(updates_df, str(kr["id"]), selected_week)
        calc_kr = kr.copy(); calc_kr["current_value"] = val
        pct = compute_progress(calc_kr)
        effective_data.append({"kr": kr, "pct": pct, "val": val, "latest": latest})

    if effective_data:
        avg_pct = sum(d["pct"] for d in effective_data) / len(effective_data)
        achieved = sum(1 for d in effective_data if d["pct"] >= 100)
        total = len(effective_data)
    else:
        avg_pct = 0.0; achieved = total = 0

    with st.container():
        # Header Info
        st.markdown(f'<div style="font-size:12px; font-weight:700; color:{PURPLE}; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">{sub_team} · WEEK {selected_week}</div>', unsafe_allow_html=True)
        
        c_title, c_opts = st.columns([5, 0.5])
        with c_title:
            st.markdown(f'<div style="font-size:20px; font-weight:700; color:#fff; line-height:1.3; margin-bottom:12px;">{obj_title}</div>', unsafe_allow_html=True)
        with c_opts:
            if st.button(" ", icon=":material/more_horiz:", key=f"opt_{obj_id}", type="tertiary"):
                _obj_actions_dialog(obj_id, obj_title)

        # Progress
        st.markdown(f'<div style="font-size:32px; font-weight:800; color:#fff; line-height:1;">{avg_pct:.0f}%</div>', unsafe_allow_html=True)
        st.markdown(_obj_progress_bar(avg_pct), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:13px; color:{MUTED}; margin-bottom:24px;">{achieved} / {total} KRs achieved</div>', unsafe_allow_html=True)

        if effective_data:
            for data in effective_data:
                _render_kr_row(data, active_kr)
        else:
            st.markdown(f'<div style="color:{MUTED}; padding:12px 0;">No key results tracked.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR Row
# ---------------------------------------------------------------------------

def _render_kr_row(data, active_kr: str) -> None:
    kr, pct, val, latest = data["kr"], data["pct"], data["val"], data["latest"]
    kr_id, title = str(kr["id"]), kr["title"]
    target, unit = float(kr.get("target", 0)), str(kr.get("unit", ""))

    with st.container():
        st.markdown('<div style="padding: 12px 0; border-top: 1px solid rgba(255,255,255,0.05); margin-top:8px;">', unsafe_allow_html=True)
        
        c_main, c_pct, c_act = st.columns([3.5, 0.8, 0.7])
        with c_main:
            st.markdown(f'<div style="font-size:15px; font-weight:600; color:#fff;">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:13px; color:{MUTED};">{_format_current_target(val, target, unit)}</div>', unsafe_allow_html=True)
        
        with c_pct:
            st.markdown(f'<div style="text-align:right; font-size:18px; font-weight:700; color:{_pct_color(pct)};">{pct:.0f}%</div>', unsafe_allow_html=True)
        
        with c_act:
            if st.button("Update", key=f"ukr_{kr_id}", type="secondary", use_container_width=True):
                st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
                st.rerun()

        # Update inline (Readability 15px)
        if latest is not None:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:10px; margin-top:8px;">
                <span style="font-size:13px; font-weight:700; color:{GREEN}; opacity:0.9;">{_format_badge(val, unit)}</span>
                <span style="font-size:15px; color:rgba(255,255,255,0.8); line-height:1.4;">{latest.get('week_notes', '')}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(_kr_progress_bar(pct), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if active_kr == kr_id: _render_update_form(kr)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_update_form(kr):
    kr_id = str(kr["id"])
    st.markdown('<div style="background:rgba(255,255,255,0.03); padding:16px; border-radius:8px; border:1px solid rgba(255,255,255,0.08); margin:8px 0;">', unsafe_allow_html=True)
    with st.form(key=f"f_{kr_id}"):
        val = st.number_input("Value", value=float(kr.get("current_value", 0)))
        notes = st.text_input("Notes")
        if st.form_submit_button("Save", use_container_width=True):
            try:
                selected_week = st.session_state.get("selected_week", 1)
                update_kr_value(
                    kr_id, val, notes, "", 3, 
                    st.session_state.get("user",{}).get("email","?"),
                    selected_week
                )
                st.session_state["updating_kr"] = None; st.rerun()
            except Exception as e: handle_error(e, "Save failed", "Update")
    st.markdown("</div>", unsafe_allow_html=True)

@st.dialog("Objective Actions")
def _obj_actions_dialog(id, title):
    st.write(f"Objective: **{title}**")
    if st.button("Edit Title"): _edit_obj_dialog(id, title)
    if st.button("Add Key Result"): add_kr_dialog(id)
    if st.button("Delete Objective"): delete_objective(id); st.rerun()

@st.dialog("Edit Title")
def _edit_obj_dialog(id, title):
    nt = st.text_input("Title", value=title)
    if st.button("Save"): update_objective(id, nt); st.rerun()

@st.dialog("Add KR")
def add_kr_dialog(id):
    t = st.text_input("Title")
    tgt = st.number_input("Target", value=100.0)
    unt = st.text_input("Unit", value="%")
    if st.button("Create"): create_kr(id, t, tgt, unt); st.rerun()
