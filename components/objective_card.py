"""Objective card — Executive OKR layout.

Refined specifically for:
- Meeting readability (15px update text)
- KR layout (Left: Info, Right: Metric/Action)
- Accurate objective progress (Average of KRs)
- Grouping & Visual Connection
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
    if pct >= 100: return GREEN
    if pct >= 70: return GREEN
    if pct >= 40: return YELLOW
    return RED


def _get_week_from_ts(ts_str: str) -> int:
    try:
        dt = datetime.strptime(str(ts_str).strip(), "%Y-%m-%d %H:%M UTC")
        return dt.isocalendar()[1]
    except: return 0


def _obj_progress_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.08); border-radius:999px; height:10px; overflow:hidden; margin:8px 0;">
<div style="height:100%; width:{max(pct, 0.5):.1f}%; border-radius:999px; background:linear-gradient(90deg, {PURPLE}, {GREEN}); transition: width 0.6s ease;"></div>
</div>"""


def _kr_progress_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.04); border-radius:999px; height:6px; overflow:hidden; margin:12px 0 0;">
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
    f = updates_df[updates_df["kr_id"].astype(str) == kr_id].copy()
    f["wk"] = f["updated_at"].apply(_get_week_from_ts)
    res = f[f["wk"] <= week].sort_values("updated_at", ascending=False)
    if not res.empty: return float(res.iloc[0].get("new_value", 0)), res.iloc[0]
    return 0.0, None


# ---------------------------------------------------------------------------
# Main Component
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, updates_df, is_primary: bool = False) -> None:
    obj_id, obj_title = str(obj_row["id"]), obj_row["title"]
    sub_team = obj_row.get("sub_team", "")
    selected_week = st.session_state.get("selected_week", 1)
    active_kr = st.session_state.get("updating_kr") or ""

    # 1. Filter KRs and compute historical/average progress
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
        # --- HEADER ---
        st.markdown(f'<div style="font-size:12px; font-weight:800; color:{PURPLE}; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">{sub_team} · WEEK {selected_week}</div>', unsafe_allow_html=True)
        
        c_title, c_opts = st.columns([5, 0.5])
        with c_title:
            st.markdown(f'<div style="font-size:24px; font-weight:700; color:#fff; line-height:1.25; margin-bottom:12px;">{obj_title}</div>', unsafe_allow_html=True)
        with c_opts:
            if st.button(" ", icon=":material/edit:", key=f"e_{obj_id}", type="tertiary"):
                _edit_obj_dialog(obj_id, obj_title)

        # --- OBJECTIVE PROGRESS (FIXED CALCULATION) ---
        st.markdown(f'<div style="font-size:42px; font-weight:800; color:#fff; line-height:1;">{avg_pct:.0f}%</div>', unsafe_allow_html=True)
        st.markdown(_obj_progress_bar(avg_pct), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:14px; color:{MUTED}; margin-bottom:32px;">{achieved} / {total} KRs achieved</div>', unsafe_allow_html=True)

        # --- SUBTLE DIVIDER & SPACING (Improve Visual Connection) ---
        st.markdown('<div style="font-size:14px; font-weight:700; color:rgba(255,255,255,0.3); text-transform:uppercase; letter-spacing:0.1em; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:20px;">Key Results</div>', unsafe_allow_html=True)

        if effective_data:
            for data in effective_data:
                _render_kr_unit(data, active_kr)
        else:
            st.markdown(f'<div style="padding:16px; text-align:center; color:{MUTED};">No key results found.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR Unit
# ---------------------------------------------------------------------------

def _render_kr_unit(data, active_kr: str) -> None:
    kr, pct, val, latest = data["kr"], data["pct"], data["val"], data["latest"]
    kr_id, title = str(kr["id"]), kr["title"]
    target, unit = float(kr.get("target", 0)), str(kr.get("unit", ""))

    with st.container():
        # Visual grouping indentation feel
        st.markdown('<div style="padding-left:4px; margin-bottom:24px;">', unsafe_allow_html=True)
        
        # --- TOP ROW (LEFT: Info, RIGHT: Action/Metric) ---
        c_left, c_right = st.columns([3.5, 1.5])
        with c_left:
            st.markdown(f'<div style="font-size:17px; font-weight:600; color:#fff; margin-bottom:2px;">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:13px; color:rgba(255,255,255,0.5); font-weight:500;">{_format_current_target(val, target, unit)}</div>', unsafe_allow_html=True)
        
        with c_right:
            st.markdown(f'<div style="text-align:right; font-size:26px; font-weight:800; color:{_pct_color(pct)}; line-height:1; margin-bottom:6px;">{pct:.0f}%</div>', unsafe_allow_html=True)
            if st.button("Update", key=f"btn_{kr_id}", type="primary", use_container_width=True):
                st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
                st.rerun()

        # --- LATEST UPDATE ROW (High Visibility 15px) ---
        if latest is not None:
            badge_color = _pct_color(pct)
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; margin-top:14px; background:rgba(255,255,255,0.02); padding:12px; border-radius:8px; border-left:3px solid {badge_color};">
                <div style="background:{badge_color}1a; color:{badge_color}; padding:4px 10px; border-radius:6px; font-size:15px; font-weight:700;">{_format_badge(val, unit)}</div>
                <div style="flex:1; font-size:15px; color:rgba(255,255,255,0.85); line-height:1.4;">{latest.get('week_notes', '')}</div>
                <div style="font-size:12px; color:rgba(255,255,255,0.25); white-space:nowrap;">W{latest.get('wk','?')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:14px; color:{MUTED}; font-style:italic; margin-top:12px;">No updates recorded for this week.</div>', unsafe_allow_html=True)

        st.markdown(_kr_progress_bar(pct), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if active_kr == kr_id: _render_update_form(kr)


# ---------------------------------------------------------------------------
# Update Form
# ---------------------------------------------------------------------------

def _render_update_form(kr):
    kr_id = str(kr["id"])
    st.markdown('<div style="background:rgba(122,80,247,0.05); padding:20px; border-radius:12px; border:1px solid rgba(122,80,247,0.2); margin:12px 0;">', unsafe_allow_html=True)
    with st.form(key=f"frm_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: val = st.number_input("New Value", value=float(kr.get("current_value", 0)))
        with c2: conf = st.slider("Confidence", 1, 5, 3)
        notes = st.text_input("Narrative (What happened this week?)")
        if st.form_submit_button("Submit Update", use_container_width=True):
            try:
                update_kr_value(kr_id, val, notes, "", conf, st.session_state.get("user",{}).get("email","?"))
                track_action("Update KR", detail=kr_id); st.session_state["updating_kr"] = None; st.rerun()
            except Exception as e: handle_error(e, "Save failed", "Update")
    st.markdown("</div>", unsafe_allow_html=True)


@st.dialog("Edit Objective")
def _edit_obj_dialog(id, title):
    nt = st.text_input("Title", value=title)
    if st.button("Save"):
        update_objective(id, nt); st.rerun()

@st.dialog("New KR")
def add_kr_dialog(obj_id):
    t = st.text_input("Title")
    tgt = st.number_input("Target", value=100.0)
    unt = st.text_input("Unit", value="%")
    if st.button("Create"):
        create_kr(obj_id, t, tgt, unt); st.rerun()
