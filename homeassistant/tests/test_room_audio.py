import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "jarvis_tablet_audio"))
from relay_room_audio import RoomAudioTransport

P = "/api/tts_proxy/example.mp3"

class TransportTests(unittest.TestCase):
    def setUp(self):
        self.now = 100
        self.r = RoomAudioTransport(lambda: self.now)
        self.r.provision("office", "a")
        self.r.provision("living", "b")
        self.a = self.r.connect("a")["session"]
        self.b = self.r.connect("b")["session"]
        self.r.poll("a", self.a, True)
        self.r.poll("b", self.b, True)

    def test_room_isolation(self):
        job = self.r.submit("a", P)
        self.assertEqual(self.r.poll("b", self.b, True), {})
        self.assertEqual(self.r.status("b", job)["stage"], "unknown")
        self.assertFalse(self.r.cancel("b", job))
        self.assertFalse(self.r.report("b", self.b, job, "playing"))
        self.assertEqual(self.r.poll("a", self.a, True), {"id": job, "path": P})
        self.assertEqual(self.r.poll("a", self.a, True), {})

    def test_report_and_finish(self):
        job = self.r.submit_room("office", P)
        self.r.poll("a", self.a, True)
        self.assertTrue(self.r.report("a", self.a, job, "playing"))
        self.assertEqual(self.r.status("a", job)["stage"], "playing")
        self.assertTrue(self.r.report("a", self.a, job, "done"))
        self.assertEqual(self.r.status("a", job)["stage"], "done")
        self.r.poll("a", self.a, True)
        self.assertIsNotNone(self.r.submit("a", P))

    def test_cancel(self):
        job = self.r.submit("a", P)
        self.r.poll("a", self.a, True)
        self.assertTrue(self.r.cancel("a", job))
        self.assertEqual(self.r.poll("a", self.a, False), {"id": job, "stop": True})
        self.assertTrue(self.r.report("a", self.a, job, "cancelled"))

    def test_expired_and_busy(self):
        self.assertIsNotNone(self.r.submit("a", P))
        self.assertIsNone(self.r.submit("a", P))
        self.now += 31
        self.assertIsNone(self.r.submit("a", P))
        with self.assertRaises(PermissionError):
            self.r.poll("a", self.a, True)

    def test_no_other_principal(self):
        with self.assertRaises(PermissionError):
            self.r.poll("b", self.a, True)
        with self.assertRaises(PermissionError):
            self.r.connect("unregistered")
        with self.assertRaises(RuntimeError):
            self.r.connect("a")

    def test_revoke_and_unique(self):
        with self.assertRaises(ValueError):
            self.r.provision("kitchen", "a")
        self.r.revoke("office")
        with self.assertRaises(PermissionError):
            self.r.poll("a", self.a, True)

    def test_only_local_paths(self):
        for bad in ("https://example.com/x", "/api/states", "/api/tts_proxy/../x", "/api/tts_proxy/x?token=y"):
            with self.assertRaises(ValueError):
                self.r.submit("a", bad)

    def test_independent_jobs(self):
        a, b = self.r.submit("a", P), self.r.submit("b", P)
        self.assertNotEqual(a, b)
        self.assertEqual(self.r.poll("a", self.a, True)["id"], a)
        self.assertEqual(self.r.poll("b", self.b, True)["id"], b)

if __name__ == "__main__":
    unittest.main()
