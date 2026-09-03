from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class JoinInfo:
    """Everything a client needs to connect, regardless of provider."""

    provider: str
    room: str
    mode: str
    # For webrtc: {"iceServers": [...], "signalUrl": "/ws/..."}
    # For managed: {"vendor": "...", "token": "...", "roomName": "..."}
    payload: dict

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "room": self.room,
            "mode": self.mode,
            **self.payload,
        }


class VideoProvider(abc.ABC):
    """Single interface the rest of the app codes against."""

    name: str

    @abc.abstractmethod
    def create_session(self, consultation, mode: str = "video") -> "VideoSession":
        """Create and persist a VideoSession for this consultation."""

    @abc.abstractmethod
    def join_info(self, session, user) -> JoinInfo:
        """Connection details for `user` to join `session`."""

    @abc.abstractmethod
    def end_session(self, session) -> None:
        ...
