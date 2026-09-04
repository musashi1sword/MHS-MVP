import { useEffect, useRef, useState } from "react";
import { api, wsUrl } from "../api/client";
import { useToast, errorMessage } from "../components/Toast";
import type { Prescription } from "../api/types";

const NEXT: Record<string, { label: string; to: string }[]> = {
  pending: [
    { label: "Mark ready for pickup", to: "ready" },
    { label: "Out for delivery", to: "out_for_delivery" },
  ],
  ready: [{ label: "Mark dispensed", to: "dispensed" }],
  out_for_delivery: [{ label: "Mark dispensed", to: "dispensed" }],
};

export default function PharmacyBoard() {
  const [rows, setRows] = useState<Prescription[]>([]);
  const [flash, setFlash] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const toast = useToast();

  const load = () => api.get<Prescription[]>("/pharmacy/queue").then(setRows).catch(() => {});

  useEffect(() => {
    load();
    const ws = new WebSocket(wsUrl("/ws/pharmacy/status"));
    wsRef.current = ws;
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      setFlash(
        data.event === "prescription.sent"
          ? `New Rx for ${data.patient} → ${data.pharmacy}`
          : `Rx #${data.prescription} → ${data.status_display ?? data.status}`,
      );
      load();
      setTimeout(() => setFlash(null), 4000);
    };
    return () => ws.close();
  }, []);

  const advance = async (rx: Prescription, to: string) => {
    try {
      await api.post(`/pharmacy/prescriptions/${rx.id}/status`, { status: to });
      toast.success(`Rx #${rx.id} → ${to.replace(/_/g, " ")}.`);
      load();
    } catch (e) {
      toast.error(errorMessage(e, `Could not update Rx #${rx.id}.`));
    }
  };

  return (
    <>
      <h1>Pharmacy Board</h1>
      <p className="sub">Live queue of routed prescriptions. Updates over WebSocket in real time.</p>

      {flash && <div className="alert warn">{flash}</div>}

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Rx</th>
              <th>Patient</th>
              <th>Medications</th>
              <th>Pharmacy</th>
              <th>Fulfilment</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((rx) => (
              <tr key={rx.id}>
                <td>#{rx.id}</td>
                <td>{rx.patient_name}</td>
                <td className="muted">{rx.medication_list.join("; ")}</td>
                <td>{rx.pharmacy_name}</td>
                <td>{rx.fulfilment}</td>
                <td>
                  <span
                    className={`pill ${
                      rx.status === "ready" ? "ok" : rx.status === "dispensed" ? "" : "warn"
                    }`}
                  >
                    {rx.status.replace(/_/g, " ")}
                  </span>
                  {rx.allergen_alert_triggered && (
                    <span className="pill danger" style={{ marginLeft: 6 }}>
                      allergy override
                    </span>
                  )}
                </td>
                <td>
                  {(NEXT[rx.status] ?? []).map((n) => (
                    <button
                      key={n.to}
                      className="secondary"
                      style={{ marginRight: 6, marginBottom: 4 }}
                      onClick={() => advance(rx, n.to)}
                    >
                      {n.label}
                    </button>
                  ))}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="muted">
                  Queue is empty.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
