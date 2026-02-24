import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";

const SEVERITY_COLORS = {
  HIGH: "#c75c2e",
  MEDIUM: "#d4a843",
  LOW: "#5a9a6b",
};

function getRadius(mag) {
  if (mag == null) return 4;
  if (mag >= 6) return 12;
  if (mag >= 4) return 8;
  return 5;
}

export default function EventMap({ events = [] }) {
  const valid = events.filter(
    (e) => e.latitude != null && e.longitude != null
  );

  if (valid.length === 0) {
    return (
      <div className="card">
        <div className="info-box info-box--info">No events to display on the map.</div>
      </div>
    );
  }

  const center = [
    valid.reduce((s, e) => s + e.latitude, 0) / valid.length,
    valid.reduce((s, e) => s + e.longitude, 0) / valid.length,
  ];

  return (
    <div className="map-container">
      <MapContainer center={center} zoom={2} scrollWheelZoom={true}>
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {valid.map((e, i) => {
          const color = SEVERITY_COLORS[e.severity] || "#9a938a";
          return (
            <CircleMarker
              key={e.event_id || i}
              center={[e.latitude, e.longitude]}
              radius={getRadius(e.mag)}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.6,
                weight: 1,
              }}
            >
              <Popup>
                <div style={{ fontFamily: "var(--font)", fontSize: 12 }}>
                  <strong>{e.place || "Unknown"}</strong>
                  <br />
                  Mag: {e.mag ?? "—"} · Depth: {e.depth ?? "—"} km
                  <br />
                  {e.time ? new Date(e.time).toUTCString() : ""}
                  {e.url && (
                    <>
                      <br />
                      <a href={e.url} target="_blank" rel="noreferrer">
                        USGS →
                      </a>
                    </>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
