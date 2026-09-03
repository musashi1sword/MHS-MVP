import { useCallback, useEffect, useRef, useState } from "react";
import { wsUrl } from "../api/client";
import type { JoinInfo } from "../api/types";

export type RoomState = "idle" | "connecting" | "waiting" | "connected" | "ended" | "error";

/**
 * One hook, both video modes (the dual-mode abstraction, client side).
 *
 * - provider === "webrtc": full peer connection with perfect-negotiation over
 *   the Channels signalling socket. STUN/TURN come from the server's JoinInfo.
 * - provider === "managed": we surface the local preview and the issued room
 *   token; a real build would hand `join.token` to the vendor SDK here.
 */
export function useVideoRoom(join: JoinInfo | null) {
  const [state, setState] = useState<RoomState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);

  const localRef = useRef<HTMLVideoElement | null>(null);
  const remoteRef = useRef<HTMLVideoElement | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const makingOffer = useRef(false);
  const ignoreOffer = useRef(false);

  const cleanup = useCallback(() => {
    wsRef.current?.close();
    pcRef.current?.close();
    localStreamRef.current?.getTracks().forEach((t) => t.stop());
    wsRef.current = null;
    pcRef.current = null;
    localStreamRef.current = null;
  }, []);

  const hangUp = useCallback(() => {
    try {
      wsRef.current?.send(JSON.stringify({ type: "bye" }));
    } catch {
      /* socket already closed */
    }
    cleanup();
    setState("ended");
  }, [cleanup]);

  useEffect(() => {
    if (!join) return;
    let cancelled = false;
    setState("connecting");
    setError(null);

    (async () => {
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: join.mode !== "audio",
        });
      } catch {
        setError("Camera/microphone permission denied.");
        setState("error");
        return;
      }
      if (cancelled) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      localStreamRef.current = stream;
      if (localRef.current) localRef.current.srcObject = stream;

      if (join.provider === "managed") {
        // Hand join.token to the vendor SDK in a real build. For the demo the
        // local preview + issued token is enough to prove the integration path.
        setState("connected");
        return;
      }

      const pc = new RTCPeerConnection({ iceServers: join.iceServers ?? [] });
      pcRef.current = pc;
      stream.getTracks().forEach((t) => pc.addTrack(t, stream));

      const remote = new MediaStream();
      pc.ontrack = (e) => {
        e.streams[0].getTracks().forEach((t) => remote.addTrack(t));
        if (remoteRef.current) remoteRef.current.srcObject = remote;
        setState("connected");
      };

      const ws = new WebSocket(wsUrl(join.signalUrl!));
      wsRef.current = ws;
      const polite = join.polite ?? false;

      const send = (m: unknown) => ws.readyState === 1 && ws.send(JSON.stringify(m));

      pc.onicecandidate = ({ candidate }) => candidate && send({ type: "candidate", candidate });
      pc.onnegotiationneeded = async () => {
        try {
          makingOffer.current = true;
          await pc.setLocalDescription();
          send({ type: "offer", sdp: pc.localDescription });
        } finally {
          makingOffer.current = false;
        }
      };
      pc.oniceconnectionstatechange = () => {
        if (pc.iceConnectionState === "disconnected" || pc.iceConnectionState === "failed") {
          setState((s) => (s === "connected" ? "waiting" : s));
        }
      };

      ws.onopen = () => setState("waiting");
      ws.onmessage = async (ev) => {
        const msg = JSON.parse(ev.data);
        try {
          if (msg.type === "offer" || msg.type === "answer") {
            const desc = msg.sdp as RTCSessionDescriptionInit;
            const offerCollision =
              msg.type === "offer" && (makingOffer.current || pc.signalingState !== "stable");
            ignoreOffer.current = !polite && offerCollision;
            if (ignoreOffer.current) return;
            await pc.setRemoteDescription(desc);
            if (msg.type === "offer") {
              await pc.setLocalDescription();
              send({ type: "answer", sdp: pc.localDescription });
            }
          } else if (msg.type === "candidate") {
            try {
              await pc.addIceCandidate(msg.candidate);
            } catch {
              if (!ignoreOffer.current) throw new Error("bad candidate");
            }
          } else if (msg.type === "bye") {
            hangUp();
          }
        } catch (e) {
          console.warn("signal handling error", e);
        }
      };
      ws.onerror = () => {
        setError("Signalling connection failed.");
        setState("error");
      };
    })();

    return () => {
      cancelled = true;
      cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [join?.room, join?.provider]);

  const toggleMic = () => {
    const track = localStreamRef.current?.getAudioTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setMicOn(track.enabled);
    }
  };
  const toggleCam = () => {
    const track = localStreamRef.current?.getVideoTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setCamOn(track.enabled);
    }
  };

  return { state, error, localRef, remoteRef, hangUp, micOn, camOn, toggleMic, toggleCam };
}
