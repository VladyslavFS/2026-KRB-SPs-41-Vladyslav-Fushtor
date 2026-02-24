import streamlit as st

from ui.components.auth_guard import require_auth


def render():
    require_auth()

    st.header("🔔 My Alert Rules")

    api = st.session_state["api"]
    data = api.get_alert_rules(limit=100)
    items = data.get("items", [])

    # ── Create new rule ───────────────────────────────────────────────────────

    with st.expander("➕ Create new alert rule", expanded=not items):
        with st.form("create_rule"):
            name = st.text_input("Rule name", placeholder="e.g. Strong earthquakes in Japan")
            c1, c2 = st.columns(2)
            with c1:
                min_mag = st.number_input(
                    "Min magnitude", 0.0, 10.0, 5.0, 0.1,
                )
            with c2:
                max_depth = st.number_input(
                    "Max depth (km)", 0.0, 700.0, 100.0, 10.0,
                )
            region = st.text_input(
                "Region keyword (optional)",
                placeholder="e.g. Japan, California",
            )
            submitted = st.form_submit_button("Create rule")

        if submitted:
            if not name:
                st.error("Rule name is required.")
            else:
                result = api.create_alert_rule(
                    name=name,
                    min_magnitude=min_mag if min_mag > 0 else None,
                    max_depth_km=max_depth if max_depth > 0 else None,
                    region=region or None,
                )
                if result:
                    st.success(f"Rule '{name}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create rule.")

    # ── Existing rules ────────────────────────────────────────────────────────

    if not items:
        st.info("No alert rules yet. Create one above!")
        return

    st.caption(f"Total rules: {data.get('total', 0)}")

    for item in items:
        rule_id = item["alert_rule_id"]
        status_icon = "✅" if item["is_active"] else "⏸️"

        with st.container(border=True):
            col_name, col_toggle, col_del = st.columns([4, 1, 1])

            with col_name:
                st.markdown(f"**{status_icon} {item['name']}**")
                details = []
                if item.get("min_magnitude") is not None:
                    details.append(f"Mag ≥ {item['min_magnitude']}")
                if item.get("max_depth_km") is not None:
                    details.append(f"Depth ≤ {item['max_depth_km']} km")
                if item.get("region"):
                    details.append(f"Region: {item['region']}")
                st.caption(" · ".join(details) if details else "No filters set")

            with col_toggle:
                new_state = not item["is_active"]
                label = "Pause" if item["is_active"] else "Enable"
                if st.button(label, key=f"toggle_{rule_id}"):
                    api.update_alert_rule(rule_id, is_active=new_state)
                    st.rerun()

            with col_del:
                if st.button("🗑️", key=f"del_rule_{rule_id}"):
                    if api.delete_alert_rule(rule_id):
                        st.success(f"Deleted rule '{item['name']}'")
                        st.rerun()
                    else:
                        st.error("Failed to delete.")
