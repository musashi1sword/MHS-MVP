import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth";
import type { Consultation, JoinInfo } from "../api/types";
import { useVideoRoom } from "../video/useVideoRoom";

export default function Visit() {
  const { appointmentId } = useParams();
  const { user } = useAuth();
  const [join, setJoin] = useState<JoinInfo | null>(null);
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [mode, setMode] = useState<"webrtc" | "managed">("webrtc");
  const [starting, setStarting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const room = useVideoRoom(join);

  const start = async () => {
    setStarting(true);
    setErr(null);
    try {
      const res = await api.post<{ consultation: Consultation; session_id: number; join: JoinInfo }>(
        "/consultations/start",
        { appointment: Number(appointmentId), mode: "video", video_provider: mode },
      );
      setConsultation(res.consultation);
      setJoin(res.join);
    } catch {
      setErr("Could not start the visit.");
    } finally {
      setStarting(false);
    }
  };

  useEffect(() => {
    return () => {
      if (consultation) api.post(`/consultations/${consultation.id}/end`).catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [consultation?.id]);

  return (
    <>
      <h1>Video Visit</h1>
      <p className="sub">
        Appointment #{appointmentId} · {user?.role === "patient" ? "Patient view" : "Provider view"}
      </p>

      {!join && (
        <div className="card">
          <label>Connection mode (dual-mode architecture)</label>
          <div className="row">
            <label className="row" style={{ margin: 0 }}>
              <input
                type="radio"
                style={{ width: "auto" }}
                checked={mode === "webrtc"}
                onChange={() => setMode("webrtc")}
              />{" "}
              Custom WebRTC (COTURN/STUN)
            </label>
            <label className="row" style={{ margin: 0 }}>
              <input
                type="radio"
                style={{ width: "auto" }}
                checked={mode === "managed"}
                onChange={() => setMode("managed")}
              />{" "}
              Managed API (Twilio/Chime)
            </label>
          </div>
          <button style={{ marginTop: 14 }} onClick={start} disabled={starting}>
            {starting ? "Connecting…" : "Join visit"}
          </button>
          {err && <div className="alert">{err}</div>}
        </div>
      )}

      {join && (
        <>
          <div className="card">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <div className="row">
                <span className="pill">{join.provider === "webrtc" ? "Custom WebRTC" : `Managed · ${join.vendor}`}</span>
                <span className={`pill ${room.state === "connected" ? "ok" : "warn"}`}>{room.state}</span>
                {join.provider === "managed" && (
                  <span className="pill">token issued {join.live ? "(live)" : "(mock)"}</span>
                )}
              </div>
              <button className="danger" onClick={room.hangUp}>
                End call
              </button>
            </div>
            {room.error && <div className="alert">{room.error}</div>}

            <div className="grid cols-2" style={{ marginTop: 14 }}>
              <div>
                <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>
                  {join.provider === "managed" ? "You (managed preview)" : "Remote"}
                </div>
                {join.provider === "webrtc" ? (
                  <video ref={room.remoteRef} autoPlay playsInline />
                ) : (
                  <video ref={room.localRef} autoPlay playsInline muted />
                )}
              </div>
              <div>
                <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>
                  You
                </div>
                <video ref={room.localRef} autoPlay playsInline muted />
              </div>
            </div>

            <div className="row" style={{ marginTop: 12 }}>
              <button className="secondary" onClick={room.toggleMic}>
                {room.micOn ? "Mute mic" : "Unmute mic"}
              </button>
              <button className="secondary" onClick={room.toggleCam}>
                {room.camOn ? "Stop camera" : "Start camera"}
              </button>
              {room.state === "waiting" && (
                <span className="muted">Waiting for the other participant to join…</span>
              )}
            </div>
          </div>

          {user?.role !== "patient" && consultation && (
            <p className="muted">
              Open the <strong>Provider Console</strong> to write the note and e-prescribe for this visit.
            </p>
          )}
        </>
      )}
    </>
  );
}
