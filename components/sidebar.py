"""Sidebar — Ontop design system (ported from shared.py)."""

from typing import Optional
import streamlit as st
from auth import logout as _logout
import os
_DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

SUB_TEAMS = [
    "All",
    "New Initiatives",
    "FinOps",
    "AI Experience",
    "AI Monetization",
    "Security & Compliance Ops",
]


def render_sidebar() -> Optional[str]:
    if "selected_team" not in st.session_state:
        st.session_state["selected_team"] = "All"

    user    = st.session_state.get("user", {})
    name    = user.get("name", "Admin")
    email   = user.get("email", "")
    picture = user.get("picture", "")
    initials = "".join(p[0] for p in name.split()[:2]).upper() or "A"

    with st.sidebar:
        # Brand
        st.markdown("""
        <div class="ontop-sidebar-brand">
            <span class="ontop-sidebar-badge">Operations</span>
            <h1>OKRs 2026</h1>
            <p>Ontop · Operations Team</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

        selected = st.session_state["selected_team"]
        for team in SUB_TEAMS:
            is_sel = team == selected
            label  = f"{'● ' if is_sel else '  '}{team}"
            if st.button(label, key=f"t_{team}", use_container_width=True,
                         type="secondary" if not is_sel else "primary"):
                st.session_state["selected_team"] = team
                st.rerun()

        st.markdown('<div class="ontop-sidebar-section-label" style="margin-top:24px;">Reporting Week</div>', unsafe_allow_html=True)
        
        # Week Selector with Arrows
        current_week = st.session_state["selected_week"]
        wk_cols = st.columns([1, 2, 1])
        with wk_cols[0]:
            if st.button("←", key="prev_wk", use_container_width=True):
                st.session_state["selected_week"] = max(1, current_week - 1)
                st.rerun()
        with wk_cols[1]:
            st.markdown(f"""
            <div style="background:rgba(122,80,247,0.1); border:1px solid rgba(122,80,247,0.3); 
                        border-radius:10px; padding:6px 0; text-align:center; font-weight:700; color:#fff; font-size:14px;">
                Week {current_week}
            </div>
            """, unsafe_allow_html=True)
        with wk_cols[2]:
            if st.button("→", key="next_wk", use_container_width=True):
                st.session_state["selected_week"] = min(53, current_week + 1)
                st.rerun()

        # User card
        if picture:
            avatar_html = f'<img src="{picture}" style="width:2.5rem;height:2.5rem;border-radius:999px;object-fit:cover;" />'
        else:
            avatar_html = f'<div class="ontop-sidebar-avatar">{initials}</div>'

        st.markdown(f"""
        <div class="ontop-sidebar-user">
            {avatar_html}
            <div>
                <span class="ontop-sidebar-user-label">Signed in</span>
                <strong>{name}</strong>
                <span>{email}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Sign out", key="signout", use_container_width=True, type="tertiary"):
            if _DEV_MODE:
                st.session_state.pop("dev_authenticated", None)
                st.session_state.pop("user", None)
                st.rerun()
            else:
                _logout()

        st.caption("v1.1 · OPS-Trend-Active")

    return selected
