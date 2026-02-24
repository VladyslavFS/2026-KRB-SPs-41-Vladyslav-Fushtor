import streamlit as st

from ui.api_client import EarthquakeAPIClient
from ui.pages import alert_rules, auth_page, feed, saved_events, top_events

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Earthquake Platform",
    page_icon="🌍",
    layout="wide",
)

# ── Session state init ────────────────────────────────────────────────────────

if "api" not in st.session_state:
    st.session_state["api"] = EarthquakeAPIClient()

if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

# Keep api_client in sync with session token
api: EarthquakeAPIClient = st.session_state["api"]
api.set_token(st.session_state["access_token"])


# ── Navigation ────────────────────────────────────────────────────────────────

public_pages = {
    "🌍 Feed": feed.render,
    "🏆 Top events": top_events.render,
}

auth_pages = {
    "⭐ Saved events": saved_events.render,
    "🔔 Alert rules": alert_rules.render,
}

all_pages = {**public_pages}

if st.session_state["access_token"]:
    all_pages.update(auth_pages)

all_pages["🔐 Auth"] = auth_page.render


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🌍 Earthquake Platform")
    page_name = st.radio("Navigation", list(all_pages.keys()), label_visibility="collapsed")

    st.divider()

    if st.session_state["access_token"]:
        st.success(f"👤 {st.session_state.get('user_email', 'User')}")
        if st.button("Logout", use_container_width=True):
            api.logout()
            st.session_state["access_token"] = None
            st.session_state["user_email"] = None
            st.rerun()
    else:
        st.info("Not logged in")


# ── Render selected page ──────────────────────────────────────────────────────

all_pages[page_name]()
