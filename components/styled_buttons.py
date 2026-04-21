"""Custom styled buttons that actually work with Streamlit"""

import streamlit as st


def html_button_group(buttons_config: list):
    """Render HTML buttons that bypass Streamlit's CSS completely.

    Args:
        buttons_config: List of dicts with:
            - label: button text
            - key: unique identifier
            - icon: optional icon symbol
    """

    html = '<div style="display: flex; gap: 8px; width: 100%;">'

    for btn in buttons_config:
        label = btn.get("label", "Button")
        key = btn.get("key", label)
        icon = btn.get("icon", "")

        icon_span = f'<span style="margin-right: 4px; font-size: 14px;">{icon}</span>' if icon else ""

        html += f'''
        <button
            onclick="alert('Button {key} clicked - use st.button as fallback')"
            style="
                flex: 1;
                background: #111633 !important;
                color: #FFFFFF !important;
                border: 1px solid #2A3555 !important;
                border-radius: 10px !important;
                padding: 8px 12px !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
                white-space: nowrap;
            "
            onmouseover="this.style.background='#1F2954'; this.style.borderColor='#7C5EFF'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.3)';"
            onmouseout="this.style.background='#111633'; this.style.borderColor='#2A3555'; this.style.boxShadow='none';"
        >
            {icon_span}{label}
        </button>
        '''

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
