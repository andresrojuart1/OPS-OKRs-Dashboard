"""Objective card — Executive OKR layout with Time-Travel & Dynamic Trends.

Hierarchy: Sub-team → Objective → Key Results → Weekly Updates
Designed for leadership meetings: high contrast, readable, scannable.
Supports global week selection with historical progress & trend analysis.
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
    if pct >= 70:
        return GREEN
    if pct >= 40:
        return YELLOW
    return RED


# ---------------------------------------------------------------------------
# Visual helpers
# ---------------------------------------------------------------------------

def _get_week_from_ts(ts_str: str) -> int:
    """Helper to derive ISO week from 'YYYY-MM-DD HH:MM UTC' string."""
    try:
        dt = datetime.strptime(str(ts_str).strip(), "%Y-%m-%d %H:%M UTC")
        return dt.isocalendar()[1]
    except:
        return 0


def _obj_progress_bar(pct: float) -> str:
    """Full-width progress bar for objective level."""
    return f"""<div style="background:rgba(255,255,255,0.06); border-radius:999px; height:8px;
    overflow:hidden; margin:8px 0 4px;">
<div style="height:100%; width:{max(pct, 0.5):.1f}%; border-radius:999px;
    background:linear-gradient(90deg, {PURPLE}, {GREEN});
    transition: width 0.6s ease;"></div>
</div>"""


def _kr_progress_bar(pct: float) -> str:
    """Thinner progress bar for KR level."""
    return f"""<div style="background:rgba(255,255,255,0.04); border-radius:999px; height:5px;
    overflow:hidden; margin:10px 0 0;">
<div style="height:100%; width:{max(pct, 0.5):.1f}%; border-radius:999px;
    background:{PURPLE}; box-shadow:0 0 8px {PURPLE}44;
    transition: width 0.6s ease;"></div>
</div>"""


def _relative_time(ts_str: str) -> str:
    """Convert 'YYYY-MM-DD HH:MM UTC' to a relative timestamp or week label."""
    try:
        dt = datetime.strptime(str(ts_str).strip(), "%Y-%m-%d %H:%M UTC")
        dt = dt.replace(tzinfo=timezone.utc)
        diff = datetime.now(timezone.utc) - dt
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            return "just now"
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 7:
            return f"{days}d ago"
        return f"Week {dt.isocalendar()[1]}"
    except Exception:
        return str(ts_str) if ts_str else ""


def _format_badge(value, unit: str) -> str:
    """Format a value for display as a change badge."""
    try:
        v = float(value)
    except (ValueError, TypeError):
        return str(value)
    u = unit.lower().strip()
    if u == "%":
        return f"{v:.2f}%"
    if u in ("$", "$/month"):
        if v >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        if v >= 1_000:
            return f"${v / 1_000:.0f}K"
        return f"${v:,.0f}"
    if u == "binary":
        return "Done ✓" if v >= 1 else "Pending"
    return f"{v:g} {unit}"


def _format_current_target(current: float, target: float, unit: str) -> str:
    """Full 'Current: X / Target: Y' label."""
    u = unit.lower().strip()
    if u == "binary":
        return "Done ✓" if current >= 1 else "Status: Pending"
    if u in ("$", "$/month"):
        def fmt(v):
            if v >= 1_000_000:
                return f"${v / 1_000_000:.1f}M"
            if v >= 1_000:
                return f"${v / 1_000:.0f}K"
            return f"${v:,.0f}"
        return f"Current: {fmt(current)} / Target: {fmt(target)}"
    if u == "%":
        return f"Current: {current:.2f}% / Target: {target:.0f}%"
    return f"Current: {current:g} / Target: {target:g} {unit}"


def _get_historical_val(updates_df, kr_id: str, target_week: int):
    """Derive effective value and latest update for a target week."""
    if updates_df.empty: return 0.0, None
    
    valid_upds = updates_df[updates_df["kr_id"].astype(str) == kr_id].copy()
    valid_upds["wk"] = valid_upds["updated_at"].apply(_get_week_from_ts)
    up_to_week = valid_upds[valid_upds["wk"] <= target_week].sort_values("updated_at", ascending=False)
    
    if not up_to_week.empty:
        return float(up_to_week.iloc[0].get("new_value", 0)), up_to_week.iloc[0]
    return 0.0, None


# ---------------------------------------------------------------------------
# Main component
# ---------------------------------------------------------------------------

def render_objective_card(
    obj_row, krs_df, updates_df, is_primary: bool = False
) -> None:
    obj_id = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team = obj_row.get("sub_team", "")
    active_kr = st.session_state.get("updating_kr") or ""
    selected_week = st.session_state.get("selected_week", 1)

    # Filter KRs
    if not krs_df.empty:
        obj_krs = krs_df[krs_df["objective_id"].astype(str) == obj_id]
    else:
        obj_krs = krs_df

    # --- Trend & Progress Logic ---
    effective_krs_data = []
    prev_week_pcts = []
    
    if not obj_krs.empty:
        for _, kr in obj_krs.iterrows():
            kr_id = str(kr["id"])
            
            # Val as of Selected Week
            val, latest = _get_historical_val(updates_df, kr_id, selected_week)
            # Val as of Selected Week - 1 (for Trend)
            v_prev, _ = _get_historical_val(updates_df, kr_id, selected_week - 1)
            
            # Pct now
            calc_kr = kr.copy()
            calc_kr["current_value"] = val
            pct = compute_progress(calc_kr)
            
            # Pct prev
            calc_kr_prev = kr.copy()
            calc_kr_prev["current_value"] = v_prev
            pct_prev = compute_progress(calc_kr_prev)
            
            effective_krs_data.append({
                "kr": kr, "pct": pct, "val": val, "latest": latest,
                "updates": updates_df[updates_df["kr_id"].astype(str) == kr_id] if not updates_df.empty else pd.DataFrame()
            })
            prev_week_pcts.append(pct_prev)

    if effective_krs_data:
        avg_pct = sum(d["pct"] for d in effective_krs_data) / len(effective_krs_data)
        prev_avg_pct = sum(prev_week_pcts) / len(prev_week_pcts)
        total_krs = len(effective_krs_data)
        active_krs = sum(1 for d in effective_krs_data if d["pct"] > 0)
        
        # Trend Badge
        diff = avg_pct - prev_avg_pct
        if diff > 0:
            trend_label = f"↑ {diff:.0f}% Week"
            trend_bg = f"{GREEN}15"
            trend_txt = GREEN
        elif diff < 0:
            trend_label = f"↓ {abs(diff):.0f}% Week"
            trend_bg = f"{RED}15"
            trend_txt = RED
        else:
            trend_label = "Stable"
            trend_bg = "rgba(255,255,255,0.06)"
            trend_txt = MUTED
    else:
        avg_pct = 0.0
        total_krs = 0
        active_krs = 0
        trend_label = "No Data"
        trend_bg = "transparent"
        trend_txt = MUTED

    with st.container():
        st.markdown('<div class="okr-card-trigger" style="display:none;"></div>', unsafe_allow_html=True)

        # ── HEADER ──
        c_label, _, c_add, c_edit, c_del = st.columns([3, 2.5, 1.2, 0.5, 0.5])
        with c_label:
            st.markdown(
                f'<div style="font-size:12px; font-weight:700; color:{PURPLE}; '
                f'text-transform:uppercase; letter-spacing:0.1em; padding-top:4px;">'
                f'{sub_team} <span style="opacity:0.4; margin:0 8px;">·</span> '
                f'<span style="color:#fff; opacity:0.6;">Week {selected_week}</span></div>',
                unsafe_allow_html=True,
            )
        with c_add:
            if st.button("Add KR", icon=":material/add:", key=f"akr_{obj_id}", type="secondary", use_container_width=True):
                add_kr_dialog(obj_id, obj_title)
        with c_edit:
            if st.button(" ", icon=":material/edit:", key=f"eobj_{obj_id}", type="tertiary", help="Edit"):
                _edit_obj_dialog(obj_id, obj_title)
        with c_del:
            if st.button(" ", icon=":material/delete:", key=f"dobj_{obj_id}", type="tertiary", help="Delete"):
                _confirm_delete_obj_dialog(obj_id, obj_title)

        st.markdown(f'<div style="font-size:22px; font-weight:700; color:#fff; line-height:1.35; margin:12px 0 20px;">{obj_title}</div>', unsafe_allow_html=True)

        # ── PROGRESS & TREND ──
        st.markdown(
            f"""<div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
<span style="font-size:2.6rem; font-weight:800; color:#fff; letter-spacing:-0.04em; line-height:1;">{avg_pct:.0f}%</span>
<span style="font-size:11px; font-weight:700; color:{trend_txt}; background:{trend_bg}; padding:4px 10px; border-radius:6px; text-transform:uppercase; letter-spacing:0.04em;">{trend_label}</span>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(_obj_progress_bar(avg_pct), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:13px; color:{MUTED}; margin-bottom:20px;">{avg_pct:.0f}% completion · {active_krs} / {total_krs} KRs achieved</div>', unsafe_allow_html=True)

        # ── KEY RESULTS ──
        st.markdown('<div style="font-size:15px; font-weight:700; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:0.06em; padding:16px 0 12px; border-top:1px solid rgba(255,255,255,0.06);">Key Results</div>', unsafe_allow_html=True)

        if effective_krs_data:
            for data in effective_krs_data:
                _render_kr_block(data, active_kr)
        else:
            st.markdown(f'<div style="color:{MUTED}; padding:1.5rem 0; font-size:14px; text-align:center;">No key results tracked yet.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR block
# ---------------------------------------------------------------------------

def _render_kr_block(data, active_kr: str) -> None:
    kr, pct, val, latest, upds = data["kr"], data["pct"], data["val"], data["latest"], data["updates"]
    kr_id, title = str(kr["id"]), kr["title"]
    target, unit = float(kr.get("target", 0)), str(kr.get("unit", ""))
    pct_color = _pct_color(pct)

    with st.container():
        st.markdown('<div class="kr-block-trigger" style="display:none;"></div>', unsafe_allow_html=True)

        # ── ROW 1 ──
        st.markdown(
            f"""<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
<div style="flex:1; padding-right:16px;">
    <div style="font-size:16px; font-weight:600; color:#FFFFFF; line-height:1.35; margin-bottom:4px;">{title}</div>
    <div style="font-size:13px; color:rgba(255,255,255,0.5); font-weight:500;">{_format_current_target(val, target, unit)}</div>
</div>
<div style="text-align:right; flex-shrink:0;">
    <div style="font-size:22px; font-weight:700; color:{pct_color}; letter-spacing:-0.02em; line-height:1;">{pct:.0f}%</div>
    <div style="font-size:9px; color:rgba(255,255,255,0.3); text-transform:uppercase; font-weight:800; letter-spacing:0.06em; margin-top:3px;">Achievement</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )

        # ── ROW 2 ──
        c_actions, c_update_info, c_btn = st.columns([1.2, 3, 1.8])

        with c_actions:
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                if st.button(" ", icon=":material/description:", key=f"sh_{kr_id}", type="tertiary", help="History"):
                    st.session_state[f"h_{kr_id}"] = not st.session_state.get(f"h_{kr_id}", False)
                    st.rerun()
            with ac2:
                if st.button(" ", icon=":material/edit:", key=f"ek_{kr_id}", type="tertiary", help="Edit"):
                    _edit_kr_dialog(kr_id, title)
            with ac3:
                if st.button(" ", icon=":material/delete:", key=f"dk_{kr_id}", type="tertiary", help="Delete"):
                    _confirm_delete_kr_dialog(kr_id, title)

        with c_update_info:
            if latest is not None:
                badge_val = _format_badge(latest.get("new_value", 0), unit)
                notes_text = str(latest.get("week_notes", "")) or ""
                st.markdown(
                    f"""<div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; padding-top:6px;">
<span style="background:rgba(45,212,191,0.12); color:{GREEN}; padding:3px 10px; border-radius:6px; font-size:13px; font-weight:700; white-space:nowrap;">{badge_val}</span>
<span style="color:rgba(255,255,255,0.7); font-size:14px; line-height:1.4;">{notes_text}</span>
</div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div style="color:rgba(255,255,255,0.25); font-size:13px; padding-top:8px;">No updates recorded</div>', unsafe_allow_html=True)

        with c_btn:
            upd_icon = ":material/sync:" if active_kr != kr_id else ":material/close:"
            if st.button("Update", icon=upd_icon, key=f"uk_{kr_id}", type="secondary", use_container_width=True):
                st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
                st.rerun()

        st.markdown(_kr_progress_bar(pct), unsafe_allow_html=True)

    if active_kr == kr_id:
        _render_update_form(kr)
    if st.session_state.get(f"h_{kr_id}"):
        _render_history(kr_id, upds)


# ---------------------------------------------------------------------------
# Update form
# ---------------------------------------------------------------------------

def _render_update_form(kr) -> None:
    kr_id = str(kr["id"])
    st.markdown('<div style="background:rgba(122,80,247,0.04); padding:1rem 1.25rem; border-radius:12px; border:1px solid rgba(122,80,247,0.12); margin:0.5rem 0 1rem;">', unsafe_allow_html=True)
    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            new_val = st.number_input("New Value", value=float(kr.get("current_value", 0)))
        with c2:
            conf = st.slider("Confidence", 1, 5, 3)
        notes = st.text_input("What happened this week?")
        blockers = st.text_input("Blockers / Dependencies")

        if st.form_submit_button("Register Update", use_container_width=True):
            try:
                update_kr_value(kr_id=kr_id, new_value=float(new_val), week_notes=notes, blockers=blockers, confidence=conf, updated_by=st.session_state.get("user", {}).get("email", "?"))
                track_action("Updated KR", detail=f"{kr_id} → {new_val}")
                st.session_state["updating_kr"] = None
                st.rerun()
            except Exception as exc: handle_error(exc, "Failed to save update", "Update KR")
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def _render_history(kr_id: str, kr_updates: pd.DataFrame) -> None:
    with st.expander("Update history", expanded=True):
        if kr_updates.empty: return
        all_time = kr_updates.sort_values("updated_at", ascending=False)
        for _, row in all_time.iterrows():
            value, notes, blockers, ts_str, row_id = row.get("new_value", "—"), row.get("week_notes", ""), row.get("blockers", ""), str(row.get("updated_at", "")), str(row.get("id", ""))
            c_info, c_del = st.columns([6, 0.5])
            with c_info:
                blocker_html = f' · <span style="color:{RED};">⚠ {blockers}</span>' if blockers else ""
                st.markdown(f"""<div style="padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04);"><div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;"><span style="color:rgba(255,255,255,0.3); font-size:12px;">{_relative_time(ts_str)}</span><span style="background:rgba(45,212,191,0.1); color:{GREEN}; padding:2px 8px; border-radius:4px; font-size:13px; font-weight:700;">{value}</span><span style="color:rgba(255,255,255,0.65); font-size:14px;">{notes}</span>{blocker_html}</div></div>""", unsafe_allow_html=True)
            with c_del:
                if row_id and st.button(" ", icon=":material/delete:", key=f"delu_{row_id}_{ts_str}", type="tertiary"):
                    try:
                        delete_update_by_id(row_id)
                        track_action("Deleted update", detail=row_id)
                        st.rerun()
                    except Exception as exc: handle_error(exc, "Failed to delete update", "Delete update")


# ---------------------------------------------------------------------------
# Dialogs (Edit/Delete/Add)
# ---------------------------------------------------------------------------

@st.dialog("Edit Objective")
def _edit_obj_dialog(obj_id: str, title: str) -> None:
    nt = st.text_area("Title", value=title, height=80)
    if st.button("Save", type="primary", use_container_width=True):
        try:
            update_objective(obj_id, nt.strip())
            track_action("Edited objective", detail=obj_id); st.rerun()
        except Exception as exc: handle_error(exc, "Failed to save objective", "Edit objective")


@st.dialog("Delete Objective")
def _confirm_delete_obj_dialog(obj_id: str, title: str) -> None:
    st.warning(f"Delete **{title}**?")
    if st.button("Confirm Delete", type="primary", use_container_width=True):
        try:
            delete_objective(obj_id); track_action("Deleted objective", detail=obj_id); st.rerun()
        except Exception as exc: handle_error(exc, "Failed to delete objective", "Delete objective")


@st.dialog("Edit Key Result")
def _edit_kr_dialog(kr_id: str, title: str) -> None:
    from sheets import load_key_results, update_kr_fields
    df = load_key_results()
    kr = df[df["id"].astype(str) == str(kr_id)].iloc[0] if not df.empty else {}
    nt = st.text_input("Title", value=kr.get("title", title))
    c1, c2 = st.columns(2)
    with c1: ntgt = st.number_input("Target", value=float(kr.get("target", 0)))
    with c2: nunit = st.text_input("Unit", value=str(kr.get("unit", "")))
    if st.button("Save Changes", type="primary", use_container_width=True):
        try:
            update_kr_fields(kr_id, nt.strip(), float(ntgt), nunit.strip()); track_action("Edited KR", detail=kr_id); st.rerun()
        except Exception as exc: handle_error(exc, "Failed to save KR changes", "Edit KR")


@st.dialog("Delete KR")
def _confirm_delete_kr_dialog(kr_id: str, title: str) -> None:
    st.warning(f"Delete **{title}**?")
    if st.button("Delete", type="primary", use_container_width=True):
        try:
            delete_kr_by_id(kr_id); track_action("Deleted KR", detail=kr_id); st.rerun()
        except Exception as exc: handle_error(exc, "Failed to delete KR", "Delete KR")


@st.dialog("New KR")
def add_kr_dialog(obj_id: str, title: str) -> None:
    name = st.text_input("Title")
    c1, c2 = st.columns(2)
    with c1: tgt = st.number_input("Target", min_value=1.0, value=100.0)
    with c2: unit = st.text_input("Unit", value="%")
    if st.button("Create", type="primary", use_container_width=True):
        if not name.strip(): st.error("Title cannot be empty."); return
        try:
            create_kr(obj_id, name.strip(), float(tgt), unit.strip()); track_action("Created KR", detail=f"for {obj_id}"); st.rerun()
        except Exception as exc: handle_error(exc, "Failed to create KR", "Create KR")
