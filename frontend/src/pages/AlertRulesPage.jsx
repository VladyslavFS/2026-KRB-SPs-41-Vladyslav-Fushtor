import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  apiGetAlertRules,
  apiCreateAlertRule,
  apiUpdateAlertRule,
  apiDeleteAlertRule,
} from "../api/client";

export default function AlertRulesPage() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [minMag, setMinMag] = useState(5);
  const [maxDepth, setMaxDepth] = useState(100);
  const [region, setRegion] = useState("");

  function load() {
    setLoading(true);
    apiGetAlertRules(token).then((res) => {
      if (res?.ok) {
        setItems(res.data.items || []);
      }
      setLoading(false);
    });
  }

  useEffect(() => { load(); }, [token]);

  async function handleCreate(e) {
    e.preventDefault();
    if (!name.trim()) return;

    await apiCreateAlertRule(token, {
      name,
      min_magnitude: minMag > 0 ? minMag : null,
      max_depth_km: maxDepth > 0 ? maxDepth : null,
      region: region || null,
      is_active: true,
    });

    setName("");
    setMinMag(5);
    setMaxDepth(100);
    setRegion("");
    setShowForm(false);
    load();
  }

  async function handleToggle(rule) {
    await apiUpdateAlertRule(token, rule.alert_rule_id, {
      is_active: !rule.is_active,
    });
    load();
  }

  async function handleDelete(ruleId) {
    await apiDeleteAlertRule(token, ruleId);
    load();
  }

  return (
    <div className="main">
      <div className="page-header flex justify-between items-center">
        <div>
          <h2>Alert Rules</h2>
          <p className="page-header__sub">Manage notification criteria</p>
        </div>
        <button
          className="btn btn--primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "New Rule"}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="card">
          <div className="card__title">Create Alert Rule</div>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label>Rule name</label>
              <input
                className="form-input"
                placeholder="e.g. Strong quakes in Japan"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Min magnitude</label>
                <input
                  className="form-input"
                  type="number"
                  min="0"
                  max="10"
                  step="0.5"
                  value={minMag}
                  onChange={(e) => setMinMag(Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label>Max depth (km)</label>
                <input
                  className="form-input"
                  type="number"
                  min="0"
                  max="700"
                  step="10"
                  value={maxDepth}
                  onChange={(e) => setMaxDepth(Number(e.target.value))}
                />
              </div>
            </div>
            <div className="form-group">
              <label>Region (optional)</label>
              <input
                className="form-input"
                placeholder="e.g. Japan, California"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn--primary">
              Create
            </button>
          </form>
        </div>
      )}

      {/* Rules list */}
      {loading ? (
        <div className="spinner"></div>
      ) : items.length === 0 ? (
        <div className="info-box info-box--info">
          No alert rules yet. Create one above.
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Name</th>
                  <th>Min Mag</th>
                  <th>Max Depth</th>
                  <th>Region</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((rule) => (
                  <tr key={rule.alert_rule_id}>
                    <td>
                      <span
                        className={`badge badge--${rule.is_active ? "low" : "medium"}`}
                      >
                        {rule.is_active ? "Active" : "Paused"}
                      </span>
                    </td>
                    <td><strong>{rule.name}</strong></td>
                    <td>{rule.min_magnitude ?? "—"}</td>
                    <td>{rule.max_depth_km ? `${rule.max_depth_km} km` : "—"}</td>
                    <td>{rule.region || "—"}</td>
                    <td>
                      <div className="flex gap-8">
                        <button
                          className="btn btn--ghost btn--sm"
                          onClick={() => handleToggle(rule)}
                        >
                          {rule.is_active ? "Pause" : "Enable"}
                        </button>
                        <button
                          className="btn btn--danger btn--sm"
                          onClick={() => handleDelete(rule.alert_rule_id)}
                        >
                          Delete
                        </button>
                      </div>
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
