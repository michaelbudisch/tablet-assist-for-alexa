"""Separate, bounded RAM-only frames for opt-in shared-room camera streams."""
from .relay_frames import FrameStore, DEVICE

INTERVALS = {1, 2, 3, 5, 10}


class RoomCameraStore:
    def __init__(self, transport, clock):
        self.transport = transport
        self.clock = clock
        self.frames = {}
        self.principals = {}
        self.intervals = {}
        self.last_upload = {}

    def enabled(self, room):
        return room in self.transport.rooms and self.transport.settings.get(room, {}).get("camera_enabled") is True

    def sync(self):
        changed = set()
        for room in list(self.frames):
            if not self.enabled(room) or self.principals[room] != self.transport.rooms.get(room):
                self.frames.pop(room).clear()
                self.principals.pop(room, None)
                self.intervals.pop(room, None)
                self.last_upload.pop(room, None)
                changed.add(room)
        return changed

    def room_for(self, principal):
        self.sync()
        room = self.transport.room_for(principal)
        if not self.enabled(room):
            raise PermissionError("Camera not opted in for this room")
        return room

    def register(self, principal, device):
        room = self.room_for(principal)
        if not isinstance(device, str) or not DEVICE.fullmatch(device):
            raise ValueError("Invalid device")
        store = self.frames.get(room)
        if store and store.device and store.device != device and store.session:
            raise RuntimeError("Another tablet is paired to this room")
        if store is None:
            store = self.frames[room] = FrameStore(self.clock)
            self.principals[room] = principal
        self.last_upload.pop(room, None)
        self.intervals.pop(room, None)
        return room, store.register(device)

    def authorized(self, principal, device, session):
        room = self.room_for(principal)
        store = self.frames.get(room)
        if store is None or not store.authorized(device, session):
            raise PermissionError("Inactive camera session")
        return room, store

    def put(self, principal, device, session, sequence, image, captured, motion, interval):
        room, store = self.authorized(principal, device, session)
        if type(interval) is not int or interval not in INTERVALS:
            raise ValueError("Invalid refresh interval")
        now = self.clock()
        if room in self.last_upload and now - self.last_upload[room] < .5:
            raise RuntimeError("Too many images")
        store.put(device, session, sequence, image, captured, motion)
        self.last_upload[room] = now
        self.intervals[room] = interval
        return room

    def stop(self, principal, device, session):
        room, store = self.authorized(principal, device, session)
        store.clear()
        self.last_upload.pop(room, None)
        self.intervals.pop(room, None)
        return room

    def expire(self):
        return self.sync() | {room for room, store in self.frames.items() if store.expire()}

    def fresh(self, room):
        store = self.frames.get(room)
        return bool(self.enabled(room) and store and store.fresh)
