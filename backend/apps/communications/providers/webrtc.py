from django.conf import settings
from django.utils import timezone

from ..models import VideoSession
from .base import JoinInfo, VideoProvider


class WebRTCVideoProvider(VideoProvider):
    """Custom WebRTC path: we mint the room and hand the client ICE servers
    (STUN + optional COTURN TURN) plus a Channels signalling URL. Peers exchange
    SDP/ICE over the `ConsultationSignalConsumer` websocket.
    """

    name = "webrtc"

    def _ice_servers(self) -> list[dict]:
        servers: list[dict] = [{"urls": settings.WEBRTC_STUN_URLS}]
        if settings.WEBRTC_TURN_URL:
            servers.append(
                {
                    "urls": settings.WEBRTC_TURN_URL,
                    "username": settings.WEBRTC_TURN_USERNAME,
                    "credential": settings.WEBRTC_TURN_CREDENTIAL,
                }
            )
        return servers

    def create_session(self, consultation, mode: str = "video") -> VideoSession:
        return VideoSession.objects.create(
            consultation=consultation, provider=self.name, mode=mode, status="created"
        )

    def join_info(self, session, user) -> JoinInfo:
        if session.status == "created":
            session.status = "active"
            session.save(update_fields=["status"])
        role = "provider" if user == session.consultation.provider else "patient"
        return JoinInfo(
            provider=self.name,
            room=session.room,
            mode=session.mode,
            payload={
                "iceServers": self._ice_servers(),
                "signalUrl": f"/ws/consultations/{session.room}/signal",
                "role": role,
                # The provider initiates the offer; keeps the demo deterministic.
                "polite": role == "patient",
            },
        )

    def end_session(self, session) -> None:
        session.status = "ended"
        session.ended_at = timezone.now()
        session.save(update_fields=["status", "ended_at"])
