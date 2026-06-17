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
  const [error, setError] = useState(null);

  // Filters
  const [hours, setHours] = useState(24);
  const [magMin, setMagMin] = useState(0);
  const [severity, setSeverity] = useState("ALL");
  const [limit, setLimit] = useState(200);

  useEffect(() => {
    // AbortController cancels in-flight requests when filters change quickly.
    // This prevents stale responses from overwriting fresher data (race condition fix).
    const controller = new AbortController();

    setLoading(true);
    setError(null);

    apiGetEvents({ hours, mag_min: magMin, severity, limit }, controller.signal).then((res) => {
      // res === null means the request was intentionally aborted — do nothing
      if (res === null) return;

      if (res.status === 429) {
        setError("Too many requests — slow down a bit and try again.");
        setLoading(false);
        return;
      }
      if (res?.ok) {
        setEvents(res.data.items || []);
        setTotal(res.data.total || 0);
      }
      setLoading(false);
    });

    // Cleanup: abort the previous in-flight request when the effect re-runs
    return () => controller.abort();
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
              {[
                { value: 1, label: "1h" },
                { value: 6, label: "6h" },
                { value: 12, label: "12h" },
                { value: 24, label: "24h (1d)" },
                { value: 48, label: "48h (2d)" },
                { value: 72, label: "72h (3d)" },
                { value: 168, label: "168h (7d)" },
                { value: 720, label: "720h (30d)" },
                { value: 2160, label: "2160h (90d)" },
                { value: 8760, label: "8760h (365d)" },
                { value: 0, label: "All time" },
              ].map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
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
              {[50, 100, 200, 500, 1000, 2000, 5000, 10000].map((n) => (
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

      {/* Error banner (rate limit or other API errors) */}
      {error && (
        <div className="card" style={{ borderColor: "var(--danger)", color: "var(--danger)", padding: "12px 16px" }}>
          ⚠️ {error}
        </div>
      )}

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
