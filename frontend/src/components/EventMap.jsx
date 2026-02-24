import { useState } from "react";
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

export default function EventMap({ events = [], onSave }) {
  const [savedIds, setSavedIds] = useState(new Set());
  const [noteFor, setNoteFor] = useState(null);   // event_id being noted
  const [noteText, setNoteText] = useState("");
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
                <div style={{ fontFamily: "var(--font)", fontSize: 12, lineHeight: 1.6 }}>
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
                  {onSave && e.event_id && (
                    <div style={{ marginTop: 6 }}>
                      {savedIds.has(e.event_id) ? (
                        <span style={{ color: "#5a9a6b", fontSize: 11 }}>✓ saved</span>
                      ) : noteFor === e.event_id ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                          <input
                            type="text"
                            placeholder="Note (optional)"
                            value={noteText}
                            onChange={(ev) => setNoteText(ev.target.value)}
                            style={{
                              fontSize: 11,
                              padding: "3px 6px",
                              border: "1px solid #555",
                              borderRadius: 3,
                              background: "#2a2a2a",
                              color: "#eee",
                              width: "100%",
                            }}
                          />
                          <div style={{ display: "flex", gap: 4 }}>
                            <button
                              onClick={() => {
                                onSave(e.event_id, noteText || undefined);
                                setSavedIds((prev) => new Set(prev).add(e.event_id));
                                setNoteFor(null);
                                setNoteText("");
                              }}
                              style={{
                                background: "#d4a843",
                                color: "#111",
                                border: "none",
                                borderRadius: 3,
                                padding: "2px 8px",
                                fontSize: 10,
                                fontWeight: 600,
                                cursor: "pointer",
                              }}
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => { setNoteFor(null); setNoteText(""); }}
                              style={{
                                background: "transparent",
                                color: "#999",
                                border: "1px solid #555",
                                borderRadius: 3,
                                padding: "2px 8px",
                                fontSize: 10,
                                cursor: "pointer",
                              }}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => setNoteFor(e.event_id)}
                          style={{
                            background: "#d4a843",
                            color: "#111",
                            border: "none",
                            borderRadius: 4,
                            padding: "3px 10px",
                            fontSize: 11,
                            fontWeight: 600,
                            cursor: "pointer",
                          }}
                        >
                          Save
                        </button>
                      )}
                    </div>
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
