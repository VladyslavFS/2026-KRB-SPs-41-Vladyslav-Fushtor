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
    st.write("DB connection")
    st.code(
        f"{os.getenv('DWH_HOST')}:{os.getenv('DWH_PORT')} db={os.getenv('DWH_DB')}",
        language="text",
    )

try:
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM public.app_heartbeat", conn)
    st.success("Connected to DWH ✅")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error("Cannot connect to DWH")
    st.exception(e)
