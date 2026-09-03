import secrets

from django.db import models


class VideoSession(models.Model):
    """A single video/audio session, provider-agnostic.

    `provider` records which implementation minted the session so the client
    knows how to connect; `join_payload` carries whatever that implementation
    needs the client to have (ICE servers, or a managed room token).
    """

    PROVIDERS = [("webrtc", "Custom WebRTC"), ("managed", "Managed API")]
    STATUS = [("created", "Created"), ("active", "Active"), ("ended", "Ended")]

    consultation = models.ForeignKey(
        "consultations.Consultation", on_delete=models.CASCADE, related_name="video_sessions"
    )
    provider = models.CharField(max_length=12, choices=PROVIDERS)
    room = models.CharField(max_length=64, unique=True, default="")
    status = models.CharField(max_length=12, choices=STATUS, default="created")
    mode = models.CharField(
        max_length=8, choices=[("video", "video"), ("audio", "audio")], default="video"
    )
    join_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.room:
            self.room = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"VideoSession<{self.provider}:{self.room}>"


class StoreAndForwardMessage(models.Model):
    """Async, low-bandwidth messaging tied to a consultation (store-and-forward)."""

    consultation = models.ForeignKey(
        "consultations.Consultation", on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    body = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
