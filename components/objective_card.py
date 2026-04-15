"""Objective card — Ontop design system."""

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
)

CORAL  = "#E35276"
PURPLE = "#261C94"
BORDER = "#2A2A3E"
TEXT1  = "#FFFFFF"
TEXT2  = "#B8B8C8"
MUTED  = "#6B6B7E"
AMBER  = "#F59E0B"

_CARD_CSS_INJECTED = False

def _inject_card_css() -> None:
    global _CARD_CSS_INJECTED
    if _CARD_CSS_INJECTED:
        return
    st.markdown("""
<style>
.obj-toggle-card {
    cursor: pointer;
    position: relative;
    background: radial-gradient(circle at top right, rgba(227,82,118,0.10), transparent 35%),
                linear-gradient(180deg, rgba(26,26,36,.92), rgba(6,6,9,.92));
    border: 1px solid #2A2A3E;
    border-radius: 20px;
    padding: 1.1rem 1.25rem .9rem;
    margin-bottom: .75rem;
    transition: border-color 0.2s ease;
}
.obj-toggle-card:hover { border-color: #3a3f6e; }
.obj-badge-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}
.obj-badge {
    padding: 3px 10px;
    border-radius: 999px;
    font-size: .76rem;
    font-weight: 700;
    letter-spacing: .03em;
    white-space: nowrap;
}
.obj-badge-coral {
    background: rgba(227,82,118,.12);
    color: #ff9ab0;
    border: 1px solid rgba(227,82,118,.32);
}
.obj-badge-amber {
    background: rgba(245,158,11,.12);
    color: #f8c56a;
    border: 1px solid rgba(245,158,11,.28);
}
.obj-badge-green {
    background: rgba(34,197,94,.12);
    color: #7ee2a8;
    border: 1px solid rgba(34,197,94,.30);
}
.obj-subteam { color: #6B6B7E; font-size: 13px; }
.obj-chevron { margin-left: auto; color: #6B6B7E; font-size: 12px; }
.obj-title { color: #FFFFFF; font-size: 16px; font-weight: 700; line-height: 1.35; }

/* Invisible Streamlit toggle button stretched over the card */
div[data-testid="stButton"].obj-toggle-btn > button {
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    width: 100% !important; height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
    z-index: 10 !important;
    border-radius: 20px !important;
}
</style>
""", unsafe_allow_html=True)
    _CARD_CSS_INJECTED = True


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Editar Key Result")
def _edit_kr_dialog(kr_id: str, current_title: str, current_target: float, current_unit: str) -> None:
    new_title  = st.text_input("Título del KR",  value=current_title)
    new_target = st.number_input("Target", value=float(current_target), min_value=0.0, step=1.0)
    new_unit   = st.text_input("Unidad",         value=current_unit)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True, key=f"edit_cancel_{kr_id}"):
            st.rerun()
    with c2:
        if st.button("Guardar", type="primary", use_container_width=True, key=f"edit_save_{kr_id}"):
            try:
                update_kr_fields(kr_id, new_title, new_target, new_unit)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


@st.dialog("Confirmar eliminación de KR")
def _confirm_delete_kr_dialog(kr_id: str, kr_title: str) -> None:
    st.warning(f"¿Eliminar este KR y **todos** sus updates? Esta acción no se puede deshacer.")
    st.markdown(
        f'<div style="font-size:13px;color:{TEXT2};padding:6px 0 10px;">{kr_title}</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True, key=f"dkr_cancel_{kr_id}"):
            st.rerun()
    with c2:
        if st.button("Eliminar", type="primary", use_container_width=True, key=f"dkr_ok_{kr_id}"):
            try:
                delete_kr_by_id(kr_id)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


@st.dialog("New Key Result")
def add_kr_dialog(objective_id: str, objective_title: str) -> None:
    cap = objective_title[:80] + "…" if len(objective_title) > 80 else objective_title
    st.caption(cap)

    title = st.text_input(
        "Key Result description",
        placeholder="Ex: Revenue reaches $20K/month",
    )

    col_target, col_unit = st.columns([2, 1])
    with col_target:
        target = st.number_input("Target value", min_value=0.0, value=100.0, step=1.0)
    with col_unit:
        _UNITS = ["$", "$/month", "%", "tickets/month", "workflows", "Launched", "PASS", "binary", "Custom..."]
        unit_sel = st.selectbox("Unit", options=_UNITS)

    if unit_sel == "Custom...":
        unit = st.text_input("Custom unit", placeholder="Ex: MRR, AUM, users")
    else:
        unit = unit_sel

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True, key=f"add_kr_cancel_{objective_id}"):
            st.rerun()
    with c2:
        if st.button("Create KR", type="primary", use_container_width=True, key=f"add_kr_create_{objective_id}"):
            if title.strip():
                create_kr(objective_id, title.strip(), target, unit)
                st.rerun()
            else:
                st.error("La descripción no puede estar vacía.")


@st.dialog("Confirmar eliminación de update")
def _confirm_delete_update_dialog(update_id: str) -> None:
    st.warning("¿Eliminar este update? El valor del KR se recalculará con el update más reciente restante.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True, key=f"du_cancel_{update_id}"):
            st.rerun()
    with c2:
        if st.button("Eliminar", type="primary", use_container_width=True, key=f"du_ok_{update_id}"):
            try:
                delete_update_by_id(update_id)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _progress_bar(pct: float) -> str:
    return f"""
    <div class="progress-track">
        <div class="progress-fill" style="width:{pct:.1f}%;"></div>
    </div>"""


# ---------------------------------------------------------------------------
# Objective card
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, active_kr: str, show_sub_team: bool = False) -> None:
    _inject_card_css()

    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")

    obj_krs = krs_df[krs_df["objective_id"] == obj_id] if not krs_df.empty else krs_df
    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    if avg_pct >= 70:
        status_label, badge_cls = "On Track",  "obj-badge-green"
    elif avg_pct >= 40:
        status_label, badge_cls = "At Risk",   "obj-badge-amber"
    else:
        status_label, badge_cls = "Off Track", "obj-badge-coral"

    exp_key   = f"obj_expanded_{obj_id}"
    if exp_key not in st.session_state:
        st.session_state[exp_key] = False
    is_expanded = st.session_state[exp_key]
    chevron     = "▲" if is_expanded else "▼"

    subteam_html = (
        f'<span class="obj-subteam">{sub_team}</span>'
        if (show_sub_team and sub_team) else ""
    )

    # Card HTML — the visible toggle
    st.markdown(f"""
<div class="obj-toggle-card" style="position:relative;">
    <div class="obj-badge-row">
        <span class="obj-badge {badge_cls}">{avg_pct:.0f}% · {status_label}</span>
        {subteam_html}
        <span class="obj-chevron">{chevron}</span>
    </div>
    <div class="obj-title">{obj_title}</div>
</div>
""", unsafe_allow_html=True)

    # Invisible button that captures the click — CSS stretches it over the card
    st.markdown('<div class="obj-toggle-btn">', unsafe_allow_html=True)
    if st.button("toggle", key=f"toggle_{obj_id}", label_visibility="collapsed"):
        st.session_state[exp_key] = not is_expanded
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # KRs — only when expanded
    if is_expanded:
        if obj_krs.empty:
            st.markdown(
                f'<div style="padding:10px 0 4px 8px;"><span style="color:{MUTED};font-size:13px;">No Key Results yet.</span></div>',
                unsafe_allow_html=True,
            )
        else:
            for _, kr in obj_krs.iterrows():
                _render_kr_row(kr, active_kr)

        col_add, _ = st.columns([2, 5])
        with col_add:
            if st.button("+ Add KR", key=f"add_kr_{obj_id}", type="tertiary"):
                add_kr_dialog(obj_id, str(obj_title))

    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR row
# ---------------------------------------------------------------------------

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
        if st.button("✏", key=f"e_{kr_id}", help="Editar KR", type="tertiary"):
            _edit_kr_dialog(kr_id, str(title), float(target), str(unit))

    with c_del:
        if st.button("🗑", key=f"d_{kr_id}", help="Eliminar KR", type="tertiary"):
            _confirm_delete_kr_dialog(kr_id, str(title))

    with c_show:
        hist_key  = f"h_{kr_id}"
        hist_open = st.session_state.get(hist_key, False)
        st.button(
            "↑ Hide updates" if hist_open else "→ Show updates",
            key=f"s_{kr_id}",
            type="tertiary",
            on_click=lambda k=hist_key: st.session_state.update({k: not st.session_state.get(k, False)}),
        )

    with c_upd:
        is_upd = active_kr == kr_id
        st.button(
            "✕ Cancel" if is_upd else "Update",
            key=f"u_{kr_id}",
            type="secondary",
            use_container_width=True,
            on_click=lambda: st.session_state.update(
                {"updating_kr": None if active_kr == kr_id else kr_id}
            ),
        )

    if active_kr == kr_id:
        _render_update_form(kr)

    if st.session_state.get(f"h_{kr_id}", False):
        _render_history(kr_id)


# ---------------------------------------------------------------------------
# Update form
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Update history
# ---------------------------------------------------------------------------

def _render_history(kr_id: str) -> None:
    updates = load_updates_for_kr(kr_id)

    if updates.empty:
        st.markdown(
            f'<span style="color:{MUTED};font-size:12px;padding:8px 0;display:block;">No updates yet.</span>',
            unsafe_allow_html=True,
        )
        return

    for _, row in updates.iterrows():
        update_id = str(row.get("id", ""))
        val       = row.get("new_value", "")
        notes     = str(row.get("week_notes", "") or "")
        blockers  = str(row.get("blockers",   "") or "")
        conf      = int(row.get("confidence",  0) or 0)
        dots      = "●" * conf + "○" * (5 - conf)

        col_info, col_del = st.columns([12, 1])
        with col_info:
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid {BORDER};">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                    <span style="font-size:13px;font-weight:600;color:{TEXT1};">→ {val}</span>
                    <span style="font-size:10px;color:{MUTED};">{row.get('updated_at', '')}</span>
                </div>
                <div style="font-size:11px;color:{TEXT2};">
                    {row.get('updated_by', '')} &nbsp;·&nbsp;
                    <span style="color:{CORAL};">{dots}</span>
                </div>
                {"" if not notes    else f'<div style="font-size:12px;color:{TEXT2};margin-top:4px;">📝 {notes}</div>'}
                {"" if not blockers else f'<div style="font-size:12px;color:{AMBER};margin-top:2px;">⚠️ {blockers}</div>'}
            </div>
            """, unsafe_allow_html=True)
        with col_del:
            if st.button("🗑", key=f"del_upd_{update_id}", help="Eliminar update", type="tertiary"):
                _confirm_delete_update_dialog(update_id)
