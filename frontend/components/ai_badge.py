"""
WorkFlow — AI Confidence Badge Component
Renders premium, styled HTML badges for AI logs.
"""
import streamlit as st


def render_confidence_badge(confidence: str, feedback: str = "") -> None:
    """Renders a gorgeous custom HTML badge based on AI confidence."""
    colors = {
        "High": {
            "bg": "rgba(16, 185, 129, 0.15)",
            "border": "#10B981",
            "text": "#34D399",
            "icon": "🛡️",
        },
        "Medium": {
            "bg": "rgba(245, 158, 11, 0.15)",
            "border": "#F59E0B",
            "text": "#FBBF24",
            "icon": "⚠️",
        },
        "Low": {
            "bg": "rgba(239, 68, 68, 0.15)",
            "border": "#EF4444",
            "text": "#FCA5A5",
            "icon": "🚨",
        },
        "Pending": {
            "bg": "rgba(107, 114, 128, 0.15)",
            "border": "#6B7280",
            "text": "#9CA3AF",
            "icon": "⏳",
        },
    }

    style = colors.get(confidence, colors["Pending"])

    badge_html = f"""
    <div style="
        display: inline-flex;
        align-items: center;
        background-color: {style['bg']};
        border: 1px solid {style['border']};
        color: {style['text']};
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        font-family: inherit;
        margin: 4px 0;
    ">
        <span style="margin-right: 6px;">{style['icon']}</span>
        AI Confidence: {confidence}
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)
    if feedback:
        st.markdown(
            f"<div style='font-style: italic; color: #94A3B8; font-size: 0.9rem; margin-top: 4px;'>Feedback: {feedback}</div>",
            unsafe_allow_html=True,
        )
