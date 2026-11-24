"""Offline mocked checks for the opt-in multi-frame benchmark API."""
import base64
import io
import unittest

from PIL import Image
from server import create_app, DEFAULT_MODEL

TOKEN = "unit-test-token-" + "z" * 40
AUTH = {"X-API-Key": TOKEN}


def image():
    buf = io.BytesIO()
    Image.new("RGB", (96, 64), "teal").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def frames(count=4):
    return [{"second": round((i + 0.5) * 0.8, 2), "image": image()}
            for i in range(count)]


class SequenceBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.requests = []

        def fake(path, data=None, timeout=8):
            self.requests.append((path, data, timeout))
            return {
                "message": {"content": "In einem Bild ist ein Weg sichtbar."},
                "load_duration": 1_000_000,
                "prompt_eval_duration": 15_000_000,
                "eval_duration": 12_000_000,
            }

        self.client = create_app(TOKEN, call=fake).test_client()

    def send(self, *, n=4, mode="joint", **kwargs):
        return self.client.post(
            "/benchmark/sequence",
            json={"frames": frames(n), "mode": mode, **kwargs},
            headers=AUTH,
        )

    def test_not_accessible_without_api_key(self):
        result = self.client.post(
            "/benchmark/sequence", json={"frames": frames()}, headers={}
        )
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.requests, [])

    def test_joint_four_frames_one_inference(self):
        result = self.send()
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(result.json["frames"], 4)
        self.assertEqual(result.json["mode"], "joint")
        self.assertEqual(len(self.requests), 1)
        path, body, timeout = self.requests[0]
        self.assertEqual(path, "/api/chat")
        self.assertEqual(len(body["messages"][1]["images"]), 4)
        self.assertEqual(body["model"], DEFAULT_MODEL)
        self.assertEqual(body["keep_alive"], 300)
        self.assertEqual(body["options"]["num_ctx"], 8192)
        self.assertEqual(result.json["metrics"]["requested_num_ctx"], 4096)
        self.assertEqual(result.json["metrics"]["effective_num_ctx"], 8192)
        self.assertEqual(body["think"], False)
        self.assertFalse(body["stream"])
        self.assertIn("Bild 4", body["messages"][1]["content"])
        self.assertIn("Keine Gesichts- oder Identitätserkennung",
                      body["messages"][0]["content"])
        self.assertEqual(result.headers["Cache-Control"], "no-store")
        self.assertEqual(result.json["metrics"]["ollama"][0]["eval_ms"], 12.0)

    def test_joint_eight_and_twelve_are_single_calls(self):
        for count in (8, 12):
            with self.subTest(count=count):
                self.requests.clear()
                result = self.send(n=count, mode="joint", num_ctx=8192)
                self.assertEqual(result.status_code, 200, result.json)
                self.assertEqual(len(self.requests), 1)
                imgs = self.requests[0][1]["messages"][1]["images"]
                self.assertEqual(len(imgs), count)
                self.assertEqual(self.requests[0][1]["options"]["num_ctx"], 16384)
                self.assertEqual(result.json["metrics"]["effective_num_ctx"], 16384)
                with Image.open(io.BytesIO(base64.b64decode(imgs[0]))) as img:
                    self.assertLessEqual(max(img.size), 768)
                    self.assertEqual(img.format, "JPEG")

    def test_independent_four_frames_four_inferences(self):
        result = self.send(mode="independent")
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(len(result.json["descriptions"]), 4)
        self.assertEqual(len(self.requests), 4)
        self.assertTrue(all(req[1]["options"]["num_ctx"] == 4096 for req in self.requests))
        self.assertEqual(result.json["metrics"]["effective_num_ctx"], 4096)
        self.assertTrue(all(len(req[1]["messages"][1]["images"]) == 1
                            for req in self.requests))
        self.assertTrue(all("Keine Annahmen" in req[1]["messages"][1]["content"]
                            for req in self.requests))

    def test_invalid_frame_counts(self):
        for count in (0, 1, 3, 5, 11, 13):
            with self.subTest(count=count):
                self.assertEqual(self.send(n=count).status_code, 400)
        self.assertEqual(self.send(n=8, mode="independent").status_code, 400)
        self.assertEqual(self.requests, [])

    def test_invalid_params_never_infer(self):
        cases = [
            {"mode": "video"},
            {"model": "gemma3:4b"},
            {"model": "http://external.example"},
            {"num_ctx": 65536},
            {"num_ctx": True},
            {"keep_alive": "300"},
            {"priority": "admin"},
            {"wait_ms": 50000},
            {"wait_ms": True},
            {"question": "who is this person"},
            {"source_url": "http://example.org/clip.mp4"},
        ]
        for change in cases:
            with self.subTest(change=change):
                self.assertEqual(self.send(**change).status_code, 400)
        self.assertEqual(self.requests, [])

    def test_invalid_timestamps_and_frame_format(self):
        cases = [
            [{"second": 1, "image": image()}] * 4,
            [{"second": i, "image": image()} for i in (1, 2, 3, 121)],
            [{"second": i, "image": image()} for i in (-1, 1, 2, 3)],
            [{"second": i, "image": image()} for i in (1, 2, 1, 4)],
            [{"second": i, "image": image(), "label": "x"} for i in range(4)],
            [{"second": i, "image": "bad"} for i in range(4)],
        ]
        for set_of_frames in cases:
            with self.subTest(frames=set_of_frames[0].keys()):
                result = self.client.post(
                    "/benchmark/sequence",
                    json={"frames": set_of_frames, "mode": "joint"},
                    headers=AUTH,
                )
                self.assertEqual(result.status_code, 400, result.json)
        self.assertEqual(self.requests, [])

    def test_no_frames_is_bad_request_in_both_modes(self):
        for mode in ("joint", "independent"):
            with self.subTest(mode=mode):
                result = self.client.post(
                    "/benchmark/sequence",
                    json={"frames": None, "mode": mode}, headers=AUTH,
                )
                self.assertEqual(result.status_code, 400)

    def test_failed_model_returns_generic_error(self):
        def bad(*args, **kwargs):
            raise RuntimeError("untrusted host internal details")
        client = create_app(TOKEN, call=bad).test_client()
        result = client.post(
            "/benchmark/sequence",
            json={"frames": frames(4), "mode": "joint"}, headers=AUTH,
        )
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json["error"], "benchmark inference unavailable")

    def test_endpoint_advertised_without_changing_existing_contract(self):
        info = self.client.get("/capabilities", headers=AUTH)
        self.assertEqual(info.json["worker_version"], "2.1.1")
        self.assertEqual(info.json["benchmark_api"], 1)
        self.assertIn("/benchmark/sequence", info.json["endpoints"])
        self.assertIn("/describe", info.json["endpoints"])
        self.assertIn("/detect", info.json["endpoints"])


if __name__ == "__main__":
    unittest.main()
