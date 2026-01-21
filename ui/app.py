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
    hours = st.slider("Lookback (hours)", min_value=1, max_value=168, value=24)
    min_mag = st.number_input("Min magnitude", min_value=2.5, max_value=10.0, value=2.5, step=0.1)
    limit = st.selectbox("Rows", [50, 100, 200, 500], index=1)

query = """
SELECT
  time,
  mag,
  place,
  depth,
  latitude,
  longitude,
  net,
  status,
  updated,
  id
FROM ods.fct_earthquake_event
WHERE time >= now() - (%s || ' hours')::interval
  AND (mag IS NULL OR mag >= %s)
ORDER BY time DESC
LIMIT %s;
"""

try:
    with get_conn() as conn:
        df = pd.read_sql(query, conn, params=(hours, min_mag, limit))

    st.subheader("Latest events")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(f"Rows shown: {len(df)}")

except Exception as e:
    st.error("Cannot load data from DWH")
    st.exception(e)
