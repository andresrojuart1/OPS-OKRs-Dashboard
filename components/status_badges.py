"""Status badge system — integrated with CSS design tokens"""

import streamlit as st


def render_status_badge(status: str, text: str = None) -> None:
    """Render a status badge aligned with design system.

    Args:
        status: "success" | "warning" | "error" | "info"
        text: Optional override text (uses status name if not provided)
    """
    display_text = text or status.upper()

    status_classes = {
        "success": "status-success",
        "warning": "status-warning",
        "error": "status-error",
        "info": "status-info",
    }

    css_class = status_classes.get(status.lower(), "status-info")

    st.markdown(
        f"""
        <span style="
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.05em;
        " class="{css_class}">
            {display_text}
        </span>
        """,
        unsafe_allow_html=True
    )


def render_progress_indicator(current: float, target: float, status: str = None) -> None:
    """Render progress with automatic status inference.

    Args:
        current: Current value
        target: Target value
        status: Optional override ("success" | "warning" | "error")
    """
    if status is None:
        pct = (current / target * 100) if target > 0 else 0
        if pct >= 100:
            status = "success"
        elif pct >= 75:
            status = "warning"
        else:
            status = "error"

    status_colors = {
        "success": "#10B981",
        "warning": "#FBBF24",
        "error": "#EF4444",
        "info": "#A78BFA",
    }

    color = status_colors.get(status, "#A78BFA")
    pct = min((current / target * 100) if target > 0 else 0, 100)

    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.06);
            border-radius: 999px;
            height: 8px;
            overflow: hidden;
            margin: 0.75rem 0;
        ">
            <div style="
                height: 100%;
                width: {max(pct, 0.5):.1f}%;
                border-radius: 999px;
                background: {color};
                transition: width 0.6s ease;
            "></div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_status_class(pct: float) -> str:
    """Return status class based on percentage."""
    if pct >= 100:
        return "success"
    elif pct >= 75:
        return "warning"
    else:
        return "error"
