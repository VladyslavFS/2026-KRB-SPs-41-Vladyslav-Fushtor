import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { apiGetSavedEvents, apiDeleteSavedEvent } from "../api/client";

export default function SavedEventsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    apiGetSavedEvents(token).then((res) => {
      if (res?.ok) {
        setItems(res.data.items || []);
      }
      setLoading(false);
    });
  }

  useEffect(() => { load(); }, [token]);

  async function handleDelete(eventId) {
    await apiDeleteSavedEvent(token, eventId);
    load();
  }

  return (
    <div className="main">
      <div className="page-header">
        <h2>Saved Events</h2>
        <p className="page-header__sub">Your bookmarked earthquakes</p>
      </div>

      {loading ? (
        <div className="spinner"></div>
      ) : items.length === 0 ? (
        <div className="info-box info-box--info">
          No saved events yet. Go to the Feed and save some.
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Event ID</th>
                  <th>Note</th>
                  <th>Saved at</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.event_id}>
                    <td><strong>{item.event_id}</strong></td>
                    <td>{item.note || "—"}</td>
                    <td>
                      {item.created_at
                        ? new Date(item.created_at).toISOString().slice(0, 19).replace("T", " ")
                        : "—"}
                    </td>
                    <td>
                      <button
                        className="btn btn--danger btn--sm"
                        onClick={() => handleDelete(item.event_id)}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
