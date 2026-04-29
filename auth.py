"""
auth.py — Google OAuth manual para Streamlit Cloud.
Sin cookies, sin JS. Solo session_state + query_params.
La sesión dura mientras el tab está abierto (suficiente para uso interno).
"""

import urllib.parse
import secrets as _secrets

import jwt
import requests
import streamlit as st
from datetime import datetime, timedelta, timezone

ALLOWED_DOMAIN   = "getontop.com"
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"
APP_URL          = "https://ops-okrs-dashboard.streamlit.app"


def _cfg():
    s = st.secrets
    return {
        "client_id":     s["GOOGLE_CLIENT_ID"],
        "client_secret": s["GOOGLE_CLIENT_SECRET"],
    }


def _exchange_code(code: str, cfg: dict) -> dict | None:
    r = requests.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri":  APP_URL,
        "grant_type":    "authorization_code",
    }, timeout=10)
    if not r.ok:
        return None
    access_token = r.json().get("access_token")
    if not access_token:
        return None
    info = requests.get(
        GOOGLE_USERINFO,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    return info.json() if info.ok else None


def _hydrate(user_info: dict) -> None:
    email = user_info.get("email", "")
    st.session_state["connected"] = True
    st.session_state["user_info"] = user_info
    st.session_state["user"] = {
        "email":      email,
        "name":       user_info.get("name",       email.split("@")[0]),
        "given_name": user_info.get("given_name", email.split("@")[0]),
        "picture":    user_info.get("picture",    ""),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def require_login() -> bool:
    """
    Returns True if authenticated.
    Must be called at the very top of every render cycle.
    """
    # 1. Already authenticated this session
    if st.session_state.get("connected"):
        return True

    # 2. Google OAuth callback — code in URL
    code = st.query_params.get("code")
    if code:
        cfg = _cfg()
        # Clear URL immediately so reloads don't re-exchange the same code
        st.query_params.clear()

        user_info = _exchange_code(code, cfg)
        if not user_info:
            st.error("Google authentication failed. Please try again.")
            return False

        email = user_info.get("email", "")
        if ALLOWED_DOMAIN and not email.endswith(f"@{ALLOWED_DOMAIN}"):
            st.error(f"⛔ Access restricted to @{ALLOWED_DOMAIN}. Signed in as `{email}`.")
            return False

        _hydrate(user_info)
        st.rerun()  # clean rerun without code in URL

    return False


def get_user() -> dict:
    return st.session_state.get("user") or {}


def logout() -> None:
    for k in ("user", "connected", "user_info"):
        st.session_state.pop(k, None)


def render_login_button() -> None:
    """Renders the Google Sign-In button. Call inside render_login_page()."""
    cfg = _cfg()
    params = {
        "client_id":     cfg["client_id"],
        "redirect_uri":  APP_URL,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "online",
        "prompt":        "select_account",
    }
    auth_url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    st.link_button(
        "Sign in with Google",
        auth_url,
        type="primary",
        use_container_width=True,
    )
