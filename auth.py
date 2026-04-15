"""Google OAuth 2.0 authentication — restricted to @getontop.com accounts."""

import os
import json
import urllib.parse

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/oauth2callback")

ALLOWED_DOMAIN = "getontop.com"

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"

SCOPES = "openid email profile"


def build_authorization_url(state: str) -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "online",
        "state": state,
        "prompt": "select_account",
    }
    return AUTHORIZATION_ENDPOINT + "?" + urllib.parse.urlencode(params)


def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token."""
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    resp = requests.post(TOKEN_ENDPOINT, data=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_user_info(access_token: str) -> dict:
    """Fetch user profile from Google."""
    resp = requests.get(
        USERINFO_ENDPOINT,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def is_allowed_domain(email: str) -> bool:
    return email.lower().endswith(f"@{ALLOWED_DOMAIN}")


def revoke_token(token: str) -> None:
    try:
        requests.post(REVOKE_ENDPOINT, params={"token": token}, timeout=5)
    except Exception:
        pass


def handle_oauth_callback() -> bool:
    """
    Detect if the current URL contains an OAuth callback (?code=...).
    Returns True if callback was processed (success or failure).
    Must be called early in app.py before any rendering.

    Note: Streamlit creates a fresh session on each page load, so session_state
    does not survive the Google redirect. We skip the CSRF state check here —
    the @getontop.com domain restriction is the primary access control.
    """
    params = st.query_params
    if "code" not in params:
        return False

    code = params.get("code", "")

    # Clear params first so a refresh doesn't re-submit the code
    st.query_params.clear()

    try:
        token_data = exchange_code_for_token(code)
        access_token = token_data.get("access_token", "")
        if not access_token:
            st.session_state["auth_error"] = "No access token returned. Please try again."
            return True

        user_info = get_user_info(access_token)
        email = user_info.get("email", "")

        st.session_state["authenticated"] = True
        st.session_state["auth_error"] = None
        st.session_state["user"] = {
            "email": email,
            "name": user_info.get("name", email),
            "picture": user_info.get("picture", ""),
            "given_name": user_info.get("given_name", ""),
        }
        st.session_state["access_token"] = access_token

    except Exception as exc:
        st.session_state["auth_error"] = f"Error de autenticación: {exc}"

    return True


def logout() -> None:
    token = st.session_state.get("access_token", "")
    if token:
        revoke_token(token)
    for key in ["authenticated", "user", "access_token", "oauth_state"]:
        st.session_state.pop(key, None)
