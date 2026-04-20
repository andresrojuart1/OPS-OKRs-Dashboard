"""Lightweight logging and observability for the OKRs Dashboard."""

import logging
import os
from datetime import datetime
from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

_LOG_FORMAT = "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(format=_LOG_FORMAT, datefmt=_DATE_FORMAT, level=logging.INFO)
logger = logging.getLogger("okr_dashboard")

if DEBUG:
    logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Activity tracker (session-state backed)
# ---------------------------------------------------------------------------

MAX_ACTIVITY_LOG = 50  # keep last N entries


def _ensure_activity_state() -> None:
    if "activity_log" not in st.session_state:
        st.session_state["activity_log"] = []
    if "last_action" not in st.session_state:
        st.session_state["last_action"] = None


def track_action(action: str, status: str = "success", detail: str = "") -> None:
    """Record a user/system action for observability.

    Args:
        action:  Short description, e.g. "Updated KR"
        status:  "success" | "error"
        detail:  Optional extra context
    """
    _ensure_activity_state()

    entry = {
        "action": action,
        "status": status,
        "detail": detail,
        "timestamp": datetime.now(),
    }

    st.session_state["last_action"] = entry
    log = st.session_state["activity_log"]
    log.insert(0, entry)
    st.session_state["activity_log"] = log[:MAX_ACTIVITY_LOG]

    # Also emit to Python logger
    msg = f"{action}"
    if detail:
        msg += f" — {detail}"
    if status == "error":
        logger.error(msg)
    else:
        logger.info(msg)


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------

def handle_error(exc: Exception, user_msg: str, action_label: Optional[str] = None) -> None:
    """Unified error handler: shows user message, logs exception, tracks action.

    Args:
        exc:          The caught exception
        user_msg:     Clean message shown to the user
        action_label: Optional label for the activity log
    """
    logger.exception(user_msg)

    if DEBUG:
        st.exception(exc)
    else:
        st.error(user_msg)

    if action_label:
        track_action(action_label, status="error", detail=str(exc)[:200])


# ---------------------------------------------------------------------------
# UI components
# ---------------------------------------------------------------------------

def render_last_action() -> None:
    """Render a subtle 'last action' indicator in the UI."""
    _ensure_activity_state()
    last = st.session_state.get("last_action")
    if not last:
        return

    ts: datetime = last["timestamp"]
    diff = datetime.now() - ts
    minutes = int(diff.total_seconds() / 60)

    if minutes == 0:
        ago = "just now"
    elif minutes < 60:
        ago = f"{minutes}m ago"
    else:
        ago = f"{minutes // 60}h ago"

    icon = "✅" if last["status"] == "success" else "❌"
    st.markdown(
        f'<div style="font-size:11px; color:rgba(255,255,255,0.35); '
        f'text-align:right; padding:4px 0;">'
        f'{icon} {last["action"]} · {ago}</div>',
        unsafe_allow_html=True,
    )


def render_activity_log() -> None:
    """Render a collapsible activity log panel."""
    _ensure_activity_state()
    log = st.session_state.get("activity_log", [])
    if not log:
        return

    with st.expander("📋 Activity Log", expanded=False):
        for entry in log[:20]:
            ts: datetime = entry["timestamp"]
            time_str = ts.strftime("%H:%M:%S")
            icon = "✅" if entry["status"] == "success" else "❌"
            detail = f' — <span style="opacity:0.6">{entry["detail"]}</span>' if entry.get("detail") else ""

            st.markdown(
                f'<div style="font-size:12px; color:rgba(255,255,255,0.6); '
                f'padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.04);">'
                f'<span style="color:rgba(255,255,255,0.3); margin-right:8px;">{time_str}</span>'
                f'{icon} {entry["action"]}{detail}</div>',
                unsafe_allow_html=True,
            )
