import streamlit as st


def require_auth():
    """
    Call at the top of any protected page.
    Stops execution and shows a warning if user is not authenticated.
    """
    if not st.session_state.get("access_token"):
        st.warning("🔒 Please log in to access this page.")
        st.stop()
