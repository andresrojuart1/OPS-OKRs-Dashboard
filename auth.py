"""
auth.py — Google OAuth manual, sin librerías de auth externas.
Compatibilidad total con app.py existente (require_login / get_user / logout).
"""

import urllib.parse
import secrets as _secrets

import jwt
import requests
import streamlit as st
from datetime import datetime, timedelta, timezone

ALLOWED_DOMAIN  = "getontop.com"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL= "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"
COOKIE_NAME     = "ontop_okrs_auth"
COOKIE_EXPIRY_D = 1
APP_URL         = "https://ops-okrs-dashboard.streamlit.app"


# ── helpers ──────────────────────────────────────────────────────────────────

def _cfg():
    s = st.secrets
    return {
        "client_id":     s["GOOGLE_CLIENT_ID"],
        "client_secret": s["GOOGLE_CLIENT_SECRET"],
        "cookie_secret": s["COOKIE_SECRET"],
    }


def _make_jwt(user: dict, secret: str) -> str:
    payload = {**user,
               "exp": datetime.now(timezone.utc) + timedelta(days=COOKIE_EXPIRY_D),
               "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, secret, algorithm="HS256")


def _decode_jwt(token: str, secret: str) -> dict | None:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        return None


def _set_cookie(token: str) -> None:
    exp = (datetime.now(timezone.utc) + timedelta(days=COOKIE_EXPIRY_D)
           ).strftime("%a, %d %b %Y %H:%M:%S GMT")
    st.markdown(
        f"<script>document.cookie='{COOKIE_NAME}="
        f"{urllib.parse.quote(token)};path=/;expires={exp};SameSite=Lax;Secure';</script>",
        unsafe_allow_html=True,
    )


def _clear_cookie() -> None:
    st.markdown(
        f"<script>document.cookie='{COOKIE_NAME}=;path=/;"
        "expires=Thu, 01 Jan 1970 00:00:00 GMT';</script>",
        unsafe_allow_html=True,
    )


def _exchange_code(code: str, cfg: dict) -> dict | None:
    r = requests.post(GOOGLE_TOKEN_URL, data={
        "code": code, "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri": APP_URL, "grant_type": "authorization_code",
    }, timeout=10)
    if not r.ok:
        return None
    access_token = r.json().get("access_token")
    if not access_token:
        return None
    info = requests.get(GOOGLE_USERINFO,
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=10)
    return info.json() if info.ok else None


def _hydrate(user_info: dict) -> None:
    email = user_info.get("email", "")
    st.session_state["connected"] = True
    st.session_state["user_info"] = user_info
    st.session_state["user"] = {
        "email":      email,
        "name":       user_info.get("name", email.split("@")[0]),
        "given_name": user_info.get("given_name", email.split("@")[0]),
        "picture":    user_info.get("picture", ""),
    }


def _build_auth_url(cfg: dict) -> str:
    # Store state in BOTH session_state AND query_params so it survives reruns
    state = _secrets.token_urlsafe(20)
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


# ── public API ────────────────────────────────────────────────────────────────

def require_login() -> bool:
    cfg   = _cfg()
    qp    = st.query_params

    # ── 1. Already authenticated in this session ──
    if st.session_state.get("connected"):
        return True

    # ── 2. OAuth callback: code + state in URL ──
    code  = qp.get("code")
    state = qp.get("state")

    if code and state:
        # Accept state from session_state OR from a _st param we embed in the URL
        expected = (st.session_state.get("oauth_state") or
                    qp.get("_st"))          # fallback: we encoded it in the redirect

        if not expected or state != expected:
            st.warning("Session expired — please sign in again.")
            st.query_params.clear()
            st.rerun()
            return False

        user_info = _exchange_code(code, cfg)
        if not user_info:
            st.error("Could not retrieve user info from Google. Please try again.")
            st.query_params.clear()
            return False

        email = user_info.get("email", "")
        if ALLOWED_DOMAIN and not email.endswith(f"@{ALLOWED_DOMAIN}"):
            st.error(f"⛔ Access restricted to @{ALLOWED_DOMAIN}. Signed in as `{email}`.")
            st.query_params.clear()
            return False

        _hydrate(user_info)
        token = _make_jwt(st.session_state["user"], cfg["cookie_secret"])
        _set_cookie(token)
        st.query_params.clear()
        st.rerun()

    # ── 3. Try JWT cookie (via _token param injected by JS below) ──
    raw_token = qp.get("_token")
    if raw_token:
        payload = _decode_jwt(urllib.parse.unquote(raw_token), cfg["cookie_secret"])
        if payload:
            email = payload.get("email", "")
            if not ALLOWED_DOMAIN or email.endswith(f"@{ALLOWED_DOMAIN}"):
                _hydrate(payload)
                st.query_params.clear()
                return True

    # ── 4. Inject JS to read cookie and reload with _token param ──
    if not st.session_state.get("_cookie_checked"):
        st.session_state["_cookie_checked"] = True
        st.markdown(f"""<script>
        (function(){{
            var m=document.cookie.match(/(^|;)\\s*{COOKIE_NAME}=([^;]+)/);
            if(m){{
                var u=new URL(window.location.href);
                if(!u.searchParams.get('_token')){{
                    u.searchParams.set('_token',m[2]);
                    window.location.replace(u.toString());
                }}
            }}
        }})();
        </script>""", unsafe_allow_html=True)

    return False


def get_user() -> dict:
    return st.session_state.get("user") or {}


def logout() -> None:
    _clear_cookie()
    for k in ("user","connected","user_info","oauth_state","_cookie_checked"):
        st.session_state.pop(k, None)


def render_login_button() -> None:
    """Renders the Google Sign-In link button. Call inside render_login_page()."""
    cfg = _cfg()
    # Embed state in the redirect URL itself (_st param) so it survives session loss
    state = _secrets.token_urlsafe(20)
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
    auth_url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    st.link_button("Sign in with Google", auth_url,
                   type="primary", use_container_width=True)
