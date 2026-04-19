"""Sidebar — Ontop design system (ported from shared.py)."""

from typing import Optional
import streamlit as st
from auth import logout as _logout
import os
_DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

SUB_TEAMS = [
    "All",
    "Growth Initiatives",
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
        if st.button("🔄 Refresh Data", use_container_width=True, type="secondary"):
            st.cache_data.clear()
            st.rerun()
            
        # Brand
        st.markdown("""
        <div class="ontop-sidebar-brand">
            <span class="ontop-sidebar-badge">Operations</span>
            <h1>OKRs Q2 2026</h1>
            <p>Ontop · Operations Team</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="ontop-sidebar-section-label">Sub-teams</div>', unsafe_allow_html=True)

        selected = st.session_state["selected_team"]
        for team in SUB_TEAMS:
            is_sel = team == selected
            label  = f"{'● ' if is_sel else '  '}{team}"
            if st.button(label, key=f"t_{team}", use_container_width=True,
                         type="secondary" if not is_sel else "primary"):
                st.session_state["selected_team"] = team
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

    return None if selected == "All" else selected
