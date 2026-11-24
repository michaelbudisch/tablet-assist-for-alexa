"""Pure routing tests, no HA instance, network, or camera needed."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "jarvis_tablet_audio"))
from relay_room_router import RoomRouter

A, B = "a" * 32, "b" * 32


class RoomRouterTests(unittest.TestCase):
    def setUp(self):
        self.now = 100
        self.router = RoomRouter(lambda: self.now)
        self.router.provision(A, "living_room", "user_a")
        self.router.provision(B, "office", "user_b")
        self.router.heartbeat(A, "user_a", False)
        self.router.heartbeat(B, "user_b", False)

    def test_reply_never_redirects(self):
        job = self.router.request_reply(A, "user_a")
        self.assertIsNotNone(job)
        self.assertFalse(self.router.claim(job, B, "user_b"))
        self.assertTrue(self.router.claim(job, A, "user_a"))
        self.assertFalse(self.router.claim(job, A, "user_a"))

    def test_independent_rooms(self):
        a = self.router.request_room("living_room")
        b = self.router.request_room("office")
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertNotEqual(a, b)
        self.assertTrue(self.router.claim(a, A, "user_a"))
        self.assertTrue(self.router.claim(b, B, "user_b"))

    def test_wrong_principal(self):
        with self.assertRaises(PermissionError):
            self.router.heartbeat(A, "user_b", False)
        with self.assertRaises(PermissionError):
            self.router.request_reply(A, "user_b")

    def test_busy_or_stale_no_fallback(self):
        self.router.heartbeat(A, "user_a", True)
        self.assertIsNone(self.router.request_room("living_room"))
        self.now += 31
        self.router.heartbeat(B, "user_b", False)
        self.assertIsNone(self.router.request_reply(A, "user_a"))

    def test_expired_job(self):
        job = self.router.request_reply(A, "user_a")
        self.now += 91
        self.router.heartbeat(A, "user_a", False)
        self.assertFalse(self.router.claim(job, A, "user_a"))

    def test_finish_and_revoke(self):
        job = self.router.request_reply(A, "user_a")
        self.assertFalse(self.router.finish(job, B, "user_b"))
        self.assertTrue(self.router.claim(job, A, "user_a"))
        self.assertTrue(self.router.finish(job, A, "user_a"))
        other = self.router.request_reply(A, "user_a")
        self.router.revoke(A)
        self.router.provision(A, "living_room", "user_a")
        self.router.heartbeat(A, "user_a", False)
        self.assertFalse(self.router.claim(other, A, "user_a"))

    def test_single_pending_per_device(self):
        self.assertIsNotNone(self.router.request_reply(A, "user_a"))
        self.assertIsNone(self.router.request_reply(A, "user_a"))

    def test_duplicate_room_rejected(self):
        with self.assertRaises(ValueError):
            self.router.provision("c" * 32, "office", "user_c")


if __name__ == "__main__":
    unittest.main()
