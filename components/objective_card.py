"""Objective card — Executive Boardroom Layout.

Hierarchy: Sub-team → Objective → Key Results
Logic: Accurate historical progress (Average of KRs) & Time-Travel navigation.
Design Focus:
- 15px update narrative (Critical readability)
- Left-Right KR layout
- Distinct value badges
"""

import html
import pandas as pd
import streamlit as st
from datetime import datetime, timezone

from sheets import (
    compute_progress,
    create_kr,
    delete_kr_by_id,
    delete_update_by_id,
    edit_kr_update,
    format_value,
    load_updates_for_kr,
    normalize_kr_id,
    update_kr_fields,
    update_kr_value,
    update_objective,
    delete_objective,
)
from observability import handle_error, track_action

# ---------------------------------------------------------------------------
# Visual tokens — integrated with CSS design system
# ---------------------------------------------------------------------------

MUTED = "rgba(255,255,255,0.4)"
PURPLE = "#A78BFA"  # status-purple from CSS
GREEN = "#10B981"   # status-green from CSS
YELLOW = "#FBBF24"  # status-yellow from CSS
RED = "#EF4444"     # status-red from CSS


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


def _kr_compact_bar(pct: float) -> str:
    return f"""<div style="background:rgba(255,255,255,0.06); border-radius:999px; height:6px; overflow:hidden; margin: 2px 0 16px 0;">
<div style="height:100%; width:{max(min(pct, 100), 0.5):.1f}%; border-radius:999px; background:{PURPLE}; transition: width 0.6s ease;"></div>
</div>"""


def _format_badge(value, unit: str, fmt_override: str = "number") -> str:
    try: v = float(value)
    except: return str(value)
    
    # Try override first, fallback to unit label
    f = str(fmt_override).lower().strip() if fmt_override else "number"
    u = unit.lower().strip()
    
    if f == "percentage" or u in ("percentage", "%"): return f"{v:.1f}%"
    if f == "currency" or u in ("currency", "$", "$/month"): return f"${v:,.2f}"
    
    return f"{v:g} {unit if u not in ('number', 'count') else ''}"


def _format_current_target(current: float, target: float, unit: str, fmt: str = "number") -> str:
    f = fmt.lower().strip()
    u = unit.lower().strip()
    if u == "binary": return "Done ✓" if current >= 1 else "Pending"
    
    def apply_fmt(val):
        if f == "percentage" or u in ("percentage", "%"): return f"{val:.1f}%"
        if f == "currency" or u in ("currency", "$", "$/month"): return f"${val:,.2f}"
        return f"{val:g}"

    label = unit if u not in ("percentage", "%", "currency", "$", "number", "count") else ""
    return f"{apply_fmt(current)} / {apply_fmt(target)} {label}"


# ---------------------------------------------------------------------------
# Main Component
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, updates_df, krs_info_all: dict, is_primary: bool = False, read_only: bool = False) -> None:
    obj_id, obj_title = str(obj_row["id"]), obj_row["title"]
    sub_team = obj_row.get("sub_team", "")
    selected_week = st.session_state.get("selected_week", 1)
    active_kr = st.session_state.get("updating_kr") or ""
    # Use read_only parameter if provided (presentation mode), otherwise check if viewing "All" team
    is_read_only = read_only or st.session_state.get("selected_team", "All") == "All"

    # Logic: Use precomputed historical/average progress passed from app.py
    obj_krs = krs_df[krs_df["objective_id"].astype(str) == obj_id] if not krs_df.empty else pd.DataFrame()
    effective_data = []
    
    for _, kr in obj_krs.iterrows():
        kr_id = normalize_kr_id(kr["id"])
        info = krs_info_all.get(kr_id, {
            "kr": kr, "pct": 0.0, "val": float(kr.get("current_value", 0)), 
            "latest": None, "narrative": None, "prev_pct": None
        })
        effective_data.append(info)

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
        st.markdown(f'<div style="font-size:14px; font-weight:800; color:{PURPLE}; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:6px;">{sub_team} · WEEK {selected_week}</div>', unsafe_allow_html=True)
        
        c_title_width = 5 if st.session_state.get("selected_team", "All") != "All" else 5.5
        c_title, c_opts = st.columns([c_title_width, 0.5])
        with c_title:
            st.markdown(f'<div style="font-size:20px; font-weight:700; color:#fff; line-height:1.3; margin-bottom:8px;">{obj_title}</div>', unsafe_allow_html=True)

        if st.session_state.get("selected_team", "All") != "All":
            with c_opts:
                # Only show objective buttons when not in presentation mode
                if not is_read_only:
                    edit_col, settings_col = st.columns([0.08, 0.08], gap="small")
                    with edit_col:
                        if st.button("", icon=":material/edit:", key=f"edit_title_{obj_id}", type="tertiary", help="Edit title"):
                            st.session_state["updating_kr"] = None
                            st.session_state[f"obj_view_{obj_id}"] = "edit_title"
                            st.rerun()
                    with settings_col:
                        if st.button("", icon=":material/settings:", key=f"opt_{obj_id}", type="tertiary", help="Objective settings"):
                            # Clear any active KR update when opening objective settings
                            st.session_state["updating_kr"] = None
                            st.session_state["active_obj_settings"] = {"id": obj_id, "title": obj_title}
                            st.rerun()
        
        # Dialog is now triggered globally in app.py for persistence

        # Objective Progress Summary
        st.markdown(f'<div style="font-size:32px; font-weight:700; color:#fff; line-height:1;">{avg_pct:.0f}%</div>', unsafe_allow_html=True)
        st.markdown(_obj_progress_bar(avg_pct), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:13px; color:{MUTED}; margin-bottom:20px; font-weight:600;">{achieved} / {total} KRs achieved</div>', unsafe_allow_html=True)

        # Divider Section
        st.markdown('<div style="font-size:13px; font-weight:800; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:0.1em; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:12px;">Key Results Tracking</div>', unsafe_allow_html=True)

        if effective_data:
            for data in effective_data:
                _render_kr_block(data, active_kr, is_read_only)

        else:
            st.markdown(f'<div style="padding:16px; text-align:center; color:{MUTED}; font-size:14px;">No key results found.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR Render
# ---------------------------------------------------------------------------

def _render_kr_block(data, active_kr: str, is_read_only: bool) -> None:
    kr, pct, val, latest = data["kr"], data["pct"], data["val"], data["latest"]
    narrative = data.get("narrative") # Specifically for current week display
    prev_pct = data.get("prev_pct")
    kr_id, title = normalize_kr_id(kr["id"]), kr["title"]
    target, unit = float(kr.get("target", 0)), str(kr.get("unit", ""))


    def _render_trend():
        if prev_pct is None: return ""
        diff = pct - prev_pct
        if abs(diff) < 0.1: return ""
        color = "#10b981" if diff > 0 else "#ef4444"
        prefix = "+" if diff > 0 else ""
        return f'<span style="font-size:12px; font-weight:700; color:{color}; margin-left:8px;">{prefix}{diff:.1f}pp</span>'

    # Deployment Verification Marker
    st.markdown("<!-- OKR-V1.1 -->", unsafe_allow_html=True)

    with st.container():
        # Use the is_read_only parameter passed from render_objective_card (includes presentation mode)
        h_left_width = 5 if not is_read_only else 5.5
        h_left, h_right = st.columns([h_left_width, 0.5])
        title_safe = html.escape(str(title), quote=False)
        h_left.markdown(
            f'<div style="font-size:18px; font-weight:600; color:#fff; line-height:1.2; margin-bottom:12px;">{title_safe}</div>',
            unsafe_allow_html=True,
        )

        if not is_read_only:
            with h_right:
                # Two icon buttons: edit (✏️) and settings (⚙️) - same layout as objective
                edit_col, settings_col = st.columns([0.08, 0.08], gap="small")
                button_icon = ":material/close:" if active_kr == kr_id else ":material/edit:"
                button_help = "Cancel update" if active_kr == kr_id else "Update KR"
                with edit_col:
                    if st.button("", icon=button_icon, key=f"upd_{kr_id}", type="tertiary", help=button_help):
                        # Ensure we clear objective settings when updating a KR
                        st.session_state.pop("active_obj_settings", None)
                        st.session_state["updating_kr"] = None if active_kr == kr_id else kr_id
                        st.session_state["editing_id"] = None
                        st.rerun()
                with settings_col:
                    if st.button("", icon=":material/settings:", key=f"edit_meta_{kr_id}", type="tertiary", help="KR settings"):
                        # Also clear KR update state when opening metadata dialog
                        st.session_state["updating_kr"] = None
                        _edit_kr_metadata_dialog(kr)

        # --- VALUE ROW ---
        v_left, v_right = st.columns([0.7, 0.3])
        cur_fmt = latest.get("value_format", "number") if latest is not None else "number"
        v_left.markdown(f'<div style="font-size:13px; color:rgba(255,255,255,0.45); font-weight:500; margin-top:-4px;">{_format_current_target(val, target, unit, cur_fmt)}</div>', unsafe_allow_html=True)
        v_right.markdown(f'<div style="text-align:right; font-size:15px; font-weight:800; color:{_pct_color(pct)}; margin-top:-8px;">{pct:.0f}% progress{_render_trend()}</div>', unsafe_allow_html=True)

        # --- PROGRESS BAR DIRECTLY BELOW ---
        st.markdown(_kr_compact_bar(pct), unsafe_allow_html=True)

        # --- NARRATIVE ROW & PROGRESS ---
        if narrative is not None:
            badge_color = _pct_color(pct)
            fmt_override = narrative.get("value_format", "number")
            notes_safe = html.escape(str(narrative.get("week_notes", "") or ""), quote=False)
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; margin-top:14px; background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; border-left:4px solid {badge_color};">
                <div style="background:{badge_color}1a; color:{badge_color}; padding:4px 10px; border-radius:6px; font-size:16px; font-weight:700; white-space:nowrap;">{_format_badge(val, unit, fmt_override)}</div>
                <div style="flex:1; font-size:16px; color:rgba(255,255,255,0.8); line-height:1.55;">{notes_safe}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Row (Edit/Deps)
            if not is_read_only:
                col_edit, col_empty = st.columns([0.08, 0.92])
                if col_edit.button("", icon=":material/edit:", key=f"edit_btn_{narrative.get('id')}", type="tertiary", width="stretch", help="Edit update"):
                    st.session_state["updating_kr"] = kr_id
                    st.session_state["editing_id"] = narrative.get("id")
                    st.rerun()

            deps = narrative.get("blockers", "")
            if deps:
                deps_safe = html.escape(str(deps), quote=False)
                st.markdown(
                    f'<div style="padding-left:12px; margin-top:4px; font-size:13px; color:#f87171; font-weight:500;">'
                    f"⚠ Dependencies: {deps_safe}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div style="font-size:14px; color:{MUTED}; font-style:italic; margin-top:10px; opacity:0.6; margin-bottom:12px;">No updates recorded for this week.</div>',
                unsafe_allow_html=True,
            )

    if not is_read_only and active_kr == kr_id: _render_update_form(data)


# ---------------------------------------------------------------------------
# Update Form
# ---------------------------------------------------------------------------

def _render_update_form(data):
    kr, latest = data["kr"], data["latest"]
    kr_id = normalize_kr_id(kr["id"])
    edit_id = st.session_state.get("editing_id")
    
    # Pre-populate if editing
    init_val = float(kr.get("current_value", 0))
    init_notes = ""
    init_deps = ""
    init_fmt = "number"
    
    if edit_id and latest is not None and str(latest.get("id")) == str(edit_id):
        # Explicit schema mapping (Standardizing field names)
        init_val = float(latest.get("value", latest.get("new_value", init_val)))
        init_notes = str(latest.get("notes", latest.get("week_notes", "")))
        init_deps = str(latest.get("dependencies", latest.get("blockers", "")))
        init_fmt = str(latest.get("value_format", "number"))

    st.markdown('<div style="background:rgba(122,80,247,0.05); padding:16px; border-radius:12px; border:1px solid rgba(122,80,247,0.2); margin:12px 0;">', unsafe_allow_html=True)
    with st.form(key=f"frm_{kr_id}"):
        c1, c2 = st.columns([1, 1])
        with c1:
            val = st.number_input("Numerical Value", value=init_val)
        with c2:
            v_fmt = st.selectbox("Value format", ["number", "percentage", "currency"], 
                               index=["number", "percentage", "currency"].index(init_fmt) if init_fmt in ["number", "percentage", "currency"] else 0)
            
        notes = st.text_input("Narrative (Notes)", value=init_notes)
        deps = st.text_input("Dependencies / Blockers", value=init_deps)
        
        btn_label = "Update Log" if edit_id else "Save New Update"
        if st.form_submit_button(btn_label, width="stretch"):
            curr_edit_id = st.session_state.get("editing_id")
            try:
                if curr_edit_id:
                    edit_kr_update(curr_edit_id, val, notes, deps, v_fmt)
                else:
                    selected_week = st.session_state.get("selected_week", 1)
                    update_kr_value(
                        kr_id, val, notes, deps, 3, 
                        st.session_state.get("user",{}).get("email","?"),
                        selected_week,
                        v_fmt
                    )
                
                # Assume success if no exception raised
                st.session_state["updating_kr"] = None
                st.session_state["editing_id"] = None
                st.rerun()
            except Exception as e:
                handle_error(e, "Operation failed", "Update")
    st.markdown("</div>", unsafe_allow_html=True)

@st.dialog("Objective Settings")
def _obj_actions_dialog(id, title):
    view = st.session_state.get(f"obj_view_{id}", "menu")
    
    # helper to close everything
    def _close():
        st.session_state.pop("active_obj_settings", None)
        st.session_state.pop(f"obj_view_{id}", None)
        st.rerun()

    if view == "edit_title":
        st.markdown("### Edit Objective Title")
        nt = st.text_input("Title", value=title)
        c1, c2 = st.columns(2)
        if c1.button("Save", type="primary", width="stretch"):
            update_objective(id, nt)
            _close()
        if c2.button("Back", width="stretch"):
            st.session_state.pop(f"obj_view_{id}", None)
            st.rerun()
            
    elif view == "add_kr":
        st.markdown("### Add New Key Result")
        t = st.text_input("KR Title")
        tgt = st.number_input("Target", value=100.0)
        fmt = st.selectbox("Format", ["number", "percentage", "currency"])
        c1, c2 = st.columns(2)
        if c1.button("Create", type="primary", width="stretch"):
            create_kr(id, t, tgt, fmt)
            _close()
        if c2.button("Back", width="stretch"):
            st.session_state.pop(f"obj_view_{id}", None)
            st.rerun()

    elif view == "delete_confirm":
        st.error("⚠️ **Delete Objective?** This will also delete all associated Key Results and cannot be undone.")
        c1, c2 = st.columns(2)
        if c1.button("Yes, delete", type="primary", width="stretch"):
            delete_objective(id)
            _close()
        if c2.button("No, cancel", width="stretch"):
            st.session_state[f"obj_view_{id}"] = "menu"
            st.rerun()
            
    else:
        st.write(f"Objective: **{title}**")
        if st.button("Add Key Result", width="stretch"):
            st.session_state[f"obj_view_{id}"] = "add_kr"
            st.rerun()
        st.divider()
        if st.button("Delete Objective", type="secondary", width="stretch"):
            st.session_state[f"obj_view_{id}"] = "delete_confirm"
            st.rerun()

        if st.button("Close Settings", width="stretch", type="tertiary"):
            _close()

@st.dialog("Edit Key Result")
def _edit_kr_metadata_dialog(kr):
    kr_id = normalize_kr_id(kr["id"])
    t_val = st.text_input("Title", value=kr["title"])
    tgt_val = st.number_input("Target Value", value=float(kr["target"]))
    
    # Standardized Format Selector with Mapping
    fmt_options = ["number", "percentage", "currency"]
    # Map existing unit to format for compatibility
    curr_u = str(kr.get("unit", "number")).lower().strip()
    idx = 0
    if curr_u in ("percentage", "%"): idx = 1
    elif curr_u in ("currency", "$", "$/month"): idx = 2
    
    f_val = st.selectbox("Display Format", options=fmt_options, index=idx)
    
    if st.button("Save Metadata", width="stretch"):
        try:
            update_kr_fields(kr_id, t_val, tgt_val, f_val)
            st.rerun()
        except Exception as e:
            handle_error(e, "Failed to update KR metadata", "KR")
            
    st.divider()
    if st.button("Delete Key Result", type="secondary", width="stretch"):
        try:
            delete_kr_by_id(kr_id)
            track_action("Deleted KR", detail=kr_id)
            st.rerun()
        except Exception as e:
            handle_error(e, "Failed to delete KR", "KR")

