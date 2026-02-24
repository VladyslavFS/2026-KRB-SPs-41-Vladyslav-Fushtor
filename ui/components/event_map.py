import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium


def render_event_map(events: list[dict], height: int = 600):
    """
    Renders a Folium map with clustered earthquake markers.
    Each event dict should have: latitude, longitude, place, mag, depth, time, url.
    """
    df = pd.DataFrame(events)
    if df.empty:
        st.info("No events to display on the map.")
        return

    df["latitude"] = pd.to_numeric(df.get("latitude"), errors="coerce")
    df["longitude"] = pd.to_numeric(df.get("longitude"), errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

    if df.empty:
        st.info("No events with valid coordinates.")
        return

    center_lat = float(df["latitude"].mean())
    center_lon = float(df["longitude"].mean())

    m = folium.Map(location=[center_lat, center_lon], zoom_start=2)
    cluster = MarkerCluster().add_to(m)

    for _, r in df.iterrows():
        place = r.get("place") or "Unknown"
        mag = r.get("mag")
        depth = r.get("depth")
        url = r.get("url")

        time_val = r.get("time")
        time_str = str(time_val)[:19] if time_val else "—"

        mag_str = f"{mag}" if mag is not None and not pd.isna(mag) else "—"
        depth_str = f"{depth}" if depth is not None and not pd.isna(depth) else "—"

        popup_html = f"""
        <div style="width:260px">
          <b>{place}</b><br/>
          <b>Magnitude:</b> {mag_str}<br/>
          <b>Depth:</b> {depth_str} km<br/>
          <b>Time (UTC):</b> {time_str}<br/>
          {"<a href='" + str(url) + "' target='_blank'>USGS link</a>" if url else ""}
        </div>
        """

        tooltip = f"{place} | M {mag}" if mag is not None and not pd.isna(mag) else place

        folium.Marker(
            location=[float(r["latitude"]), float(r["longitude"])],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip,
        ).add_to(cluster)

    st_folium(m, width=1200, height=height)
