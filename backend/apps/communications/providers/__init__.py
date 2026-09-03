"""Dual-mode video: one interface, two implementations, selected at runtime.

    get_provider()            -> the configured default (settings.VIDEO_PROVIDER)
    get_provider("managed")   -> an explicit choice (e.g. per-request override)
"""
from django.conf import settings

from .base import VideoProvider
from .managed import ManagedVideoProvider
from .webrtc import WebRTCVideoProvider

_REGISTRY: dict[str, type[VideoProvider]] = {
    "webrtc": WebRTCVideoProvider,
    "managed": ManagedVideoProvider,
}


def get_provider(name: str | None = None) -> VideoProvider:
    key = (name or settings.VIDEO_PROVIDER or "webrtc").lower()
    try:
        return _REGISTRY[key]()
    except KeyError:
        raise ValueError(f"Unknown video provider '{key}'. Options: {sorted(_REGISTRY)}")


__all__ = ["VideoProvider", "get_provider"]
