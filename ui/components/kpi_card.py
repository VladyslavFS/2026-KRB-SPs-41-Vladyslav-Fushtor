import streamlit as st


def kpi_card(label: str, value: str, help_text: str | None = None):
    with st.container(border=True):
        st.caption(label)
        st.subheader(value)
        if help_text:
            st.caption(help_text)
