import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Metrics } from "../api/types";

function Stat({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="card metric">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

export default function MetricsDashboard() {
  const [m, setM] = useState<Metrics | null>(null);

  useEffect(() => {
    const load = () => api.get<Metrics>("/dashboard/metrics").then(setM).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  if (!m) return <p>Loading metrics…</p>;
  const c = m.funnel.conversion;

  return (
    <>
      <h1>Metrics</h1>
      <p className="sub">{m.note}</p>

      <h2>Funnel</h2>
      <div className="grid cols-4">
        <Stat value={m.funnel.bookings} label="Bookings" />
        <Stat value={m.funnel.completed_visits} label="Completed visits" />
        <Stat value={m.funnel.prescriptions_issued} label="Rx issued" />
        <Stat value={m.funnel.prescriptions_filled} label="Rx filled" />
      </div>
      <div className="grid cols-4">
        <Stat value={`${c.booking_to_visit_pct}%`} label="Booking → visit" />
        <Stat value={`${c.visit_to_rx_pct}%`} label="Visit → Rx" />
        <Stat value={`${c.rx_to_filled_pct}%`} label="Rx → filled" />
        <Stat value={`${c.booking_to_filled_pct}%`} label="Booking → filled" />
      </div>

      <h2>Speed</h2>
      <div className="grid cols-2">
        <Stat value={`${m.speed.avg_booking_to_provider_min} min`} label="Booking → provider" />
        <Stat value={`${m.speed.avg_rx_to_pharmacy_pickup_min} min`} label="Rx → pharmacy pickup" />
      </div>

      <h2>Unit economics</h2>
      <div className="grid cols-4">
        <Stat value={`$${m.unit_economics.revenue_per_consult_usd}`} label="Revenue / consult" />
        <Stat value={`$${m.unit_economics.cost_per_consult_usd}`} label="Cost / consult" />
        <Stat value={`$${m.unit_economics.contribution_margin_usd}`} label="Contribution margin" />
        <Stat value={`${m.unit_economics.pharmacy_margin_share_pct}%`} label="Pharmacy margin share" />
      </div>

      <h2>Retention</h2>
      <div className="grid cols-2">
        <Stat value={`${m.retention.return_within_90d_pct}%`} label="Return within 90 days" />
        <div className="card">
          <div className="label" style={{ marginBottom: 6 }}>
            Market wedge
          </div>
          <div style={{ fontSize: 13 }}>{m.market_wedge}</div>
        </div>
      </div>
    </>
  );
}
