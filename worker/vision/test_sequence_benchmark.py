"""Offline mocked checks for the opt-in multi-frame benchmark API."""
import base64
import io
import json
import unittest

from PIL import Image
from server import create_app, DEFAULT_MODEL

AUTH = {}


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

        self.client = create_app( call=fake).test_client()

    def send(self, *, n=4, mode="joint", **kwargs):
        return self.client.post(
            "/benchmark/sequence",
            json={"frames": frames(n), "mode": mode, **kwargs},
            headers=AUTH,
        )

    def test_accessible_without_token_on_private_network(self):
        result = self.client.post(
            "/benchmark/sequence", json={"frames": frames()}, headers={}
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(self.requests), 1)

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
        client = create_app( call=bad).test_client()
        result = client.post(
            "/benchmark/sequence",
            json={"frames": frames(4), "mode": "joint"}, headers=AUTH,
        )
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json["error"], "benchmark inference unavailable")

    def test_endpoint_advertised_without_changing_existing_contract(self):
        info = self.client.get("/capabilities", headers=AUTH)
        self.assertEqual(info.json["worker_version"], "2.2.1")
        self.assertEqual(info.json["benchmark_api"], 1)
        self.assertIn("/benchmark/sequence", info.json["endpoints"])
        self.assertIn("/describe", info.json["endpoints"])
        self.assertIn("/detect", info.json["endpoints"])



class ProductionSequenceTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.answer = {"description": "Eine Person trägt ein Paket.",
                       "person": "yes", "vehicle": "no", "parcel_carried": "yes",
                       "parcel_placed": "no", "delivery_vehicle": "no",
                       "delivery_clothing": "no"}
        def fake(path, data=None, timeout=8):
            self.requests.append((path, data, timeout))
            return {"message": {"content": json.dumps(self.answer)}}
        self.client = create_app( call=fake).test_client()

    def send(self, count=12, **kw):
        return self.client.post("/describe/sequence", headers=AUTH,
                                json={"frames": frames(count), **kw})

    def test_standard_contract(self):
        result = self.send()
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(result.json["delivery_assessment"], "likely")
        self.assertEqual(result.json["evidence"]["parcel_carried"], "yes")
        self.assertEqual(result.json["frames"], 12)
        self.assertEqual(result.json["sequence_api"], 1)
        self.assertEqual(len(self.requests), 1)
        body = self.requests[0][1]
        self.assertEqual(body["options"]["num_ctx"], 16384)
        self.assertEqual(len(body["messages"][1]["images"]), 12)
        self.assertEqual(body["format"]["additionalProperties"], False)
        self.assertEqual(result.headers["Cache-Control"], "no-store")

    def test_detail_profile_same_context(self):
        result = self.send(4, profile="detail", num_ctx=16384)
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(result.json["metrics"]["max_image_edge"], 1024)
        self.assertEqual(result.json["metrics"]["effective_num_ctx"], 16384)

    def test_uncertain_and_contradictory(self):
        self.answer["person"] = "no"
        result = self.send()
        self.assertEqual(result.json["delivery_assessment"], "uncertain")
        self.assertEqual(result.json["evidence"]["parcel_carried"], "uncertain")

    def test_clothing_alone_not_likely(self):
        self.answer.update(parcel_carried="no", delivery_clothing="yes")
        self.assertEqual(self.send().json["delivery_assessment"], "uncertain")

    def test_no_evidence(self):
        self.answer.update(parcel_carried="no")
        self.assertEqual(self.send().json["delivery_assessment"], "no_evidence")

    def test_missing_and_invalid_fields_fail_closed(self):
        self.answer.pop("parcel_placed")
        self.assertEqual(self.send().status_code, 503)
        self.answer["parcel_placed"] = True
        self.assertEqual(self.send().status_code, 503)

    def test_bounds_and_auth(self):
        self.assertEqual(self.client.post("/describe/sequence", json={"frames": frames(12)}).status_code, 200)
        self.requests.clear()  # Valid unauthenticated call may reach inference; next cases may not.
        for count, kw in [(4, {}), (12, {"profile": "detail"}),
                          (12, {"num_ctx": 65536}), (12, {"source_url": "https://example.com"})]:
            self.assertEqual(self.send(count, **kw).status_code, 400)
        self.assertEqual(self.requests, [])

    def test_capability(self):
        result = self.client.get("/capabilities", headers=AUTH)
        self.assertEqual(result.json["sequence_api"], 1)
        self.assertIn("/describe/sequence", result.json["endpoints"])


if __name__ == "__main__":
    unittest.main()
