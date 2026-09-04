import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useToast, errorMessage } from "../components/Toast";
import type {
  Appointment,
  Consultation,
  Medication,
  Prescription,
  SafetyReport,
} from "../api/types";

interface Draft {
  medicationId: number;
  dose: string;
  frequency: string;
  duration: string;
}

export default function ProviderConsole() {
  const [queue, setQueue] = useState<Appointment[]>([]);
  const [active, setActive] = useState<Appointment | null>(null);
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [formulary, setFormulary] = useState<Medication[]>([]);

  const [note, setNote] = useState({ subjective: "", objective: "", assessment: "", plan: "" });
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [safety, setSafety] = useState<SafetyReport | null>(null);
  const [rx, setRx] = useState<Prescription | null>(null);
  const [override, setOverride] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const toast = useToast();

  const loadQueue = () =>
    api.get<Appointment[]>("/appointments/queue").then(setQueue).catch(() => {});

  useEffect(() => {
    loadQueue();
    api.get<Medication[]>("/formulary").then(setFormulary);
    const t = setInterval(loadQueue, 4000);
    return () => clearInterval(t);
  }, []);

  const open = async (appt: Appointment) => {
    setActive(appt);
    setSafety(null);
    setRx(null);
    setOverride("");
    setMsg(null);
    try {
      const res = await api.post<{ consultation: Consultation }>("/consultations/start", {
        appointment: appt.id,
        mode: "video",
      });
      setConsultation(res.consultation);
      setNote({
        subjective: res.consultation.subjective,
        objective: res.consultation.objective,
        assessment: res.consultation.assessment,
        plan: res.consultation.plan,
      });
      setDrafts([]);
    } catch (e) {
      setActive(null);
      toast.error(errorMessage(e, "Could not open the consultation."));
    }
  };

  const saveNote = async () => {
    if (!consultation) return;
    try {
      await api.patch(`/consultations/${consultation.id}/note`, note);
      setMsg("Note saved.");
      toast.success("Note saved.");
    } catch (e) {
      toast.error(errorMessage(e, "Could not save the note."));
    }
  };

  const addDraft = () => {
    const first = formulary[0];
    if (first) setDrafts((d) => [...d, { medicationId: first.id, dose: "", frequency: "", duration: "" }]);
  };

  const medIds = useMemo(() => drafts.map((d) => d.medicationId), [drafts]);

  const runSafety = async () => {
    if (!active || medIds.length === 0) return;
    try {
      const report = await api.post<SafetyReport>("/prescriptions/check-allergy", {
        patient: active.patient,
        medications: medIds,
      });
      setSafety(report);
    } catch (e) {
      toast.error(errorMessage(e, "Safety check failed."));
    }
  };

  // Live check whenever the medication set changes.
  useEffect(() => {
    if (active && medIds.length) runSafety();
    else setSafety(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [medIds.join(","), active?.id]);

  const createRx = async () => {
    if (!consultation) return;
    try {
      const created = await api.post<Prescription>("/prescriptions", {
        consultation: consultation.id,
        fulfilment: "pickup",
        items: drafts.map((d) => ({
          medication: d.medicationId,
          dose: d.dose,
          frequency: d.frequency,
          duration: d.duration,
        })),
      });
      setRx(created);
      setMsg("Prescription created (draft). Send it to route to the pharmacy.");
      toast.success(`Prescription #${created.id} created (draft).`);
    } catch (e) {
      toast.error(errorMessage(e, "Could not create the prescription."));
    }
  };

  const sendRx = async () => {
    if (!rx) return;
    try {
      const sent = await api.post<Prescription>(`/prescriptions/${rx.id}/send`, {});
      setRx(sent);
      setMsg(`Routed to ${sent.pharmacy_name}. Status: ${sent.status}.`);
      toast.success(`Sent to ${sent.pharmacy_name}. Status: ${sent.status}.`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setMsg("Blocked by the safety layer. Enter an override reason to proceed.");
        toast.error("Blocked by the safety layer — enter an override reason to proceed.");
      } else {
        setMsg("Send failed.");
        toast.error(errorMessage(e, "Could not send the prescription to the pharmacy."));
      }
    }
  };

  const applyOverride = async () => {
    if (!rx || !override.trim()) return;
    try {
      await api.post(`/prescriptions/${rx.id}/override`, { reason: override });
      setMsg("Override recorded. You can send now.");
      toast.info("Override recorded.");
      await sendRx();
    } catch (e) {
      toast.error(errorMessage(e, "Could not record the override."));
    }
  };

  const completeVisit = async () => {
    if (!active) return;
    try {
      await api.post(`/appointments/${active.id}/complete`, {});
      setMsg("Visit completed.");
      toast.success("Visit completed.");
      setActive(null);
      setConsultation(null);
      loadQueue();
    } catch (e) {
      toast.error(errorMessage(e, "Could not complete the visit."));
    }
  };

  return (
    <>
      <h1>Provider Console</h1>
      <p className="sub">Queue, video visit, clinical note, and e-prescribing with the safety layer.</p>

      <div className="grid cols-2">
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Queue ({queue.length})</h2>
          <table>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Triage</th>
                <th>Symptom</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {queue.map((a) => (
                <tr key={a.id}>
                  <td>{a.patient_name}</td>
                  <td>
                    <span className={`pill ${a.triage.acuity === "routine" ? "ok" : "warn"}`}>
                      P{a.triage.priority_level}
                    </span>
                  </td>
                  <td className="muted">{a.symptom_note.slice(0, 40)}</td>
                  <td>
                    <button className="secondary" onClick={() => open(a)}>
                      Open
                    </button>
                  </td>
                </tr>
              ))}
              {queue.length === 0 && (
                <tr>
                  <td colSpan={4} className="muted">
                    No one waiting.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {active && (
          <div className="card">
            <h2 style={{ marginTop: 0 }}>{active.patient_name}</h2>
            <div className="row">
              <Link to={`/visit/${active.id}`}>
                <button className="secondary">Open video visit ↗</button>
              </Link>
              <span className="pill">{active.triage.acuity}</span>
            </div>
            <p className="muted" style={{ fontSize: 13 }}>
              Reported: {active.symptom_note}
            </p>
          </div>
        )}
      </div>

      {active && consultation && (
        <>
          <div className="card">
            <h2 style={{ marginTop: 0 }}>Clinical note</h2>
            {(["subjective", "objective", "assessment", "plan"] as const).map((f) => (
              <div key={f}>
                <label style={{ textTransform: "capitalize" }}>{f}</label>
                <textarea
                  value={note[f]}
                  onChange={(e) => setNote({ ...note, [f]: e.target.value })}
                />
              </div>
            ))}
            <button style={{ marginTop: 12 }} onClick={saveNote}>
              Save note
            </button>
          </div>

          <div className="card">
            <h2 style={{ marginTop: 0 }}>E-prescription</h2>
            {drafts.map((d, i) => (
              <div className="row" key={i} style={{ marginBottom: 8 }}>
                <select
                  value={d.medicationId}
                  onChange={(e) =>
                    setDrafts((x) =>
                      x.map((y, j) => (j === i ? { ...y, medicationId: Number(e.target.value) } : y)),
                    )
                  }
                  style={{ maxWidth: 240 }}
                >
                  {formulary.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <input
                  placeholder="dose"
                  value={d.dose}
                  onChange={(e) =>
                    setDrafts((x) => x.map((y, j) => (j === i ? { ...y, dose: e.target.value } : y)))
                  }
                  style={{ maxWidth: 90 }}
                />
                <input
                  placeholder="frequency"
                  value={d.frequency}
                  onChange={(e) =>
                    setDrafts((x) =>
                      x.map((y, j) => (j === i ? { ...y, frequency: e.target.value } : y)),
                    )
                  }
                  style={{ maxWidth: 110 }}
                />
                <input
                  placeholder="duration"
                  value={d.duration}
                  onChange={(e) =>
                    setDrafts((x) =>
                      x.map((y, j) => (j === i ? { ...y, duration: e.target.value } : y)),
                    )
                  }
                  style={{ maxWidth: 110 }}
                />
                <button
                  className="secondary"
                  onClick={() => setDrafts((x) => x.filter((_, j) => j !== i))}
                >
                  ✕
                </button>
              </div>
            ))}
            <button className="secondary" onClick={addDraft}>
              + Add medication
            </button>

            {safety && safety.alerts.length > 0 && (
              <div className={`alert ${safety.blocking ? "" : "warn"}`}>
                <strong>
                  {safety.blocking ? "⛔ Safety check — blocking" : "⚠ Safety check — review"}
                </strong>
                <ul style={{ margin: "8px 0 0 16px" }}>
                  {safety.alerts.map((a, i) => (
                    <li key={i}>
                      [{a.type} · {a.severity}] {a.medication} vs {a.against} — {a.detail}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {safety && safety.alerts.length === 0 && (
              <div className="alert warn" style={{ borderColor: "var(--ok)", background: "rgba(6,214,160,.12)" }}>
                ✓ No allergy or interaction alerts.
              </div>
            )}

            <div className="row" style={{ marginTop: 12 }}>
              <button onClick={createRx} disabled={drafts.length === 0}>
                Create prescription
              </button>
              {rx && (
                <button onClick={sendRx} className="secondary">
                  Send to pharmacy
                </button>
              )}
            </div>

            {rx && rx.status === "draft" && (rx.safety_report as SafetyReport)?.blocking && (
              <div style={{ marginTop: 12 }}>
                <label>Override reason (required to dispense despite the alert)</label>
                <textarea value={override} onChange={(e) => setOverride(e.target.value)} />
                <button className="danger" style={{ marginTop: 8 }} onClick={applyOverride}>
                  Override &amp; send
                </button>
              </div>
            )}

            {rx && (
              <p className="muted" style={{ fontSize: 13 }}>
                Rx #{rx.id} · {rx.status}
                {rx.pharmacy_name ? ` · ${rx.pharmacy_name}` : ""}
              </p>
            )}
          </div>

          <button onClick={completeVisit}>Complete visit</button>
        </>
      )}

      {msg && (
        <div className="alert warn" style={{ marginTop: 16 }}>
          {msg}
        </div>
      )}
    </>
  );
}
