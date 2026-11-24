"""Run with python -m unittest -v test_priority_gate."""
import threading
import time
import unittest
from priority_gate import VisionGate


class GateTests(unittest.TestCase):
    def test_legacy_nonblocking(self):
        gate = VisionGate()
        self.assertTrue(gate.acquire())
        self.assertFalse(gate.acquire())
        self.assertEqual(gate.snapshot()["queue_depth"], 0)
        gate.release()
        self.assertTrue(gate.acquire())
        gate.release()

    def test_bounds(self):
        gate = VisionGate()
        with self.assertRaises(ValueError):
            gate.acquire(priority="admin")
        with self.assertRaises(ValueError):
            gate.acquire(wait_ms=True)
        with self.assertRaises(ValueError):
            gate.acquire(wait_ms=30000)

    def test_bounded_queue(self):
        gate = VisionGate(max_waiters=1)
        gate.acquire()
        results = []
        thread = threading.Thread(target=lambda: results.append(gate.acquire(wait_ms=120)))
        thread.start()
        for _ in range(40):
            if gate.snapshot()["queue_depth"] == 1:
                break
            time.sleep(.005)
        self.assertEqual(gate.snapshot()["queue_depth"], 1)
        self.assertFalse(gate.acquire(wait_ms=100))
        thread.join(timeout=2)
        self.assertEqual(results, [False])
        gate.release()

    def test_interactive_precedes_background(self):
        gate = VisionGate()
        gate.acquire()
        order = []
        def job(kind):
            if gate.acquire(priority=kind, wait_ms=2000):
                order.append(kind)
                gate.release()
        background = threading.Thread(target=job, args=("background",))
        interactive = threading.Thread(target=job, args=("interactive",))
        background.start()
        while gate.snapshot()["queue_depth"] < 1:
            time.sleep(.005)
        interactive.start()
        while gate.snapshot()["queue_depth"] < 2:
            time.sleep(.005)
        gate.release()
        background.join(timeout=3)
        interactive.join(timeout=3)
        self.assertEqual(order, ["interactive", "background"])

    def test_release_requires_owner(self):
        with self.assertRaises(RuntimeError):
            VisionGate().release()


if __name__ == "__main__":
    unittest.main()
