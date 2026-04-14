"""Objective card — Ontop design system."""

import streamlit as st
from sheets import compute_progress, format_value, load_updates_for_kr, update_kr_value

CORAL  = "#E35276"
PURPLE = "#261C94"
BORDER = "#2A2A3E"
TEXT1  = "#FFFFFF"
TEXT2  = "#B8B8C8"
MUTED  = "#6B6B7E"
AMBER  = "#F59E0B"


def _pct_badge(pct: float) -> str:
    if pct >= 70:
        cls, label = "status-green", "On Track"
    elif pct >= 40:
        cls, label = "status-amber", "At Risk"
    else:
        cls, label = "status-coral", "Off Track"
    return (
        f'<span class="ontop-status-badge {cls}">{pct:.0f}% · {label}</span>'
    )


def _progress_bar(pct: float) -> str:
    return f"""
    <div class="progress-track">
        <div class="progress-fill" style="width:{pct:.1f}%;"></div>
    </div>"""


def render_objective_card(obj_row, krs_df, active_kr: str) -> None:
    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")

    obj_krs = krs_df[krs_df["objective_id"] == obj_id] if not krs_df.empty else krs_df
    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    st.markdown(f"""
    <div class="okr-card">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
            <div style="display:flex;align-items:center;gap:10px;">
                {_pct_badge(avg_pct)}
                <span style="font-size:11px;color:{MUTED};">{sub_team}</span>
            </div>
        </div>
        <div style="font-size:16px;font-weight:700;color:{TEXT1};line-height:1.35;">
            {obj_title}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if obj_krs.empty:
        st.markdown(f'<div style="padding:10px 0;"><span style="color:{MUTED};font-size:13px;">No Key Results yet.</span></div>', unsafe_allow_html=True)
    else:
        for i, (_, kr) in enumerate(obj_krs.iterrows()):
            _render_kr_row(kr, active_kr)

    st.markdown("<div style='margin-bottom:18px;'></div>", unsafe_allow_html=True)


def _render_kr_row(kr, active_kr: str) -> None:
    kr_id   = str(kr["id"])
    title   = kr["title"]
    current = float(kr.get("current_value", 0))
    target  = float(kr.get("target", 0))
    unit    = str(kr.get("unit", ""))
    pct     = compute_progress(kr)
    val_str = format_value(current, target, unit)

    st.markdown(f"""
    <div class="kr-row">
        <div style="font-size:13px;font-weight:500;color:{TEXT1};line-height:1.4;margin-bottom:4px;">
            {title}
        </div>
        <div style="font-size:11px;color:{MUTED};margin-bottom:6px;">{val_str}</div>
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:10px;color:{MUTED};text-transform:uppercase;
                         letter-spacing:.06em;min-width:48px;">Progress</span>
            <div style="flex:1;background:{BORDER};border-radius:999px;height:5px;">
                <div style="width:{pct:.1f}%;height:100%;border-radius:999px;
                             background:linear-gradient(90deg,{PURPLE},{CORAL});"></div>
            </div>
            <span style="font-size:12px;font-weight:700;color:{CORAL};min-width:30px;text-align:right;">
                {pct:.0f}%
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action row
    c_edit, c_del, c_show, c_gap, c_upd = st.columns([0.5, 0.5, 2, 4, 2])

    with c_edit:
        st.button("✏", key=f"e_{kr_id}", help="Edit KR (TODO)", type="tertiary")
    with c_del:
        st.button("🗑", key=f"d_{kr_id}", help="Delete KR (TODO)", type="tertiary")
    with c_show:
        hist_key  = f"h_{kr_id}"
        hist_open = st.session_state.get(hist_key, False)
        st.button(
            "↑ Hide updates" if hist_open else "→ Show updates",
            key=f"s_{kr_id}", type="tertiary",
            on_click=lambda k=hist_key: st.session_state.update({k: not st.session_state.get(k, False)}),
        )
    with c_upd:
        is_upd = active_kr == kr_id
        st.button(
            "✕ Cancel" if is_upd else "Update",
            key=f"u_{kr_id}",
            type="secondary" if is_upd else "primary",
            use_container_width=True,
            on_click=lambda: st.session_state.update(
                {"updating_kr": None if active_kr == kr_id else kr_id}
            ),
        )

    if active_kr == kr_id:
        _render_update_form(kr)

    if st.session_state.get(f"h_{kr_id}", False):
        _render_history(kr_id)


def _render_update_form(kr) -> None:
    kr_id   = str(kr["id"])
    unit    = str(kr.get("unit", ""))
    target  = float(kr.get("target", 0))
    current = float(kr.get("current_value", 0))

    st.markdown(f"""
    <div style="background:rgba(38,28,148,0.12);border:1px solid rgba(124,115,247,0.3);
                border-radius:16px;padding:14px 18px 4px;margin:8px 0 4px;">
        <div style="font-size:10px;color:#b5afff;font-weight:700;
                    text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">
            Update · {kr_id}
        </div>
        <div style="font-size:12px;color:{TEXT2};">
            {kr['title'][:80]}{'…' if len(kr['title'])>80 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form(key=f"f_{kr_id}", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            if unit.lower() == "binary":
                new_val = float(st.selectbox(
                    "New value", [0.0, 1.0],
                    format_func=lambda x: "✓ Done" if x >= 1 else "Pending",
                    index=int(current >= 1),
                ))
            else:
                step = 0.1 if "%" in unit else (1000.0 if "$" in unit else 1.0)
                new_val = st.number_input(
                    f"New value ({unit})", min_value=0.0,
                    max_value=float(target * 3) if target > 0 else 1e9,
                    value=float(current), step=step,
                )
        with c2:
            confidence = st.slider("Confidence", 1, 5, 3)

        week_notes = st.text_area("What happened this week?",
                                  placeholder="Key wins, progress made…", height=72)
        blockers   = st.text_area("Blockers / Dependencies",
                                  placeholder="What's in the way?", height=56)

        cs, cc = st.columns(2)
        with cs:
            submitted = st.form_submit_button("Save Update", use_container_width=True)
        with cc:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            email = st.session_state.get("user", {}).get("email", "unknown")
            try:
                update_kr_value(
                    kr_id=kr_id, new_value=float(new_val),
                    week_notes=week_notes, blockers=blockers,
                    confidence=int(confidence), updated_by=email,
                )
                st.success(f"{kr_id} updated → {format_value(float(new_val), target, unit)}")
                st.session_state["updating_kr"] = None
                st.rerun()
            except Exception as exc:
                st.error(f"Error: {exc}")

        if cancelled:
            st.session_state["updating_kr"] = None
            st.rerun()


def _render_history(kr_id: str) -> None:
    updates = load_updates_for_kr(kr_id)
    with st.container():
        st.markdown(f"""
        <div style="background:rgba(6,6,9,0.9);border:1px solid {BORDER};
                    border-radius:14px;padding:12px 16px;margin:4px 0 6px;">
        """, unsafe_allow_html=True)

        if updates.empty:
            st.markdown(f'<span style="color:{MUTED};font-size:12px;">No updates yet.</span>',
                        unsafe_allow_html=True)
        else:
            for _, row in updates.iterrows():
                val      = row.get("new_value", "")
                notes    = str(row.get("week_notes", "") or "")
                blockers = str(row.get("blockers", "") or "")
                conf     = int(row.get("confidence", 0) or 0)
                dots     = "●" * conf + "○" * (5 - conf)
                st.markdown(f"""
                <div style="padding:8px 0;border-bottom:1px solid {BORDER};">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                        <span style="font-size:13px;font-weight:600;color:{TEXT1};">→ {val}</span>
                        <span style="font-size:10px;color:{MUTED};">{row.get('updated_at','')}</span>
                    </div>
                    <div style="font-size:11px;color:{TEXT2};">
                        {row.get('updated_by','')} &nbsp;·&nbsp;
                        <span style="color:{CORAL};">{dots}</span>
                    </div>
                    {"" if not notes    else f'<div style="font-size:12px;color:{TEXT2};margin-top:4px;">📝 {notes}</div>'}
                    {"" if not blockers else f'<div style="font-size:12px;color:{AMBER};margin-top:2px;">⚠️ {blockers}</div>'}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
