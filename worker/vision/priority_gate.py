"""Bounded, per-process admission control for vision inference.

Only vision requests are serialized here. This does not control other GPU
containers such as Whisper, Ollama conversations, or Qwen TTS.
"""
import threading
import time


class VisionGate:
    def __init__(self, max_waiters=6, clock=time.monotonic):
        self._cv = threading.Condition()
        self._busy = False
        self._waiters = []
        self._sequence = 0
        self._max_waiters = max_waiters
        self._clock = clock

    def locked(self):
        with self._cv:
            return self._busy

    def snapshot(self):
        with self._cv:
            return {"busy": self._busy, "queue_depth": len(self._waiters),
                    "queue_capacity": self._max_waiters}

    def acquire(self, *, priority="interactive", wait_ms=0):
        if priority not in ("interactive", "background"):
            raise ValueError("invalid priority")
        if type(wait_ms) is not int or not 0 <= wait_ms <= 20000:
            raise ValueError("invalid wait_ms")
        with self._cv:
            if not self._busy and not self._waiters:
                self._busy = True
                return True
            if wait_ms == 0 or len(self._waiters) >= self._max_waiters:
                return False
            self._sequence += 1
            waiter = (0 if priority == "interactive" else 1, self._sequence)
            self._waiters.append(waiter)
            deadline = self._clock() + wait_ms / 1000
            try:
                while True:
                    best = min(self._waiters)
                    if not self._busy and waiter == best:
                        self._waiters.remove(waiter)
                        self._busy = True
                        return True
                    remaining = deadline - self._clock()
                    if remaining <= 0:
                        return False
                    self._cv.wait(remaining)
            finally:
                if waiter in self._waiters:
                    self._waiters.remove(waiter)
                    self._cv.notify_all()

    def release(self):
        with self._cv:
            if not self._busy:
                raise RuntimeError("vision gate was not held")
            self._busy = False
            self._cv.notify_all()
