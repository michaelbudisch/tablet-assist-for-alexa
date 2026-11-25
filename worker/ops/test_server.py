"""No Docker, GPU, or personal configuration required."""
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import VERSION, make_handler, status


class OpsTests(unittest.TestCase):
    def setUp(self):
        def fake():
            return {"worker_version": VERSION, "mode": "read-only",
                    "services": {"vision": {"available": True}, "whisper": {"available": False}},
                    "gpu": {"available": False}, "overall": "degraded"}
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(checker=fake))
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.thread.join(timeout=2)

    def get(self, path):
        req = Request(f"http://127.0.0.1:{self.srv.server_port}{path}")
        with urlopen(req, timeout=2) as response:
            return response.status, json.loads(response.read()), response.headers

    def test_tokenless_status(self):
        self.assertEqual(self.get("/status")[0], 200)

    def test_health_and_status(self):
        self.assertEqual(self.get("/health")[1]["worker_version"], VERSION)
        code, body, headers = self.get("/status")
        self.assertEqual(code, 200)
        self.assertEqual(body["overall"], "degraded")
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_selftest_is_passive(self):
        body = self.get("/selftest")[1]
        self.assertEqual((body["passed"], body["total"]), (1, 2))
        self.assertIn("Connectivity", body["limitation"])

    def test_path_no_arbitrary_urls(self):
        with self.assertRaises(HTTPError) as err:
            self.get("/proxy?url=http://test")
        self.assertEqual(err.exception.code, 404)

    def test_offline_status(self):
        fake = lambda n, e: {"available": False, "latency_ms": 1}
        report = status(check=fake, gpu=lambda: {"available": False})
        self.assertEqual(report["overall"], "unavailable")


if __name__ == "__main__":
    unittest.main()
