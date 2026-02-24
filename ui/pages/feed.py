import pandas as pd
import streamlit as st

from ui.components.event_map import render_event_map
from ui.components.kpi_card import kpi_card


def render():
    st.header("🌍 Earthquake Feed")

    # ── Sidebar filters ───────────────────────────────────────────────────────

    with st.sidebar:
        st.subheader("Filters")
        lookback_hours = st.slider("Lookback (hours)", 1, 168, 24)
        mag_min = st.number_input("Min magnitude", 0.0, 10.0, 0.0, 0.1)
        severity = st.selectbox("Severity", ["ALL", "LOW", "MEDIUM", "HIGH"], index=0)
        limit = st.selectbox("Rows", [50, 100, 200, 500, 1000], index=2)

    # ── Fetch data ────────────────────────────────────────────────────────────

    api = st.session_state["api"]
    data = api.get_events(
        hours=lookback_hours,
        mag_min=mag_min,
        severity=severity,
        limit=limit,
    )
    items = data.get("items", [])
    total = data.get("total", 0)

    # ── KPI row ───────────────────────────────────────────────────────────────

    df = pd.DataFrame(items)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Rows", f"{len(items)} / {total}")
    with c2:
        has_mag = not df.empty and "mag" in df.columns and df["mag"].notna().any()
        max_mag = df["mag"].max() if has_mag else None
        kpi_card(
            "Max magnitude",
            f"{max_mag:.2f}" if max_mag is not None else "—",
        )
    with c3:
        tsunami_cnt = (
            int((df["tsunami"] == 1).sum())
            if not df.empty and "tsunami" in df.columns
            else 0
        )
        kpi_card("Tsunami flagged", str(tsunami_cnt))
    with c4:
        high_cnt = (
            int((df["severity"] == "HIGH").sum())
            if not df.empty and "severity" in df.columns
            else 0
        )
        kpi_card("HIGH severity", str(high_cnt))

    # ── Map ───────────────────────────────────────────────────────────────────

    st.subheader("Interactive map")
    render_event_map(items)

    # ── Table with save button ────────────────────────────────────────────────

    st.subheader("Table")

    if st.session_state.get("access_token") and not df.empty:
        selected_idx = st.multiselect(
            "Select events to save ⭐",
            options=df.index.tolist(),
            format_func=lambda i: (
                f"{df.loc[i, 'event_id']} — "
                f"{df.loc[i, 'place']} (M {df.loc[i, 'mag']})"
            ),
        )
        if selected_idx and st.button("⭐ Save selected events"):
            saved_count = 0
            for i in selected_idx:
                event_id = df.loc[i, "event_id"]
                result = api.save_event(event_id=event_id)
                if result:
                    saved_count += 1
            st.success(f"Saved {saved_count} event(s)!")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("url")} if not df.empty else {},
    )
    st.caption(f"Showing: {len(items)} of {total}")
