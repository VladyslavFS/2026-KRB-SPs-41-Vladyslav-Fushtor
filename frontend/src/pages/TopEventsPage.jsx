import { useEffect, useState } from "react";
import { apiGetTopDailyDays, apiGetTopDaily } from "../api/client";
import KpiCard from "../components/KpiCard";
import EventMap from "../components/EventMap";
import EventTable from "../components/EventTable";

export default function TopEventsPage() {
  const [days, setDays] = useState([]);
  const [selectedDay, setSelectedDay] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGetTopDailyDays().then((res) => {
      if (res?.ok && res.data.length > 0) {
        setDays(res.data);
        setSelectedDay(res.data[0]);
      }
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!selectedDay) return;
    setLoading(true);
    apiGetTopDaily(selectedDay).then((res) => {
      if (res?.ok) {
        setEvents(res.data);
      }
      setLoading(false);
    });
  }, [selectedDay]);

  const maxMag = events.length
    ? Math.max(...events.filter((e) => e.mag != null).map((e) => e.mag))
    : null;

  return (
    <div className="main">
      <div className="page-header">
        <h2>Top Events Daily</h2>
        <p className="page-header__sub">Strongest earthquakes ranked by day</p>
      </div>

      {days.length === 0 && !loading ? (
        <div className="info-box info-box--info">
          No data yet. Run the pipeline first.
        </div>
      ) : (
        <>
          <div className="card">
            <div className="form-group">
              <label>Select day</label>
              <select
                className="form-select"
                value={selectedDay || ""}
                onChange={(e) => setSelectedDay(e.target.value)}
              >
                {days.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="kpi-row">
            <KpiCard label="Day" value={selectedDay} />
            <KpiCard label="Top events" value={events.length} />
            <KpiCard
              label="Max magnitude"
              value={maxMag != null && isFinite(maxMag) ? maxMag.toFixed(1) : "—"}
              variant="accent"
            />
          </div>

          {loading ? (
            <div className="spinner"></div>
          ) : (
            <>
              <EventMap events={events} />
              <EventTable events={events} />
            </>
          )}
        </>
      )}
    </div>
  );
}
