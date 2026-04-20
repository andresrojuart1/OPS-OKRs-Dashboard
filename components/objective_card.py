"""Objective card — Executive OKR layout with Master Hierarchical Structure.

Hierarchy: Sub-team → Objective (Master Card) → Key Results (Sub-cards) → Updates
Designed for boardroom presentations: 15px narratives, distinct grouping.
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
    if pct >= 70: return GREEN
    if pct >= 40: return YELLOW
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
    except (ValueError, TypeError): return str(value)
    u = unit.lower().strip()
    if u == "%": return f"{v:+.2f}%" if v != 0 else f"{v:.2f}%"
    if u in ("$", "$/month"):
        if v >= 1_000_000: return f"${v / 1_000_000:.1f}M"
        if v >= 1_000: return f"${v / 1_000:.0f}K"
        return f"${v:,.0f}"
    return f"{v:g} {unit}"


def _format_current_target(current: float, target: float, unit: str) -> str:
    u = unit.lower().strip()
    if u == "binary": return "Done ✓" if current >= 1 else "Status: Pending"
    if u in ("$", "$/month"):
        def fmt(v):
            if v >= 1_000_000: return f"${v / 1_000_000:.1f}M"
            if v >= 1_000: return f"${v / 1_000:.0f}K"
            return f"${v:,.0f}"
        return f"{fmt(current)} / {fmt(target)}"
    if u == "%": return f"{current:.2f}% / {target:.0f}%"
    return f"{current:g} / {target:g} {unit}"


def _get_historical_data(updates_df, kr_id: str, target_week: int):
    if updates_df.empty: return 0.0, None
    v_upds = updates_df[updates_df["kr_id"].astype(str) == kr_id].copy()
    v_upds["wk"] = v_upds["updated_at"].apply(_get_week_from_ts)
    up_to_week = v_upds[v_upds["wk"] <= target_week].sort_values("updated_at", ascending=False)
    if not up_to_week.empty:
        return float(up_to_week.iloc[0].get("new_value", 0)), up_to_week.iloc[0]
    return 0.0, None


# ---------------------------------------------------------------------------
# Main Component
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, updates_df, is_primary: bool = False) -> None:
    obj_id, obj_title = str(obj_row["id"]), obj_row["title"]
    sub_team = obj_row.get("sub_team", "General")
    selected_week = st.session_state.get("selected_week", 1)
    active_kr = st.session_state.get("updating_kr") or ""

    # Filter and Compute
    obj_krs = krs_df[krs_df["objective_id"].astype(str) == obj_id] if not krs_df.empty else pd.DataFrame()
    effective_krs = []
    prev_pcts = []
    
    for _, kr in obj_krs.iterrows():
        val, latest = _get_historical_data(updates_df, str(kr["id"]), selected_week)
        val_prev, _ = _get_historical_data(updates_df, str(kr["id"]), selected_week - 1)
        
        calc_kr = kr.copy(); calc_kr["current_value"] = val
        calc_kr_p = kr.copy(); calc_kr_p["current_value"] = val_prev
        
        pct = compute_progress(calc_kr)
        effective_krs.append({"kr": kr, "pct": pct, "val": val, "latest": latest})
        prev_pcts.append(compute_progress(calc_kr_p))

    if effective_krs:
        avg_pct = sum(d["pct"] for d in effective_krs) / len(effective_krs)
        prev_avg = sum(prev_pcts) / len(prev_pcts)
        total_krs, achieved = len(effective_krs), sum(1 for d in effective_krs if d["pct"] >= 100)
        diff = avg_pct - prev_avg
        trend_label = f"↑ {diff:.1f}% this week" if diff > 0 else (f"↓ {abs(diff):.1f}% this week" if diff < 0 else "Stable")
        trend_txt = GREEN if diff > 0 else (RED if diff < 0 else MUTED)
    else:
        avg_pct = 0.0; total_krs = achieved = 0; trend_label = "No Data"; trend_txt = MUTED

    with st.container():
        st.markdown('<div class="okr-card-trigger" style="display:none;"></div>', unsafe_allow_html=True)

        # ── HEADER: Label + Week ──
        st.markdown(
            f'<div style="font-size:11px; font-weight:800; color:{PURPLE}; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">'
            f'{sub_team} <span style="opacity:0.3; margin:0 6px;">|</span> WEEK {selected_week}</div>',
            unsafe_allow_html=True
        )

        # ── OBJECTIVE INFO ──
        c_title, c_actions = st.columns([5, 1])
        with c_title:
            st.markdown(f'<div style="font-size:22px; font-weight:700; color:#fff; line-height:1.3; margin-bottom:16px;">{obj_title}</div>', unsafe_allow_html=True)
        with c_actions:
            if st.button(" ", icon=":material/more_horiz:", key=f"more_{obj_id}", type="secondary"):
                _obj_actions_dialog(obj_id, obj_title)

        # ── PROGRESS ──
        st.markdown(
            f"""<div style="display:flex; align-items:baseline; gap:12px; margin-bottom:6px;">
<span style="font-size:36px; font-weight:800; color:#fff; letter-spacing:-1px;">{avg_pct:.0f}%</span>
<span style="font-size:11px; font-weight:700; color:{trend_txt}; text-transform:uppercase; letter-spacing:0.04em;">{trend_label}</span>
</div>""",
            unsafe_allow_html=True
        )
        st.markdown(_obj_progress_bar(avg_pct), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:13px; color:{MUTED}; margin-bottom:24px;">{achieved} / {total_krs} KRs achieved</div>', unsafe_allow_html=True)

        # ── KEY RESULTS SECTION ──
        st.markdown('<div style="font-size:14px; font-weight:700; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.08em; padding-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:16px;">Key Results</div>', unsafe_allow_html=True)

        if effective_krs:
            for data in effective_krs:
                _render_kr_subcard(data, active_kr)
        else:
            st.markdown(f'<div style="color:{MUTED}; text-align:center; padding:12px;">Add KRs to track progress</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# KR Sub-card
# ---------------------------------------------------------------------------

def _render_kr_subcard(data, active_kr: str) -> None:
    kr, pct, val, latest = data["kr"], data["pct"], data["val"], data["latest"]
    kr_id, title = str(kr["id"]), kr["title"]
    target, unit = float(kr.get("target", 0)), str(kr.get("unit", ""))
    
    with st.container():
        st.markdown('<div class="kr-block-trigger" style="display:none;"></div>', unsafe_allow_html=True)
        
        # ── TOP: Info vs Achievement ──
        c_info, c_ach = st.columns([4, 1.5])
        with c_info:
            st.markdown(f'<div style="font-size:16px; font-weight:600; color:#fff; margin-bottom:2px;">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:13px; font-weight:600; color:rgba(255,255,255,0.4);">{_format_current_target(val, target, unit)}</div>', unsafe_allow_html=True)
        with c_ach:
            st.markdown(f'<div style="text-align:right; font-size:24px; font-weight:800; color:{_pct_color(pct)}; line-height:1;">{pct:.0f}%</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:right; font-size:9px; font-weight:800; color:rgba(255,255,255,0.25); text-transform:uppercase; letter-spacing:0.05em; margin-top:2px;">Achievement</div>', unsafe_allow_html=True)

        # ── MIDDLE: Latest Update Row ──
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        if latest is not None:
            upd_val = float(latest.get("new_value", 0))
            diff_val = upd_val - float(latest.get("old_value", 0)) if "old_value" in latest else 0
            badge_color = GREEN if pct >= 100 else (YELLOW if pct > 0 else MUTED)
            
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; padding:10px 0; border-top:1px solid rgba(255,255,255,0.03);">
                <div style="background:{badge_color}15; color:{badge_color}; border-radius:6px; padding:3px 8px; font-size:14px; font-weight:700;">{_format_badge(upd_val, unit)}</div>
                <div style="flex:1; font-size:15px; color:rgba(255,255,255,0.8); line-height:1.4;">{latest.get('week_notes', '')}</div>
                <div style="font-size:12px; color:rgba(255,255,255,0.2);">Week {latest.get('wk', '?')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:14px; color:rgba(255,255,255,0.2); font-style:italic; padding:6px 0;">No updates recorded for this KR</div>', unsafe_allow_html=True)

        # ── BOTTOM: Primary Action ──
        c_sp, c_btn = st.columns([4, 1.5])
        with c_btn:
            if st.button("Update", key=f"upd_{kr_id}", type="primary", use_container_width=True):
                st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
                st.rerun()
        with c_sp:
            st.markdown(_kr_progress_bar(pct), unsafe_allow_html=True)

    if active_kr == kr_id: _render_update_form(kr)


def _render_update_form(kr):
    kr_id = str(kr["id"])
    st.markdown('<div style="background:rgba(122,80,247,0.05); padding:16px; border-radius:12px; border:1px solid rgba(122,80,247,0.2); margin-top:8px;">', unsafe_allow_html=True)
    with st.form(key=f"frm_{kr_id}"):
        c1, c2 = st.columns(2)
        with c1: val = st.number_input("Current Value", value=float(kr.get("current_value", 0)))
        with c2: conf = st.slider("Confidence", 1, 5, 3)
        notes = st.text_input("Narrative Update (What happened?)", placeholder="Ex: Closed partnerships with 3 vendors...")
        blockers = st.text_input("Blockers / Risks", placeholder="None")
        if st.form_submit_button("Submit Weekly Update", use_container_width=True):
            try:
                update_kr_value(kr_id, val, notes, blockers, conf, st.session_state.get("user", {}).get("email", "?"))
                track_action("Updated KR", detail=kr_id); st.session_state["updating_kr"] = None; st.rerun()
            except Exception as e: handle_error(e, "Save failed", "KR Update")
    st.markdown("</div>", unsafe_allow_html=True)


@st.dialog("Objective Actions")
def _obj_actions_dialog(obj_id, title):
    st.write(f"Editing: **{title}**")
    if st.button("Edit Objective Title", use_container_width=True): _edit_obj_dialog(obj_id, title)
    if st.button("Add Key Result", use_container_width=True, type="primary"): add_kr_dialog(obj_id, title)
    st.divider()
    if st.button("Delete Objective", type="secondary", use_container_width=True): _confirm_delete_obj_dialog(obj_id, title)

@st.dialog("Edit Title")
def _edit_obj_dialog(id, title):
    nt = st.text_input("New Title", value=title)
    if st.button("Save"): update_objective(id, nt); st.rerun()

@st.dialog("Delete Objective")
def _confirm_delete_obj_dialog(id, title):
    st.error(f"Delete objective and all its KRs?")
    if st.button("Yes, Delete"): delete_objective(id); st.rerun()

@st.dialog("Add Key Result")
def add_kr_dialog(obj_id, obj_title):
    t = st.text_input("KR Title")
    c1, c2 = st.columns(2)
    with c1: tgt = st.number_input("Target", value=100.0)
    with c2: unt = st.text_input("Unit", value="%")
    if st.button("Create KR", type="primary"): create_kr(obj_id, t, tgt, unt); st.rerun()
