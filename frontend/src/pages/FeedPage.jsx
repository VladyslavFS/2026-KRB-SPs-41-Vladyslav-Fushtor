import { useEffect, useState } from "react";
import { apiGetEvents, apiSaveEvent } from "../api/client";
import { useAuth } from "../context/AuthContext";
import KpiCard from "../components/KpiCard";
import EventMap from "../components/EventMap";
import EventTable from "../components/EventTable";

export default function FeedPage() {
  const { token } = useAuth();
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [hours, setHours] = useState(24);
  const [magMin, setMagMin] = useState(0);
  const [severity, setSeverity] = useState("ALL");
  const [limit, setLimit] = useState(200);

  useEffect(() => {
    setLoading(true);
    apiGetEvents({ hours, mag_min: magMin, severity, limit }).then((res) => {
      if (res?.ok) {
        setEvents(res.data.items || []);
        setTotal(res.data.total || 0);
      }
      setLoading(false);
    });
  }, [hours, magMin, severity, limit]);

  // Computed stats
  const maxMag = events.length
    ? Math.max(...events.filter((e) => e.mag != null).map((e) => e.mag))
    : null;
  const tsunamiCount = events.filter((e) => e.tsunami === 1).length;
  const highCount = events.filter((e) => e.severity === "HIGH").length;

  return (
    <div className="main">
      <div className="page-header">
        <h2>Earthquake Feed</h2>
        <p className="page-header__sub">Real-time seismic activity monitoring</p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="card__title">Filters</div>
        <div className="form-row">
          <div className="form-group">
            <label>Lookback hours</label>
            <select
              className="form-select"
              value={hours}
              onChange={(e) => setHours(Number(e.target.value))}
            >
              {[1, 6, 12, 24, 48, 72, 168].map((h) => (
                <option key={h} value={h}>
                  {h}h{h >= 24 ? ` (${h / 24}d)` : ""}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Min magnitude</label>
            <input
              className="form-input"
              type="number"
              min="0"
              max="10"
              step="0.5"
              value={magMin}
              onChange={(e) => setMagMin(Number(e.target.value))}
            />
          </div>
          <div className="form-group">
            <label>Severity</label>
            <select
              className="form-select"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
            >
              <option value="ALL">All</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </select>
          </div>
          <div className="form-group">
            <label>Limit</label>
            <select
              className="form-select"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            >
              {[50, 100, 200, 500, 1000].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="kpi-row">
        <KpiCard label="Events shown" value={`${events.length} / ${total}`} />
        <KpiCard
          label="Max magnitude"
          value={maxMag != null && isFinite(maxMag) ? maxMag.toFixed(1) : "—"}
          variant="accent"
        />
        <KpiCard
          label="Tsunami flagged"
          value={tsunamiCount}
          variant={tsunamiCount > 0 ? "danger" : undefined}
        />
        <KpiCard label="High severity" value={highCount} variant={highCount > 0 ? "danger" : undefined} />
      </div>

      {loading ? (
        <div className="spinner"></div>
      ) : (
        <>
          <EventMap
            events={events}
            onSave={token ? (eventId, note) => apiSaveEvent(token, eventId, note) : undefined}
          />
          <EventTable events={events} showSave />
          <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 8 }}>
            Showing {events.length} of {total} events
          </p>
        </>
      )}
    </div>
  );
}
