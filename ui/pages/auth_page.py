import streamlit as st


def render():
    st.header("🔐 Authentication")

    api = st.session_state["api"]

    if st.session_state.get("access_token"):
        st.success(f"You are logged in as **{st.session_state.get('user_email', '—')}**")
        if st.button("Logout"):
            api.logout()
            st.session_state["access_token"] = None
            st.session_state["user_email"] = None
            st.rerun()
        return

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            if not email or not password:
                st.error("Please fill in all fields.")
            else:
                result = api.login(email, password)
                if result:
                    st.session_state["access_token"] = result["token"]["access_token"]
                    st.session_state["user_email"] = result["user"]["email"]
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_pass")
            reg_submitted = st.form_submit_button("Register")

        if reg_submitted:
            if not reg_email or not reg_password:
                st.error("Please fill in all fields.")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                result = api.register(reg_email, reg_password)
                if result:
                    st.session_state["access_token"] = result["token"]["access_token"]
                    st.session_state["user_email"] = result["user"]["email"]
                    st.success("Registered and logged in!")
                    st.rerun()
                else:
                    st.error("Registration failed. Email may already be in use.")
