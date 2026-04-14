"""KR update panel — renders inline below the active KR."""

import streamlit as st
from sheets import update_kr_value, load_key_results, compute_progress


def render_kr_update_panel(kr_id: str) -> None:
    """
    Inline update form for a specific KR.
    Reads KR data fresh from session cache, writes to Sheets on submit.
    Expects st.session_state['updating_kr'] == kr_id to be set before calling.
    """
    krs_df = load_key_results()

    if krs_df.empty or kr_id not in krs_df["id"].values:
        st.error(f"KR '{kr_id}' not found.")
        return

    kr = krs_df[krs_df["id"] == kr_id].iloc[0]
    current = float(kr.get("current_value", 0))
    target = float(kr.get("target", 0))
    baseline = float(kr.get("baseline", 0))
    unit = str(kr.get("unit", ""))
    direction = str(kr.get("direction", "increase")).lower()
    pct = compute_progress(kr)

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1E1442, #12132B);
            border: 1px solid #7C3AED;
            border-radius: 12px;
            padding: 20px 24px;
            margin: 8px 0 16px;
        ">
            <div style="font-size:12px; color:#A78BFA; font-weight:700;
                        letter-spacing:0.06em; text-transform:uppercase; margin-bottom:6px;">
                Updating {kr_id}
            </div>
            <div style="font-size:15px; color:#E2E8F0; font-weight:600; margin-bottom:12px;">
                {kr['title']}
            </div>
            <div style="display:flex; gap:24px; font-size:12px; color:#64748B;">
                <span>Baseline: <strong style="color:#94A3B8;">{baseline:g} {unit}</strong></span>
                <span>Target: <strong style="color:#94A3B8;">{target:g} {unit}</strong></span>
                <span>Current: <strong style="color:#A78BFA;">{current:g} {unit}</strong></span>
                <span>Progress: <strong style="color:#A78BFA;">{pct:.1f}%</strong></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form(key=f"update_form_{kr_id}", clear_on_submit=True):
        col1, col2 = st.columns([2, 3])

        with col1:
            if unit == "done":
                new_val_raw = st.selectbox(
                    "New value",
                    options=[0.0, 1.0],
                    format_func=lambda x: "Done ✓" if x >= 1 else "Pending",
                    index=int(current >= 1),
                )
            else:
                step = 0.1 if unit in ("%", "score", "hours") else 1.0
                min_v = min(baseline, target) - abs(target - baseline)
                max_v = max(baseline, target) + abs(target - baseline)
                new_val_raw = st.number_input(
                    f"New value ({unit})",
                    min_value=float(min_v),
                    max_value=float(max_v),
                    value=float(current),
                    step=step,
                    format="%.2f" if step < 1 else "%.0f",
                )

        with col2:
            note = st.text_input("Note (optional)", placeholder="What changed? Add context…")

        col_submit, col_cancel = st.columns([1, 1])
        with col_submit:
            submitted = st.form_submit_button("Save Update", use_container_width=True, type="primary")
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            user = st.session_state.get("user", {})
            email = user.get("email", "unknown")
            try:
                update_kr_value(
                    kr_id=kr_id,
                    new_value=float(new_val_raw),
                    updated_by=email,
                    note=note,
                )
                st.success(f"Updated {kr_id} → {new_val_raw:g} {unit}")
                st.session_state.pop("updating_kr", None)
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to save: {exc}")

        if cancelled:
            st.session_state.pop("updating_kr", None)
            st.rerun()
