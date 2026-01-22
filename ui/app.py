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

with st.sidebar:
    st.header("Filters")
    page = st.radio("Page", ["Latest", "Map", "Data Quality"])
    hours = st.slider("Lookback (hours)", min_value=1, max_value=168, value=24)
    min_mag = st.number_input("Min magnitude", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
    limit = st.selectbox("Rows", [50, 100, 200, 500], index=1)

try:
    with get_conn() as conn:
        if page == "Latest":
            df = pd.read_sql(
                """
                SELECT
                  time, mag, place, depth, latitude, longitude, net, status, updated, id
                FROM ods.fct_earthquake_event
                WHERE time >= now() - (%s || ' hours')::interval
                  AND (mag IS NULL OR mag >= %s)
                ORDER BY time DESC
                LIMIT %s;
                """,
                conn,
                params=(hours, min_mag, limit),
            )

            st.subheader("Latest events")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Rows shown: {len(df)}")

        elif page == "Map":
            df_map = pd.read_sql(
                """
                SELECT latitude, longitude, mag, time, place
                FROM ods.fct_earthquake_event
                WHERE time >= now() - (%s || ' hours')::interval
                  AND latitude IS NOT NULL AND longitude IS NOT NULL
                  AND (mag IS NULL OR mag >= %s)
                ORDER BY time DESC
                LIMIT 5000;
                """,
                conn,
                params=(hours, min_mag),
            )

            st.subheader("Map")
            st.map(df_map.rename(columns={"latitude": "lat", "longitude": "lon"}))
            st.dataframe(df_map, use_container_width=True, hide_index=True)

        else:  # Data Quality
            runs = pd.read_sql(
                """
                SELECT run_id, run_at, window_start, window_end, status, total_rows, issues_count
                FROM ods.dq_run
                ORDER BY run_at DESC
                LIMIT 50;
                """,
                conn,
            )

            st.subheader("Data Quality runs")
            st.dataframe(runs, use_container_width=True, hide_index=True)

            if not runs.empty:
                selected = st.selectbox("Run id", runs["run_id"].tolist())
                issues = pd.read_sql(
                    """
                    SELECT issue_type, severity, message, sample_ids, created_at
                    FROM ods.dq_issue
                    WHERE run_id = %s
                    ORDER BY issue_id DESC;
                    """,
                    conn,
                    params=(int(selected),),
                )
                st.subheader("Issues")
                st.dataframe(issues, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Cannot load data from DWH")
    st.exception(e)
