"""Tests for the local-only MP4 Ring benchmark runner (no FFmpeg or camera needed)."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from benchmark_ring_video import _private_base, _token, main


class RingBenchmarkCliTests(unittest.TestCase):
    def test_worker_url_must_be_local(self):
        self.assertEqual(_private_base("http://127.0.0.1:10505"),
                         "http://127.0.0.1:10505")
        self.assertEqual(_private_base("http://192.168.178.115:10505/"),
                         "http://192.168.178.115:10505")
        for url in ("https://example.com:10505",
                    "http://8.8.8.8:10505",
                    "http://example.org:10505",
                    "http://user:pass@127.0.0.1:10505"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _private_base(url)

    def test_token_is_read_from_private_env_without_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text("JARVIS_TTS_TOKEN=local-" + "a" * 40 + "\n",
                            encoding="utf-8")
            with mock.patch.dict(os.environ, {"JARVIS_TTS_TOKEN": ""}):
                self.assertEqual(_token(path), "local-" + "a" * 40)

    def test_baseline_reuses_identical_four_frames(self):
        token = "test-only-" + "x" * 40
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / "ring.mp4"
            video.write_bytes(b"fake local clip, extraction mocked")
            report = Path(folder) / "report.json"
            seen = []

            def fake_send(base, key, *, images, mode, ctx, model):
                self.assertEqual(base, "http://127.0.0.1:10505")
                self.assertEqual(key, token)
                seen.append((mode, [x["second"] for x in images]))
                return {
                    "ok": True, "client_ms": 1000,
                    "worker": {
                        "descriptions": ["Kein eindeutiges Ereignis"],
                        "metrics": {"inference_ms": 700},
                    },
                }

            with (
                mock.patch.dict(os.environ, {"JARVIS_TTS_TOKEN": token}),
                mock.patch("benchmark_ring_video.shutil.which", return_value="fake"),
                mock.patch("benchmark_ring_video._duration", return_value=12.0),
                mock.patch("benchmark_ring_video._sample", return_value="base64-test"),
                mock.patch("benchmark_ring_video._send", side_effect=fake_send),
                mock.patch("builtins.print"),
            ):
                rc = main([str(video), "--output", str(report)])

            self.assertEqual(rc, 0)
            self.assertEqual([len(s) for _, s in seen], [4, 4, 8, 12])
            self.assertEqual(seen[0][1], seen[1][1])
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(len(data["results"]), 4)
            self.assertNotIn("base64-test", report.read_text(encoding="utf-8"))
            self.assertNotIn(token, report.read_text(encoding="utf-8"))
            self.assertNotIn("images", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
