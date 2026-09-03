"""Authenticate websocket connections from a `?token=<JWT>` query param."""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _user_from_token(token: str):
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken
    from django.contrib.auth import get_user_model

    try:
        access = AccessToken(token)
        return get_user_model().objects.get(id=access["user_id"])
    except (TokenError, KeyError, Exception):  # noqa: BLE001 - fall back to anon
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = (query.get("token") or [None])[0]
        if token:
            scope["user"] = await _user_from_token(token)
        return await super().__call__(scope, receive, send)
