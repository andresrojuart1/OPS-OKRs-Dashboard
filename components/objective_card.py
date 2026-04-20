"""Objective card — Executive Boardroom Layout.

Hierarchy: Sub-team → Objective → Key Results
Logic: Accurate historical progress (Average of KRs) & Time-Travel navigation.
Design Focus:
- 15px update narrative (Critical readability)
- Left-Right KR layout
- Distinct value badges
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
# Visual tokens
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
    return f"""<div style="background:rgba(255,255,255,0.08); border-radius:999px; height:8px; overflow:hidden; margin:10px 0;">
<div style="height:100%; width:{max(pct, 0.5):.1f}%; border-radius:999px; background:linear-gradient(90deg, {PURPLE}, {GREEN}); transition: width 0.6s ease;"></div>
</div>"""


def _kr_progress_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.04); border-radius:999px; height:5px; overflow:hidden; margin:12px 0 0;">
<div style="height:100%; width:{max(pct, 0.5):.1f}%; border-radius:999px; background:{PURPLE}; transition: width 0.6s ease;"></div>
</div>"""


def _format_badge(value, unit: str, fmt_override: str = None) -> str:
    try: v = float(value)
    except: return str(value)
    
    u = unit.lower().strip()
    f = str(fmt_override).lower().strip() if fmt_override else "number"
    
    if f == "percentage" or u == "%":
        # Note: input is usually 50 for 50%, we might multiply by 100 if raw decimal, 
        # but here UI already treats current_value as raw comparison to target.
        return f"{v:+.2f}%" if v != 0 else f"{v:.2f}%"
    
    if f == "currency" or u in ("$", "$/month"):
        if abs(v) >= 1_000_000: return f"${v / 1_000_000:.1f}M"
        if abs(v) >= 1_000: return f"${v / 1_000:.0f}K"
        return f"${v:,.2f}" if f == "currency" else f"${v:,.0f}"
        
    return f"{v:g} {unit}"


def _format_current_target(current: float, target: float, unit: str) -> str:
    u = unit.lower().strip()
    if u == "binary": return "Done ✓" if current >= 1 else "Pending"
    if u in ("$", "$/month"):
        def fmt(v):
            if v >= 1_000_000: return f"${v / 1_000_000:.1f}M"
            if v >= 1_000: return f"${v / 1_000:.0f}K"
            return f"${v:,.0f}"
        return f"{fmt(current)} / {fmt(target)}"
    return f"{current:g} / {target:g} {unit}"


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

    if not is_primary:
        st.markdown('<div style="margin-top: 72px; padding-top: 48px; border-top: 1px solid rgba(255,255,255,0.1); margin-bottom: 24px;"></div>', unsafe_allow_html=True)

    with st.container():
        # Label & Header (Visual Hierarchy 14px)
        st.markdown(f'<div style="font-size:14px; font-weight:800; color:{PURPLE}; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:10px;">{sub_team} · WEEK {selected_week}</div>', unsafe_allow_html=True)
        
        c_title, c_opts = st.columns([5, 0.5])
        with c_title:
            st.markdown(f'<div style="font-size:22px; font-weight:700; color:#fff; line-height:1.3; margin-bottom:12px;">{obj_title}</div>', unsafe_allow_html=True)
        with c_opts:
            if st.button(" ", icon=":material/more_horiz:", key=f"opt_{obj_id}", type="tertiary"):
                _obj_actions_dialog(obj_id, obj_title)

        # Objective Progress Summary
        st.markdown(f'<div style="font-size:38px; font-weight:800; color:#fff; line-height:1;">{avg_pct:.0f}%</div>', unsafe_allow_html=True)
        st.markdown(_obj_progress_bar(avg_pct), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:13px; color:{MUTED}; margin-bottom:28px; font-weight:600;">{achieved} / {total} KRs achieved</div>', unsafe_allow_html=True)

        # Divider Section
        st.markdown('<div style="font-size:13px; font-weight:700; color:rgba(255,255,255,0.25); text-transform:uppercase; letter-spacing:0.1em; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:16px;">Key Results Tracking</div>', unsafe_allow_html=True)

        if effective_data:
            for data in effective_data:
                _render_kr_block(data, active_kr)
        else:
            st.markdown(f'<div style="padding:16px; text-align:center; color:{MUTED}; font-size:14px;">No key results found.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR Render
# ---------------------------------------------------------------------------

def _render_kr_block(data, active_kr: str) -> None:
    kr, pct, val, latest = data["kr"], data["pct"], data["val"], data["latest"]
    kr_id, title = str(kr["id"]), kr["title"]
    target, unit = float(kr.get("target", 0)), str(kr.get("unit", ""))

    with st.container():
        st.markdown('<div style="margin-bottom:24px;">', unsafe_allow_html=True)
        
        # --- PRIMARY INFO (LEFT) vs ACTION/METRIC (RIGHT) ---
        c_left, c_right = st.columns([3.5, 1.5])
        with c_left:
            st.markdown(f'<div style="font-size:16px; font-weight:600; color:#fff; margin-bottom:2px;">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:13px; color:rgba(255,255,255,0.45); font-weight:500;">{_format_current_target(val, target, unit)}</div>', unsafe_allow_html=True)
        
        with c_right:
            st.markdown(f'<div style="text-align:right; font-size:24px; font-weight:800; color:{_pct_color(pct)}; line-height:1; margin-bottom:6px;">{pct:.0f}%</div>', unsafe_allow_html=True)
            u_label = "Cancel" if active_kr == kr_id else "Update"
            if st.button(u_label, key=f"upd_{kr_id}", type="secondary", use_container_width=True):
                st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
                st.rerun()

        # --- NARRATIVE ROW (15px Visibility) ---
        if latest is not None:
            badge_color = _pct_color(pct)
            fmt_override = latest.get("value_format", "number")
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; margin-top:14px; background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; border-left:4px solid {badge_color};">
                <div style="background:{badge_color}1a; color:{badge_color}; padding:4px 10px; border-radius:6px; font-size:15px; font-weight:700; white-space:nowrap;">{_format_badge(val, unit, fmt_override)}</div>
                <div style="flex:1; font-size:15px; color:rgba(255,255,255,0.8); line-height:1.4;">{latest.get('week_notes', '')}</div>
                <div style="font-size:12px; color:rgba(255,255,255,0.2); white-space:nowrap;">W{latest.get('wk','?')}</div>
            </div>
            """, unsafe_allow_html=True)
            # Show dependencies if any
            deps = latest.get("blockers", "")
            if deps:
                st.markdown(f'<div style="padding-left:12px; margin-top:4px; font-size:13px; color:#f87171; font-weight:500;">⚠ Dependencies: {deps}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:14px; color:{MUTED}; font-style:italic; margin-top:10px; opacity:0.6;">No updates recorded for this week.</div>', unsafe_allow_html=True)

        st.markdown(_kr_progress_bar(pct), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if active_kr == kr_id: _render_update_form(kr)


# ---------------------------------------------------------------------------
# Update Form
# ---------------------------------------------------------------------------

def _render_update_form(kr):
    kr_id = str(kr["id"])
    st.markdown('<div style="background:rgba(122,80,247,0.05); padding:16px; border-radius:12px; border:1px solid rgba(122,80,247,0.2); margin:12px 0;">', unsafe_allow_html=True)
    with st.form(key=f"frm_{kr_id}"):
        c1, c2 = st.columns([1, 1])
        with c1:
            val = st.number_input("Numerical Value", value=float(kr.get("current_value", 0)))
        with c2:
            v_fmt = st.selectbox("Value format", ["number", "percentage", "currency"])
            
        notes = st.text_input("Narrative (Notes)")
        deps = st.text_input("Dependencies / Blockers")
        
        if st.form_submit_button("Save Update", use_container_width=True):
            try:
                selected_week = st.session_state.get("selected_week", 1)
                update_kr_value(
                    kr_id, val, notes, deps, 3, 
                    st.session_state.get("user",{}).get("email","?"),
                    selected_week,
                    v_fmt
                )
                st.session_state["updating_kr"] = None; st.rerun()
            except Exception as e: handle_error(e, "Save failed", "Update")
    st.markdown("</div>", unsafe_allow_html=True)

@st.dialog("Objective Actions")
def _obj_actions_dialog(id, title):
    st.write(f"Objective: **{title}**")
    if st.button("Edit Title"): _edit_obj_dialog(id, title)
    if st.button("Add Key Result"): add_kr_dialog(id)
    st.divider()
    if st.button("Delete Objective", type="secondary"): delete_objective(id); st.rerun()

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
