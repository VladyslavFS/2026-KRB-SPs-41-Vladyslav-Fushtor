import os
import pandas as pd
import psycopg2
import streamlit as st


st.set_page_config(page_title="Earthquake Platform", layout="wide")
st.title("Earthquake Platform (Dev)")


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DWH_HOST", "localhost"),
        port=int(os.getenv("DWH_PORT", "5432")),
        dbname=os.getenv("DWH_DB", "earthquake"),
        user=os.getenv("DWH_USER", "postgres"),
        password=os.getenv("DWH_PASSWORD", "postgres"),
    )


def kpi_card(label: str, value: str, help_text: str | None = None):
    with st.container(border=True):
        st.caption(label)
        st.subheader(value)
        if help_text:
            st.caption(help_text)


with st.sidebar:
    st.header("Navigation")
    page = st.radio("Page", ["Feed", "Top events", "Catalog health"], index=0)

    st.header("Filters")
    lookback_hours = st.slider("Lookback (hours)", min_value=1, max_value=168, value=24)

    min_mag = st.number_input("Min magnitude", min_value=0.0, max_value=10.0, value=2.5, step=0.1)

    severity = st.selectbox("Severity", ["ALL", "LOW", "MEDIUM", "HIGH", "UNKNOWN"], index=0)

    status = st.text_input("Status contains (optional)", value="").strip()
    net = st.text_input("Net contains (optional)", value="").strip()

    limit = st.selectbox("Rows", [50, 100, 200, 500, 1000], index=2)


def build_feed_query():
    where = [
        "time >= now() - (%s || ' hours')::interval",
        "(mag IS NULL OR mag >= %s)",
    ]
    params = [lookback_hours, float(min_mag)]

    if severity != "ALL":
        where.append("severity = %s")
        params.append(severity)

    if status:
        where.append("COALESCE(status,'') ILIKE %s")
        params.append(f"%{status}%")

    if net:
        where.append("COALESCE(net,'') ILIKE %s")
        params.append(f"%{net}%")

    where_sql = " AND ".join(where)

    sql = f"""
    SELECT
      event_id,
      time,
      updated,
      ingested_at,
      mag,
      mag_type,
      depth,
      place,
      latitude,
      longitude,
      net,
      status,
      event_type,
      tsunami,
      severity,
      mag_bucket,
      depth_bucket,
      url
    FROM bi.event_feed
    WHERE {where_sql}
    ORDER BY time DESC
    LIMIT %s;
    """
    params.append(int(limit))
    return sql, tuple(params)


def render_feed(conn):
    sql, params = build_feed_query()
    df = pd.read_sql(sql, conn, params=params)

    st.subheader("Latest events (Feed)")

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Rows", str(len(df)))
    with col2:
        kpi_card("Max magnitude", f"{df['mag'].max():.2f}" if not df.empty and df["mag"].notna().any() else "—")
    with col3:
        tsunami_cnt = int((df["tsunami"] == 1).sum()) if not df.empty and "tsunami" in df.columns else 0
        kpi_card("Tsunami flagged", str(tsunami_cnt))
    with col4:
        high_cnt = int((df["severity"] == "HIGH").sum()) if not df.empty and "severity" in df.columns else 0
        kpi_card("HIGH severity", str(high_cnt))

    # Map (simple)
    st.subheader("Map (last events)")
    df_geo = df.dropna(subset=["latitude", "longitude"]).copy()
    if df_geo.empty:
        st.info("No points with valid latitude/longitude for the selected filters.")
    else:
        df_map = df_geo.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]]
        st.map(df_map)

    st.subheader("Table")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "url": st.column_config.LinkColumn("url"),
        },
    )
    st.caption(f"Showing: {len(df)} rows")


def render_top(conn):
    st.subheader("Top events daily")

    days = pd.read_sql(
        """
        SELECT DISTINCT day
        FROM bi.top_events_daily
        ORDER BY day DESC
        LIMIT 30;
        """,
        conn,
    )
    if days.empty:
        st.info("No rows in bi.top_events_daily yet. Run: make bi-marts DAYS=30")
        return

    day = st.selectbox("Day", days["day"].tolist())
    df = pd.read_sql(
        """
        SELECT
          day, rank, event_id, time, mag, depth, place, latitude, longitude, tsunami, net, status, url
        FROM bi.top_events_daily
        WHERE day = %s
        ORDER BY rank ASC;
        """,
        conn,
        params=(day,),
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Day", str(day))
    with col2:
        kpi_card("Events in Top", str(len(df)))
    with col3:
        kpi_card("Max magnitude (Top)", f"{df['mag'].max():.2f}" if not df.empty and df["mag"].notna().any() else "—")

    # Map
    st.subheader("Map (Top)")
    df_geo = df.dropna(subset=["latitude", "longitude"]).copy()
    if df_geo.empty:
        st.info("No valid geo points for this day.")
    else:
        st.map(df_geo.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]])

    st.subheader("Table")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "url": st.column_config.LinkColumn("url"),
        },
    )


def render_health(conn):
    st.subheader("Catalog health daily")

    df = pd.read_sql(
        """
        SELECT
          day,
          events_cnt,
          tsunami_cnt,
          max_mag,
          pct_missing_geo,
          pct_missing_mag,
          avg_update_delay_min,
          p95_update_delay_min,
          avg_ingest_lag_min,
          max_ingest_lag_min,
          dq_last_status,
          dq_last_run_at,
          dq_last_issues_count
        FROM bi.catalog_health_daily
        ORDER BY day DESC
        LIMIT 60;
        """,
        conn,
    )

    if df.empty:
        st.info("No rows in bi.catalog_health_daily yet. Run: make bi-marts DAYS=30")
        return

    latest = df.iloc[0]

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Latest day", str(latest["day"]))
    with c2:
        kpi_card("Events", str(int(latest["events_cnt"])))
    with c3:
        kpi_card("Max mag", f"{float(latest['max_mag']):.2f}" if latest["max_mag"] is not None else "—")
    with c4:
        kpi_card("Avg ingest lag (min)", f"{float(latest['avg_ingest_lag_min']):.1f}" if latest["avg_ingest_lag_min"] is not None else "—")
    with c5:
        dq_status = latest["dq_last_status"] if latest["dq_last_status"] is not None else "—"
        issues_cnt = latest["dq_last_issues_count"] if latest["dq_last_issues_count"] is not None else "—"
        kpi_card("DQ last", f"{dq_status} (issues: {issues_cnt})")

    st.divider()

    st.subheader("Trends")

    # Charts: Streamlit can render line charts from a DataFrame indexed by day
    df_trend = df.sort_values("day").set_index("day")

    t1, t2 = st.columns(2)
    with t1:
        st.caption("Events count")
        st.line_chart(df_trend[["events_cnt"]])

        st.caption("Max magnitude")
        if "max_mag" in df_trend.columns:
            st.line_chart(df_trend[["max_mag"]])

    with t2:
        st.caption("Missingness")
        st.line_chart(df_trend[["pct_missing_geo", "pct_missing_mag"]])

        st.caption("Ingest lag (minutes)")
        st.line_chart(df_trend[["avg_ingest_lag_min", "max_ingest_lag_min"]])

    st.subheader("Table")
    st.dataframe(df, use_container_width=True, hide_index=True)


try:
    with get_conn() as conn:
        if page == "Feed":
            render_feed(conn)
        elif page == "Top events":
            render_top(conn)
        else:
            render_health(conn)

except Exception as e:
    st.error("Cannot load data from DWH")
    st.exception(e)
