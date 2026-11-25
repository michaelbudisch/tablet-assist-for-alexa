"""Experimental room-scoped audio routing; not wired into the live integration.

All methods must be called on the Home Assistant event loop. The adapter must
supply an authenticated principal from HA, never a user ID supplied by a client.
No camera frames, microphone data, identities or speech text are stored here.
"""
from dataclasses import dataclass
import re
from time import monotonic
from uuid import uuid4

_DEVICE = re.compile(r"[a-f0-9]{32}")
_ROOM = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
MAX_DEVICES = 24
HEARTBEAT_TTL = 30
REQUEST_TTL = 90


@dataclass(frozen=True)
class Device:
    device_id: str
    room: str
    principal: str


@dataclass
class Presence:
    seen: float
    busy: bool


@dataclass
class Job:
    device_id: str
    expires: float
    claimed: bool = False


class RoomRouter:
    """Explicitly provisioned devices; never redirect a private reply."""
    def __init__(self, clock=monotonic):
        self._clock = clock
        self._devices = {}
        self._presence = {}
        self._jobs = {}

    def provision(self, device_id, room, principal):
        """Trusted administrator adapter only; no self-enrollment."""
        if (not isinstance(device_id, str) or not _DEVICE.fullmatch(device_id)
                or not isinstance(room, str) or not _ROOM.fullmatch(room)
                or not isinstance(principal, str) or not 1 <= len(principal) <= 128):
            raise ValueError("invalid device configuration")
        if device_id not in self._devices and len(self._devices) >= MAX_DEVICES:
            raise ValueError("device limit reached")
        if any(d.room == room and d.device_id != device_id for d in self._devices.values()):
            raise ValueError("room already assigned")
        self.revoke(device_id)
        self._devices[device_id] = Device(device_id, room, principal)

    def revoke(self, device_id):
        self._devices.pop(device_id, None)
        self._presence.pop(device_id, None)
        self._jobs = {k: v for k, v in self._jobs.items() if v.device_id != device_id}

    def _authorize(self, device_id, principal):
        device = self._devices.get(device_id)
        if device is None or device.principal != principal:
            raise PermissionError("device not authorized")
        return device

    def heartbeat(self, device_id, principal, busy):
        self._authorize(device_id, principal)
        if type(busy) is not bool:
            raise ValueError("invalid busy status")
        self._presence[device_id] = Presence(self._clock(), busy)

    def _prune(self):
        now = self._clock()
        self._jobs = {k: v for k, v in self._jobs.items() if v.expires > now}

    def _ready(self, device_id):
        status = self._presence.get(device_id)
        return status is not None and self._clock() - status.seen < HEARTBEAT_TTL and not status.busy

    def request_reply(self, device_id, principal):
        """Reply to the originating tablet only."""
        self._authorize(device_id, principal)
        return self._request(device_id)

    def request_room(self, room):
        """Trusted automation adapter only; one explicitly assigned room."""
        device = next((d for d in self._devices.values() if d.room == room), None)
        if device is None:
            return None
        return self._request(device.device_id)

    def _request(self, device_id):
        self._prune()
        if not self._ready(device_id) or any(j.device_id == device_id for j in self._jobs.values()):
            return None
        request_id = uuid4().hex
        self._jobs[request_id] = Job(device_id, self._clock() + REQUEST_TTL)
        return request_id

    def claim(self, request_id, device_id, principal):
        self._authorize(device_id, principal)
        self._prune()
        job = self._jobs.get(request_id)
        if job is None or job.device_id != device_id or job.claimed or not self._ready(device_id):
            return False
        job.claimed = True
        return True

    def finish(self, request_id, device_id, principal):
        self._authorize(device_id, principal)
        self._prune()
        job = self._jobs.get(request_id)
        if job is None or job.device_id != device_id or not job.claimed:
            return False
        del self._jobs[request_id]
        return True
