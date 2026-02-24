import pandas as pd
import streamlit as st

from ui.components.event_map import render_event_map
from ui.components.kpi_card import kpi_card


def render():
    st.header("🏆 Top Events Daily")

    api = st.session_state["api"]

    # ── Day selector ──────────────────────────────────────────────────────────

    days = api.get_top_daily_days()
    if not days:
        st.info("No data in top events yet. Run the pipeline first.")
        return

    day = st.selectbox("Select day", days)

    # ── Fetch data ────────────────────────────────────────────────────────────

    events = api.get_top_daily(day)
    df = pd.DataFrame(events)

    if df.empty:
        st.info(f"No top events for {day}.")
        return

    # ── KPI row ───────────────────────────────────────────────────────────────

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Day", str(day))
    with c2:
        kpi_card("Events in top", str(len(df)))
    with c3:
        max_mag = df["mag"].max() if df["mag"].notna().any() else None
        kpi_card("Max magnitude", f"{max_mag:.2f}" if max_mag is not None else "—")

    # ── Map ───────────────────────────────────────────────────────────────────

    st.subheader("Map")
    render_event_map(events)

    # ── Table ─────────────────────────────────────────────────────────────────

    st.subheader("Table")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("url")} if not df.empty else {},
    )
