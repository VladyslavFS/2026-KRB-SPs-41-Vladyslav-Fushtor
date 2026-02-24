export default function KpiCard({ label, value, variant }) {
  const cls = variant ? ` kpi-card__value--${variant}` : "";
  return (
    <div className="kpi-card">
      <div className="kpi-card__label">{label}</div>
      <div className={`kpi-card__value${cls}`}>{value ?? "—"}</div>
    </div>
  );
}
