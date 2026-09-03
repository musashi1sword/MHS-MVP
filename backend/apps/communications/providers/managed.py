import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.utils import timezone

from ..models import VideoSession
from .base import JoinInfo, VideoProvider


class ManagedVideoProvider(VideoProvider):
    """Managed API path (AWS Chime SDK or Twilio Video).

    When real credentials are present we would call the vendor SDK here. For the
    MVP demo with no keys, we mint a self-signed room token with the same shape a
    vendor JWT would have, so the client integration is exercised end to end.
    """

    name = "managed"

    def create_session(self, consultation, mode: str = "video") -> VideoSession:
        session = VideoSession.objects.create(
            consultation=consultation, provider=self.name, mode=mode, status="created"
        )
        session.join_payload = {
            "vendor": settings.MANAGED_VIDEO_VENDOR,
            "roomName": f"mhs-{session.room}",
            "live": bool(settings.MANAGED_VIDEO_API_KEY),
        }
        session.save(update_fields=["join_payload"])
        return session

    def _mint_token(self, session, user) -> str:
        # Derive a fixed 32-byte key so short dev SECRET_KEYs don't warn.
        secret = hashlib.sha256(
            (settings.MANAGED_VIDEO_API_SECRET or settings.SECRET_KEY).encode()
        ).digest()
        header = {"alg": "HS256", "typ": "JWT", "cty": "twilio-fpa;v=1"}
        now = int(time.time())
        claims = {
            "jti": f"{session.room}-{now}",
            "iss": settings.MANAGED_VIDEO_API_KEY or "mhs-mock-key",
            "sub": "mhs-mvp",
            "iat": now,
            "exp": now + 3600,
            "grants": {
                "identity": str(user.id),
                "video": {"room": session.join_payload.get("roomName", session.room)},
            },
        }

        def b64(obj):
            return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=")

        signing_input = b64(header) + b"." + b64(claims)
        sig = base64.urlsafe_b64encode(
            hmac.new(secret, signing_input, hashlib.sha256).digest()
        ).rstrip(b"=")
        return (signing_input + b"." + sig).decode()

    def join_info(self, session, user) -> JoinInfo:
        if session.status == "created":
            session.status = "active"
            session.save(update_fields=["status"])
        return JoinInfo(
            provider=self.name,
            room=session.room,
            mode=session.mode,
            payload={
                "vendor": session.join_payload.get("vendor", settings.MANAGED_VIDEO_VENDOR),
                "roomName": session.join_payload.get("roomName", session.room),
                "token": self._mint_token(session, user),
                "live": session.join_payload.get("live", False),
            },
        )

    def end_session(self, session) -> None:
        session.status = "ended"
        session.ended_at = timezone.now()
        session.save(update_fields=["status", "ended_at"])
