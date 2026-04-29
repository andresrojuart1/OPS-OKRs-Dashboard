"""
auth.py — Google OAuth via streamlit-google-auth
Replaces Streamlit native st.login() which has MismatchingStateError on Cloud.

Session state keys set by this module:
  st.session_state["connected"]  → bool
  st.session_state["user_info"]  → dict (name, email, picture)
  st.session_state["user"]       → dict (same shape as before, for app.py compat)
"""

import streamlit as st
from streamlit_google_auth import Authenticate

ALLOWED_DOMAIN = "getontop.com"


def _build_authenticator() -> Authenticate:
    return Authenticate(
        secret_credentials_path="google_credentials.json",
        cookie_name="ontop_okrs_auth",
        cookie_key=st.secrets.get(
            "COOKIE_SECRET",
            "9b31807a59e2a7709a1b8e5c494ca2fc97ea37dc4e332d39f190c0a06e808dda",
        ),
        redirect_uri="https://ops-okrs-dashboard.streamlit.app",
        cookie_expiry_days=1,
    )


def require_login() -> bool:
    """
    Call once at the top of render_dashboard().
    Returns True if user is authenticated and from the allowed domain.
    Handles the OAuth callback automatically.
    """
    auth = _build_authenticator()
    auth.check_authentification()  # catches the Google callback

    if not st.session_state.get("connected", False):
        return False

    user_info = st.session_state.get("user_info", {})
    email = user_info.get("email", "")

    # Domain restriction
    if ALLOWED_DOMAIN and not email.endswith(f"@{ALLOWED_DOMAIN}"):
        st.error(
            f"⛔ Access restricted to @{ALLOWED_DOMAIN} accounts. "
            f"You signed in as `{email}`."
        )
        if st.button("Sign out"):
            logout()
            st.rerun()
        return False

    # Hydrate st.session_state["user"] for backward compat with app.py
    if not st.session_state.get("user"):
        st.session_state["user"] = {
            "email":      email,
            "name":       user_info.get("name", email.split("@")[0]),
            "given_name": user_info.get("name", "").split()[0] if user_info.get("name") else email.split("@")[0],
            "picture":    user_info.get("picture", ""),
        }

    return True


def get_user() -> dict:
    """Returns the current user dict (backward compat with app.py)."""
    return st.session_state.get("user") or {}


def logout() -> None:
    auth = _build_authenticator()
    auth.logout()
    for key in ("user", "connected", "user_info", "oauth_id"):
        st.session_state.pop(key, None)


def render_login_button() -> None:
    """
    Renders the Google Sign-In button.
    Use inside render_login_page() instead of st.login("google").
    """
    auth = _build_authenticator()
    auth.check_authentification()

    if not st.session_state.get("connected", False):
        authorization_url = auth.get_authorization_url()
        st.link_button(
            "Sign in with Google",
            authorization_url,
            type="primary",
            use_container_width=True,
        )
