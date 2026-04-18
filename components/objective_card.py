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
    update_objective,
    delete_objective,
)

CORAL  = "#E35276"
PURPLE = "#7c73f7"
BORDER = "rgba(255,255,255,0.1)"
TEXT1  = "#FFFFFF"
TEXT2  = "#B8B8C8"
MUTED  = "#6B6B7E"
AMBER  = "#F59E0B"


# ---------------------------------------------------------------------------
# Objective Dialogs
# ---------------------------------------------------------------------------

@st.dialog("Editar Objetivo")
def _edit_obj_dialog(obj_id: str, current_title: str) -> None:
    new_title = st.text_area("Título del Objetivo", value=current_title, height=100)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True, key=f"edit_obj_cancel_{obj_id}"):
            st.rerun()
    with c2:
        if st.button("Guardar", type="primary", use_container_width=True, key=f"edit_obj_save_{obj_id}"):
            update_objective(obj_id, new_title.strip())
            st.rerun()

@st.dialog("Confirmar eliminación de Objetivo")
def _confirm_delete_obj_dialog(obj_id: str, obj_title: str) -> None:
    st.error(f"¿Eliminar este Objetivo y TODOS sus KRs asociados? Esta acción no se puede deshacer.")
    st.markdown(f"**{obj_title}**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", use_container_width=True, key=f"dobj_cancel_{obj_id}"):
            st.rerun()
    with c2:
        if st.button("Eliminar Todo", type="primary", use_container_width=True, key=f"dobj_ok_{obj_id}"):
            delete_objective(obj_id)
            st.rerun()


# ---------------------------------------------------------------------------
# KR Dialogs
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
    st.caption(f"Parent: {cap}")

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

def _pct_badge(pct: float) -> str:
    if pct >= 70:
        cls, label = "status-green", "On Track"
    elif pct >= 40:
        cls, label = "status-amber", "At Risk"
    else:
        cls, label = "status-coral", "Off Track"
    
    # Modern badge styles
    bg_color = "rgba(34,197,94,0.1)" if pct >= 70 else ("rgba(245,158,11,0.1)" if pct >= 40 else "rgba(227,82,118,0.1)")
    border_color = "rgba(34,197,94,0.3)" if pct >= 70 else ("rgba(245,158,11,0.3)" if pct >= 40 else "rgba(227,82,118,0.3)")
    text_color = "#7ee2a8" if pct >= 70 else ("#f8c56a" if pct >= 40 else "#ff9ab0")
    
    return f'<span class="ontop-status-badge" style="background:{bg_color}; border:1px solid {border_color}; color:{text_color};">{pct:.0f}% · {label}</span>'


def _progress_bar(pct: float) -> str:
    return f"""
    <div class="progress-track">
        <div class="progress-fill" style="width:{pct:.1f}%;"></div>
    </div>"""


# ---------------------------------------------------------------------------
# Objective Card
# ---------------------------------------------------------------------------

def render_objective_card(obj_row, krs_df, active_kr: str) -> None:
    obj_id    = str(obj_row["id"])
    obj_title = obj_row["title"]
    sub_team  = obj_row.get("sub_team", "")

    obj_krs = krs_df[krs_df["objective_id"] == obj_id] if not krs_df.empty else krs_df
    avg_pct = obj_krs.apply(compute_progress, axis=1).mean() if not obj_krs.empty else 0.0

    st.markdown(f"""
    <div class="okr-card">
        <div class="objective-header">
            <div style="display:flex; flex-direction:column; gap:8px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    {_pct_badge(avg_pct)}
                    <span style="font-size:12px; color:{MUTED}; font-weight:600; text-transform:uppercase;">{sub_team}</span>
                </div>
                <div class="objective-title">{obj_title}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action row for Objective (compact & aligned)
    c_edit, c_del, c_add, _ = st.columns([0.6, 0.6, 1.5, 6])
    with c_edit:
        if st.button("✏️", key=f"e_obj_{obj_id}", help="Editar Objetivo", type="tertiary"):
            _edit_obj_dialog(obj_id, str(obj_title))
    with c_del:
        if st.button("🗑️", key=f"d_obj_{obj_id}", help="Eliminar Objetivo", type="tertiary"):
            _confirm_delete_obj_dialog(obj_id, str(obj_title))
    with c_add:
        if st.button("+ Add KR", key=f"add_kr_{obj_id}", type="tertiary"):
            add_kr_dialog(obj_id, str(obj_title))

    if obj_krs.empty:
        st.markdown(
            f'<div style="padding:0 1.5rem 1rem; color:{MUTED}; font-size:0.9rem;">No Key Results yet.</div>',
            unsafe_allow_html=True,
        )
    else:
        # Tighter spacing before KRs
        st.markdown('<div style="margin-top:-10px;"></div>', unsafe_allow_html=True)
        for _, kr in obj_krs.iterrows():
            _render_kr_row(kr, active_kr)

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KR Row
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
        <div class="kr-title">{title}</div>
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 8px;">
            <span style="font-size:12px; color:{MUTED};">{val_str}</span>
            <span style="font-size:13px; font-weight:700; color:{CORAL};">{pct:.0f}%</span>
        </div>
        {_progress_bar(pct)}
    </div>
    """, unsafe_allow_html=True)

    # Action row for KR
    c_edit, c_del, c_show, c_gap, c_upd = st.columns([0.6, 0.6, 2, 4, 1.8])

    with c_edit:
        if st.button("✏️", key=f"e_{kr_id}", help="Editar KR", type="tertiary"):
            _edit_kr_dialog(kr_id, str(title), float(target), str(unit))

    with c_del:
        if st.button("🗑️", key=f"d_{kr_id}", help="Eliminar KR", type="tertiary"):
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
            "✕ Close" if is_upd else "Update Status",
            key=f"u_{kr_id}",
            type="secondary" if not is_upd else "primary",
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
    <div style="background:rgba(124,115,247,0.05); border:1px solid rgba(124,115,247,0.2);
                border-radius:16px; padding:14px 18px 4px; margin:8px 0 12px;">
        <div style="font-size:10px; color:#b5afff; font-weight:700;
                    text-transform:uppercase; letter-spacing:.08em; margin-bottom:4px;">
            Update Progress
        </div>
        <div style="font-size:12px; color:{TEXT2};">
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
                                  placeholder="Key wins, progress made…", height=80)
        blockers   = st.text_area("Blockers / Dependencies",
                                  placeholder="What's in the way?", height=60)

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
                st.success("Update saved!")
                st.session_state["updating_kr"] = None
                st.rerun()
            except Exception as exc:
                st.error(f"Error: {exc}")

        if cancelled:
            st.session_state["updating_kr"] = None
            st.rerun()


# ---------------------------------------------------------------------------
# Update History
# ---------------------------------------------------------------------------

def _render_history(kr_id: str) -> None:
    updates = load_updates_for_kr(kr_id)

    if updates.empty:
        st.markdown(
            f'<span style="color:{MUTED}; font-size:12px; padding:12px 1.2rem; display:block;">No updates yet.</span>',
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

        with st.container():
            st.markdown(f"""
            <div style="padding:12px 0; border-bottom:1px solid {BORDER}; margin-bottom:4px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                    <span style="font-size:13px; font-weight:600; color:{TEXT1};">→ {val}</span>
                    <span style="font-size:10px; color:{MUTED};">{row.get('updated_at', '')}</span>
                </div>
                <div style="font-size:11px; color:{TEXT2};">
                    {row.get('updated_by', '')} &nbsp;·&nbsp;
                    <span style="color:{CORAL}; letter-spacing:2px;">{dots}</span>
                </div>
                {"" if not notes    else f'<div style="font-size:12px; color:{TEXT2}; margin-top:6px; background:rgba(255,255,255,0.02); padding:8px; border-radius:8px;">📝 {notes}</div>'}
                {"" if not blockers else f'<div style="font-size:12px; color:{AMBER}; margin-top:4px; padding:0 8px;">⚠️ {blockers}</div>'}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🗑️ Remove Update", key=f"del_upd_{update_id}", type="tertiary"):
                _confirm_delete_update_dialog(update_id)
