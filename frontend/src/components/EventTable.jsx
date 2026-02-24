import { useAuth } from "../context/AuthContext";
import { apiSaveEvent } from "../api/client";
import { useState } from "react";

function SeverityBadge({ severity }) {
  if (!severity) return null;
  const cls = severity === "HIGH" ? "high" : severity === "MEDIUM" ? "medium" : "low";
  return <span className={`badge badge--${cls}`}>{severity}</span>;
}

export default function EventTable({ events = [], showSave = false }) {
  const { token } = useAuth();
  const [savedIds, setSavedIds] = useState(new Set());

  async function handleSave(eventId) {
    const res = await apiSaveEvent(token, eventId);
    if (res?.ok) {
      setSavedIds((prev) => new Set(prev).add(eventId));
    }
  }

  if (events.length === 0) {
    return (
      <div className="info-box info-box--info">No events found.</div>
    );
  }

  return (
    <div className="card">
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Time (UTC)</th>
              <th>Place</th>
              <th>Mag</th>
              <th>Depth</th>
              <th>Severity</th>
              <th>Net</th>
              <th>Link</th>
              {showSave && token && <th></th>}
            </tr>
          </thead>
          <tbody>
            {events.map((e, i) => (
              <tr key={e.event_id || i}>
                <td>{e.time ? new Date(e.time).toISOString().slice(0, 19).replace("T", " ") : "—"}</td>
                <td>{e.place || "—"}</td>
                <td><strong>{e.mag ?? "—"}</strong></td>
                <td>{e.depth != null ? `${e.depth} km` : "—"}</td>
                <td><SeverityBadge severity={e.severity} /></td>
                <td>{e.net || "—"}</td>
                <td>
                  {e.url ? (
                    <a href={e.url} target="_blank" rel="noreferrer">USGS</a>
                  ) : "—"}
                </td>
                {showSave && token && (
                  <td>
                    {savedIds.has(e.event_id) ? (
                      <span style={{ color: "var(--success)", fontSize: 12 }}>saved</span>
                    ) : (
                      <button
                        className="btn btn--ghost btn--sm"
                        onClick={() => handleSave(e.event_id)}
                      >
                        Save
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
