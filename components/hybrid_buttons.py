"""Hybrid buttons: Streamlit logic + HTML styling"""

import streamlit as st


def hybrid_button(label: str, key: str, icon: str = "", help_text: str = ""):
    """Render a button with Streamlit logic but custom HTML styling.

    Creates an invisible st.button (for logic) + visible HTML button (for looks).
    Clicking HTML button triggers the hidden Streamlit button via JS.

    Args:
        label: Button text
        key: Unique key for this button
        icon: Optional icon (emoji or symbol)
        help_text: Tooltip text

    Returns:
        True if button was clicked
    """

    # Create hidden Streamlit button (handles logic)
    clicked = st.button(
        label,
        key=f"{key}_hidden",
        use_container_width=True,
        type="secondary",
        help=help_text,
    )

    # Hide the Streamlit button with CSS
    st.markdown(
        f"""
        <script>
        // Find and hide the button that we just created
        setTimeout(() => {{
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {{
                if (btn.textContent.includes('{label}')) {{
                    btn.style.display = 'none';
                    btn.setAttribute('data-hybrid-key', '{key}_hidden');
                    break;
                }}
            }}
        }}, 100);
        </script>
        """,
        unsafe_allow_html=True
    )

    # Render custom HTML button
    icon_html = f'<span style="margin-right: 6px;">{icon}</span>' if icon else ""

    st.markdown(
        f"""
        <button
            class="hybrid-btn"
            data-hybrid-trigger="{key}_hidden"
            title="{help_text}"
            style="
                background: #111633 !important;
                color: #FFFFFF !important;
                border: 1px solid #2A3555 !important;
                border-radius: 10px !important;
                padding: 8px 16px !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
                width: 100% !important;
                white-space: nowrap !important;
            "
            onmouseover="this.style.background='#1F2954'; this.style.borderColor='#7C5EFF'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.3)';"
            onmouseout="this.style.background='#111633'; this.style.borderColor='#2A3555'; this.style.boxShadow='none';"
            onclick="triggerHybridButton('{key}_hidden')"
        >
            {icon_html}{label}
        </button>

        <script>
        function triggerHybridButton(key) {{
            // Find hidden button by data attribute
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {{
                if (btn.getAttribute('data-hybrid-key') === key) {{
                    btn.click();
                    return;
                }}
            }}
            // Fallback: try by textContent
            for (let btn of buttons) {{
                if (btn.getAttribute('data-hybrid-key') === key || btn.getAttribute('data-testid')?.includes(key)) {{
                    btn.click();
                    break;
                }}
            }}
        }}
        </script>
        """,
        unsafe_allow_html=True
    )

    return clicked
