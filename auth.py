"""
auth.py — Google OAuth manual flow para Streamlit Cloud.
Sin streamlit-google-auth ni extra_streamlit_components.
Usa requests-oauthlib + JWT cookies (PyJWT).
"""

import json
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import jwt
import requests
import streamlit as st

ALLOWED_DOMAIN   = "getontop.com"
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"

COOKIE_NAME      = "ontop_okrs_auth"
COOKIE_EXPIRY_D  = 1
APP_URL          = "https://ops-okrs-dashboard.streamlit.app"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cfg() -> dict:
    s = st.secrets
    return {
        "client_id":     s["GOOGLE_CLIENT_ID"],
        "client_secret": s["GOOGLE_CLIENT_SECRET"],
        "cookie_secret": s["COOKIE_SECRET"],
    }


def _make_jwt(user: dict, secret: str) -> str:
    payload = {
        **user,
        "exp": datetime.now(timezone.utc) + timedelta(days=COOKIE_EXPIRY_D),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _decode_jwt(token: str, secret: str) -> dict | None:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        return None


def _set_cookie(token: str) -> None:
    exp = datetime.now(timezone.utc) + timedelta(days=COOKIE_EXPIRY_D)
    exp_str = exp.strftime("%a, %d %b %Y %H:%M:%S GMT")
    cookie_val = urllib.parse.quote(token)
    st.markdown(
        f"""<script>
        document.cookie = "{COOKIE_NAME}={cookie_val}; path=/; expires={exp_str}; SameSite=Lax; Secure";
        </script>""",
        unsafe_allow_html=True,
    )


def _get_cookie() -> str | None:
    """Read cookie via URL query params injected by JS — see _inject_cookie_reader()."""
    return st.session_state.get("_auth_cookie_value")


def _inject_cookie_reader() -> None:
    """
    Injects a tiny JS snippet that reads the auth cookie and sends it back
    as a query param so Python can read it on the next rerun.
    Only runs once per session.
    """
    if st.session_state.get("_cookie_reader_injected"):
        return
    st.session_state["_cookie_reader_injected"] = True

    st.markdown("""
    <script>
    (function() {
        const name = "%s=";
        const cookies = document.cookie.split(';');
        let val = '';
        for (let c of cookies) {
            c = c.trim();
            if (c.startsWith(name)) { val = c.substring(name.length); break; }
        }
        if (val) {
            const url = new URL(window.location.href);
            if (!url.searchParams.get('_auth_token')) {
                url.searchParams.set('_auth_token', val);
                window.history.replaceState(null, '', url.toString());
                window.location.reload();
            }
        }
    })();
    </script>
    """ % COOKIE_NAME, unsafe_allow_html=True)


def _build_auth_url(cfg: dict) -> str:
    import secrets
    state = secrets.token_urlsafe(16)
    st.session_state["oauth_state"] = state
    params = {
        "client_id":     cfg["client_id"],
        "redirect_uri":  APP_URL,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "online",
        "prompt":        "select_account",
    }
    return GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)


def _exchange_code(code: str, cfg: dict) -> dict | None:
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri":  APP_URL,
        "grant_type":    "authorization_code",
    }, timeout=10)
    if not resp.ok:
        return None
    access_token = resp.json().get("access_token")
    if not access_token:
        return None
    info = requests.get(GOOGLE_USERINFO,
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=10)
    return info.json() if info.ok else None


# ---------------------------------------------------------------------------
# Public API (same interface as before)
# ---------------------------------------------------------------------------

def require_login() -> bool:
    """
    Returns True if the user is authenticated.
    Handles the OAuth callback (code exchange) automatically.
    """
    cfg = _cfg()
    params = st.query_params

    # 1. Handle OAuth callback
    code  = params.get("code")
    state = params.get("state")
    if code and state:
        if state != st.session_state.get("oauth_state"):
            st.error("Invalid OAuth state. Please try logging in again.")
            st.query_params.clear()
            return False

        user_info = _exchange_code(code, cfg)
        if not user_info:
            st.error("Failed to retrieve user info from Google.")
            st.query_params.clear()
            return False

        email = user_info.get("email", "")
        if ALLOWED_DOMAIN and not email.endswith(f"@{ALLOWED_DOMAIN}"):
            st.error(f"⛔ Access restricted to @{ALLOWED_DOMAIN}. You signed in as `{email}`.")
            st.query_params.clear()
            return False

        # Store in session
        _hydrate_session(user_info)

        # Set cookie
        token = _make_jwt({
            "email":      email,
            "name":       user_info.get("name", ""),
            "given_name": user_info.get("given_name", ""),
            "picture":    user_info.get("picture", ""),
        }, cfg["cookie_secret"])
        _set_cookie(token)

        st.query_params.clear()
        st.rerun()

    # 2. Already in session
    if st.session_state.get("connected"):
        return True

    # 3. Try cookie via query param (injected by JS on previous load)
    token_from_url = params.get("_auth_token")
    if token_from_url:
        payload = _decode_jwt(urllib.parse.unquote(token_from_url), cfg["cookie_secret"])
        if payload:
            email = payload.get("email", "")
            if not ALLOWED_DOMAIN or email.endswith(f"@{ALLOWED_DOMAIN}"):
                _hydrate_session(payload)
                st.query_params.clear()
                return True

    return False


def _hydrate_session(user_info: dict) -> None:
    email = user_info.get("email", "")
    st.session_state["connected"] = True
    st.session_state["user_info"] = user_info
    st.session_state["user"] = {
        "email":      email,
        "name":       user_info.get("name", email.split("@")[0]),
        "given_name": user_info.get("given_name", email.split("@")[0]),
        "picture":    user_info.get("picture", ""),
    }


def get_user() -> dict:
    return st.session_state.get("user") or {}


def logout() -> None:
    for key in ("user", "connected", "user_info", "oauth_state",
                "_auth_cookie_value", "_cookie_reader_injected"):
        st.session_state.pop(key, None)
    # Clear cookie
    st.markdown(
        f"""<script>
        document.cookie = "{COOKIE_NAME}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        </script>""",
        unsafe_allow_html=True,
    )


def render_login_button() -> None:
    """Renders the Google Sign-In button. Call inside render_login_page()."""
    cfg = _cfg()
    auth_url = _build_auth_url(cfg)
    st.link_button(
        "Sign in with Google",
        auth_url,
        type="primary",
        use_container_width=True,
    )
