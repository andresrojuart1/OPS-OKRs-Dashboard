"""Google OAuth via Streamlit's built-in authentication."""

import streamlit as st


def require_login() -> bool:
    """Returns True if the user is currently logged in."""
    return st.user.is_logged_in


def get_user() -> dict:
    """Returns a normalised user-info dict from st.user."""
    if not st.user.is_logged_in:
        return {}
    return {
        "email":      getattr(st.user, "email",      "") or "",
        "name":       getattr(st.user, "name",       "") or getattr(st.user, "email", "") or "",
        "picture":    getattr(st.user, "picture",    "") or "",
        "given_name": getattr(st.user, "given_name", "") or "",
    }


def logout() -> None:
    st.logout()
