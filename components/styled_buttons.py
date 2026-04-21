"""Custom styled buttons that bypass Streamlit's CSS"""

import streamlit as st


def styled_header_button(label: str, icon: str = "", on_click=None, key: str = None, help_text: str = "") -> bool:
    """Create a styled header button with inline CSS (bypasses Streamlit CSS conflicts).

    Args:
        label: Button text
        icon: Material icon name (e.g., "refresh", "download")
        on_click: Callback function
        key: Session state key
        help_text: Hover tooltip

    Returns:
        True if clicked
    """

    icon_html = f'<span style="margin-right: 6px;">●</span>' if icon else ""

    html = f"""
    <button
        id="btn_{key or label}"
        onclick="document.getElementById('btn_{key or label}').click()"
        style="
            background: #111633 !important;
            color: #FFFFFF !important;
            border: 1px solid #2A3555 !important;
            border-radius: 10px !important;
            padding: 8px 16px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        "
        onmouseover="this.style.background='#1F2954'; this.style.borderColor='#7C5EFF';"
        onmouseout="this.style.background='#111633'; this.style.borderColor='#2A3555';"
        title="{help_text}"
    >
        {icon_html}{label}
    </button>
    """

    st.markdown(html, unsafe_allow_html=True)

    # Fallback: use Streamlit button but log issue
    return st.button(label, key=key, width="stretch", type="secondary", help=help_text, on_click=on_click)
