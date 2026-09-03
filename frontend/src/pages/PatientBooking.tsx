import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Appointment, Slot } from "../api/types";

export default function PatientBooking() {
  const nav = useNavigate();
  const [slots, setSlots] = useState<Slot[]>([]);
  const [symptom, setSymptom] = useState("Sore throat and mild fever since yesterday.");
  const [slotId, setSlotId] = useState<number | null>(null);
  const [durationDays, setDurationDays] = useState(2);
  const [appt, setAppt] = useState<Appointment | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<Slot[]>("/slots").then((s) => {
      setSlots(s);
      if (s[0]) setSlotId(s[0].id);
    });
  }, []);

  const book = async () => {
    if (!slotId) return;
    setBusy(true);
    try {
      const a = await api.post<Appointment>("/appointments", {
        slot: slotId,
        symptom_note: symptom,
        mode: "video",
        intake: {},
      });
      setAppt(a);
    } finally {
      setBusy(false);
    }
  };

  const submitIntake = async () => {
    if (!appt) return;
    setBusy(true);
    try {
      const a = await api.post<Appointment>(`/appointments/${appt.id}/intake`, {
        intake: { duration_days: durationDays, completed: true },
      });
      setAppt(a);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1>Book &amp; Intake</h1>
      <p className="sub">Log a symptom, pick a same-day slot, complete a quick intake.</p>

      {!appt && (
        <div className="card">
          <h2 style={{ marginTop: 0 }}>1 · Symptom &amp; slot</h2>
          <label>What's going on?</label>
          <textarea value={symptom} onChange={(e) => setSymptom(e.target.value)} />
          <label>Same-day slots</label>
          <select value={slotId ?? ""} onChange={(e) => setSlotId(Number(e.target.value))}>
            {slots.map((s) => (
              <option key={s.id} value={s.id}>
                {new Date(s.start).toLocaleString()} — {s.provider_name} ({s.clinic_name})
              </option>
            ))}
          </select>
          {slots.length === 0 && <p className="muted">No open slots — seed demo data first.</p>}
          <button style={{ marginTop: 14 }} onClick={book} disabled={busy || !slotId}>
            Book appointment
          </button>
        </div>
      )}

      {appt && (
        <>
          <div className="card">
            <h2 style={{ marginTop: 0 }}>2 · Quick intake</h2>
            <div className="row">
              <span className="pill">Status: {appt.status}</span>
              <span className={`pill ${appt.triage.acuity === "routine" ? "ok" : "warn"}`}>
                Triage: {appt.triage.acuity} (P{appt.triage.priority_level})
              </span>
            </div>
            <p className="muted" style={{ fontSize: 13 }}>
              AI-assisted triage (mock): {appt.triage.recommendation}
            </p>
            <label>How many days have you had symptoms?</label>
            <input
              type="number"
              value={durationDays}
              min={0}
              onChange={(e) => setDurationDays(Number(e.target.value))}
            />
            {appt.status !== "in_queue" ? (
              <button style={{ marginTop: 14 }} onClick={submitIntake} disabled={busy}>
                Submit intake &amp; join queue
              </button>
            ) : (
              <button style={{ marginTop: 14 }} onClick={() => nav(`/visit/${appt.id}`)}>
                Enter waiting room
              </button>
            )}
          </div>
        </>
      )}
    </>
  );
}
