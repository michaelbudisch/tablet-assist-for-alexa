"""Bounded, in-memory push camera protocol; independent of Home Assistant for testing."""
import re
import secrets
from time import monotonic

DEVICE = re.compile(r"[a-f0-9]{32}")
MAX_IMAGE = 2 * 1024 * 1024
MAX_AGE = 15

class FrameStore:
    def __init__(self, clock=monotonic):
        self.clock = clock
        self.session = ""
        self.device = ""
        self.sequence = 0
        self.image = None
        self.received = 0
        self.captured_at = 0
        self.motion = None

    def register(self, device):
        if not isinstance(device, str) or not DEVICE.fullmatch(device):
            raise ValueError("invalid device")
        self.clear()
        self.device = device
        self.session = secrets.token_hex(32)
        self.sequence = 0
        return self.session

    def authorized(self, device, session):
        return bool(self.session and isinstance(session, str) and re.fullmatch(r"[a-f0-9]{64}", session) and device == self.device
                    and secrets.compare_digest(self.session, session))

    def put(self, device, session, sequence, image, captured_at, motion):
        if not self.authorized(device, session):
            raise PermissionError("inactive session")
        if not isinstance(sequence, int) or not self.sequence < sequence < 2**53:
            raise ValueError("old sequence")
        if not isinstance(image, bytes) or not 0 < len(image) <= MAX_IMAGE:
            raise ValueError("image size")
        if type(motion) not in (bool, type(None)):
            raise ValueError("motion flag")
        self.sequence = sequence
        self.image = image
        self.received = self.clock()
        self.captured_at = captured_at
        self.motion = motion

    @property
    def fresh(self):
        return self.image is not None and self.clock() - self.received <= MAX_AGE

    def expire(self):
        if self.image is not None and not self.fresh:
            self.image = None
            self.motion = None
            return True
        return False

    def clear(self):
        self.session = ""
        self.image = None
        self.motion = None
        self.received = 0
