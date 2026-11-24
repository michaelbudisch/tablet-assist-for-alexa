"""Room-scoped audio transport. No camera data or conversation text.

All calls run on one event loop. The principal is taken from authenticated HA
context. Each room needs its own dedicated HA user and one active audio player.
"""
from dataclasses import dataclass
import re
import secrets
from time import monotonic
from uuid import uuid4

ROOM = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
PATH = re.compile(r"/api/tts_proxy/[A-Za-z0-9_.~-]{1,200}")
MAX_ROOMS = 24
HEARTBEAT_TTL = 30
JOB_TTL = 180
TERMINAL = {"done", "cancelled", "error", "expired"}
STAGES = {"buffering", "playing", "done", "cancelled", "error"}


@dataclass
class Session:
    token: str
    seen: float
    ready: bool = False


@dataclass
class AudioJob:
    id: str
    room: str
    path: str
    expires: float
    stage: str = "queued"
    stop: bool = False


class RoomAudioTransport:
    def __init__(self, clock=monotonic):
        self.clock = clock
        self.rooms = {}
        self.sessions = {}
        self.jobs = {}

    def provision(self, room, principal):
        if (not isinstance(room, str) or not ROOM.fullmatch(room)
                or not isinstance(principal, str) or not 1 <= len(principal) <= 128):
            raise ValueError("invalid room or principal")
        if room not in self.rooms and len(self.rooms) >= MAX_ROOMS:
            raise ValueError("room limit reached")
        if any(p == principal and r != room for r, p in self.rooms.items()):
            raise ValueError("one dedicated HA user per room")
        self.revoke(room)
        self.rooms[room] = principal

    def revoke(self, room):
        self.rooms.pop(room, None)
        self.sessions.pop(room, None)
        self.jobs = {k: v for k, v in self.jobs.items() if v.room != room}

    def room_for(self, principal):
        room = next((r for r, p in self.rooms.items() if p == principal), None)
        if room is None:
            raise PermissionError("room not provisioned")
        return room

    def _prune(self):
        now = self.clock()
        for k, job in list(self.jobs.items()):
            if job.expires <= now:
                if job.stage not in TERMINAL:
                    job.stage, job.path, job.expires = "expired", "", now + 30
                else:
                    del self.jobs[k]
        for room, s in list(self.sessions.items()):
            if now - s.seen >= HEARTBEAT_TTL:
                del self.sessions[room]
                for job in self.jobs.values():
                    if job.room == room and job.stage not in TERMINAL:
                        self._terminal(job, "expired")

    def _terminal(self, job, stage):
        job.stage, job.path, job.expires = stage, "", self.clock() + 30

    def connect(self, principal):
        self._prune()
        room = self.room_for(principal)
        if room in self.sessions:
            raise RuntimeError("player already connected")
        s = Session(secrets.token_hex(32), self.clock())
        self.sessions[room] = s
        return {"room": room, "session": s.token}

    def _session(self, principal, token):
        self._prune()
        room = self.room_for(principal)
        s = self.sessions.get(room)
        if not s or not isinstance(token, str) or not secrets.compare_digest(s.token, token):
            raise PermissionError("inactive player session")
        s.seen = self.clock()
        return room, s

    def status(self, principal, request_id=None):
        self._prune()
        room = self.room_for(principal)
        s = self.sessions.get(room)
        result = {"room": room, "online": s is not None,
                  "ready": bool(s and s.ready and not self._active(room))}
        if request_id is not None:
            job = self.jobs.get(request_id)
            result["stage"] = job.stage if job and job.room == room else "unknown"
        return result

    def _active(self, room):
        return next((j for j in self.jobs.values()
                     if j.room == room and j.stage not in TERMINAL), None)

    def submit(self, principal, path):
        return self.submit_room(self.room_for(principal), path)

    def submit_room(self, room, path):
        self._prune()
        if not isinstance(path, str) or not PATH.fullmatch(path):
            raise ValueError("invalid local TTS path")
        s = self.sessions.get(room)
        if room not in self.rooms or not s or not s.ready or self._active(room):
            return None
        job = AudioJob(uuid4().hex, room, path, self.clock() + JOB_TTL)
        self.jobs[job.id] = job
        return job.id

    def poll(self, principal, token, ready):
        room, s = self._session(principal, token)
        if type(ready) is not bool:
            raise ValueError("invalid ready flag")
        s.ready = ready
        job = self._active(room)
        if not job:
            return {}
        if job.stop:
            return {"id": job.id, "stop": True}
        if job.stage == "queued" and ready:
            job.stage = "buffering"
            s.ready = False
            return {"id": job.id, "path": job.path}
        return {}

    def report(self, principal, token, request_id, stage):
        room, s = self._session(principal, token)
        job = self.jobs.get(request_id)
        if not job or job.room != room or stage not in STAGES or job.stage in TERMINAL or job.stage == "queued":
            return False
        if stage in TERMINAL:
            self._terminal(job, stage)
        elif stage == "playing":
            job.stage = stage
        elif job.stage == "buffering":
            job.stage = stage
        s.ready = False
        return True

    def cancel(self, principal, request_id):
        room = self.room_for(principal)
        self._prune()
        job = self.jobs.get(request_id)
        if not job or job.room != room or job.stage in TERMINAL:
            return False
        if job.stage == "queued":
            self._terminal(job, "cancelled")
        else:
            job.stop = True
        return True

    def disconnect(self, principal, token):
        room, _ = self._session(principal, token)
        self.sessions.pop(room, None)
        job = self._active(room)
        if job:
            self._terminal(job, "cancelled")
