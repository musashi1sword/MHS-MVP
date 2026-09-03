"""WebRTC signalling relay + live pharmacy status feed, over Channels."""
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ConsultationSignalConsumer(AsyncJsonWebsocketConsumer):
    """Relays SDP offers/answers and ICE candidates between the two peers in a
    room. The server never inspects media — it only forwards signalling JSON.
    """

    async def connect(self):
        self.room = self.scope["url_route"]["kwargs"]["room"]
        self.group = f"signal.{self.room}"
        user = self.scope.get("user")
        if user is None or not getattr(user, "is_authenticated", False):
            await self.close(code=4401)
            return
        self.identity = str(user.id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.group, {"type": "peer.event", "event": "peer-joined", "sender": self.identity}
        )

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_send(
                self.group,
                {"type": "peer.event", "event": "peer-left", "sender": getattr(self, "identity", "?")},
            )
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")
        if msg_type not in {"offer", "answer", "candidate", "bye", "chat"}:
            return
        await self.channel_layer.group_send(
            self.group,
            {"type": "signal.relay", "payload": content, "sender": self.identity},
        )

    async def signal_relay(self, event):
        if event["sender"] == self.identity:
            return  # don't echo to the originator
        await self.send_json(event["payload"])

    async def peer_event(self, event):
        if event["sender"] == self.identity:
            return
        await self.send_json({"type": event["event"], "sender": event["sender"]})


class PharmacyStatusConsumer(AsyncJsonWebsocketConsumer):
    """Broadcasts prescription/pharmacy status changes to any listening board."""

    GROUP = "pharmacy.status"

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not getattr(user, "is_authenticated", False):
            await self.close(code=4401)
            return
        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def status_update(self, event):
        await self.send_json(event["data"])
