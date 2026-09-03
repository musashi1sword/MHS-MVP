"""Smoke-test the WebRTC signalling relay over Channels (in-memory layer)."""
import asyncio
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver,localhost,127.0.0.1"
django.setup()

from channels.testing import WebsocketCommunicator  # noqa: E402
from rest_framework_simplejwt.tokens import AccessToken  # noqa: E402

from apps.communications.consumers import ConsultationSignalConsumer  # noqa: E402
from apps.demo.seed import seed_demo  # noqa: E402


async def main():
    seed = await asyncio.to_thread(seed_demo)
    from django.contrib.auth import get_user_model

    User = get_user_model()
    provider = await asyncio.to_thread(User.objects.get, email=seed["accounts"]["clinician"])
    patient = await asyncio.to_thread(User.objects.get, email=seed["accounts"]["patient"])
    t_prov = str(AccessToken.for_user(provider))
    t_pat = str(AccessToken.for_user(patient))

    room = "smoke-room"
    app = ConsultationSignalConsumer.as_asgi()

    a = WebsocketCommunicator(app, f"/ws/consultations/{room}/signal?token={t_prov}")
    a.scope["url_route"] = {"kwargs": {"room": room}}
    from apps.communications.middleware import _user_from_token

    a.scope["user"] = await _user_from_token(t_prov)
    connected, _ = await a.connect()
    assert connected, "provider failed to connect"

    b = WebsocketCommunicator(app, f"/ws/consultations/{room}/signal?token={t_pat}")
    b.scope["url_route"] = {"kwargs": {"room": room}}
    b.scope["user"] = await _user_from_token(t_pat)
    connected, _ = await b.connect()
    assert connected, "patient failed to connect"

    # provider gets a peer-joined notice when the patient connects
    hello = await a.receive_json_from(timeout=2)
    assert hello["type"] == "peer-joined", hello
    print("  [PASS] peer-joined notice delivered")

    # provider sends an SDP offer; patient should receive it
    await a.send_json_to({"type": "offer", "sdp": "v=0 ...fake..."})
    got = await b.receive_json_from(timeout=2)
    assert got["type"] == "offer" and got["sdp"].startswith("v=0"), got
    print("  [PASS] offer relayed provider -> patient")

    await b.send_json_to({"type": "answer", "sdp": "v=0 ...answer..."})
    got = await a.receive_json_from(timeout=2)
    assert got["type"] == "answer", got
    print("  [PASS] answer relayed patient -> provider")

    await a.disconnect()
    await b.disconnect()
    print("\nWebSocket signalling OK.")


asyncio.run(main())
