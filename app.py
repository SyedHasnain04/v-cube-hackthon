"""
Streamlit Web Interface for Library Assistant

This file provides a web-based user interface for the Public Library
Information Assistant using Streamlit.
"""

import streamlit as st
from library_assistant import LibraryAssistant

# Page configuration
st.set_page_config(
    page_title="Library Explainer Bot",
    page_icon="📚",
    layout="centered"
)

# Initialize session state for the assistant
if "assistant" not in st.session_state:
    try:
        st.session_state.assistant = LibraryAssistant()
    except ValueError as e:
        st.error(f"❌ Configuration Error: {e}")
        st.stop()

# Header
st.markdown(
    """
    <h1 style="text-align:center;">📚 Public Library Services Explainer</h1>
    <p style="text-align:center; color:gray;">
    Get clear explanations about library rules, borrowing, and digital resources
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# Info card
st.info(
    "ℹ️ **This assistant only explains library services.**\n\n"
    "It cannot issue books, manage accounts, or perform transactions."
)

# Main container
with st.container():
    st.markdown("### ❓ Ask your question")
    user_input = st.text_input(
        "",
        placeholder="e.g. How many books can I borrow at once?"
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        ask_btn = st.button("📖 Get Explanation", use_container_width=True)

# Answer section
if ask_btn:
    if user_input.strip():
        with st.spinner("📚 Thinking..."):
            try:
                answer = st.session_state.assistant.get_response(user_input)
                st.markdown("### ✅ Explanation")
                st.success(answer)
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.warning("⚠️ Please enter a question before clicking the button.")

st.divider()

# Footer
st.markdown(
    """
    <p style="text-align:center; font-size:12px; color:gray;">
    Built with Streamlit & Gemini API • Educational Use Only
    </p>
    """,
    unsafe_allow_html=True
)
