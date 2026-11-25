import base64
import io
import unittest
import json
from PIL import Image
from server import create_app, DEFAULT_MODEL, MAX_BYTES, ModelUnavailable

HEADERS = {}

def fixture():
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), "blue").save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()

class VisionTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def fake(path, data=None, timeout=8):
            self.calls.append((path, data, timeout))
            if path == "/api/tags":
                return {"models": [{"name": DEFAULT_MODEL}]}
            if path == "/api/ps":
                return {"models": [{"name": DEFAULT_MODEL, "size_vram": 3500000000, "context_length": 4096},
                    {"name": "private-unrelated-model", "secret": "not exposed"}]}
            return {"message": {"content": "Eine blaue Fläche."}}
        self.client = create_app( call=fake).test_client()
    def post(self, data):
        return self.client.post("/describe", json=data, headers=HEADERS)
    def test_tokenless_private_lan(self):
        self.assertEqual(self.client.post("/describe", json={"image": fixture()}).status_code, 200)
        self.assertEqual(len(self.calls), 1)
    def test_health(self):
        self.assertTrue(self.client.get("/health", headers=HEADERS).json["ready"])
    def test_description(self):
        r = self.post({"image": fixture()})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["model"], DEFAULT_MODEL)
        self.assertEqual(r.headers["Cache-Control"], "no-store")
        path, body, _ = self.calls[0]
        self.assertEqual(path, "/api/chat")
        self.assertEqual(body["keep_alive"], 0)
        self.assertFalse(body["stream"])
        self.assertEqual(len(body["messages"][1]["images"]), 1)
        self.assertTrue(base64.b64decode(body["messages"][1]["images"][0]).startswith(b"\xff\xd8"))
    def test_alternative(self):
        self.assertEqual(self.post({"image":fixture(),"model":"gemma3:4b","mode":"objects"}).status_code,200)
        self.assertEqual(self.calls[0][1]["model"], "gemma3:4b")
    def test_capabilities_and_vision_queue(self):
        response = self.client.get("/capabilities", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["worker_version"], "2.2.0")
        self.assertEqual(response.json["priority_queue"]["scope"], "vision-only")
        result = self.post({"image": fixture(), "priority": "background", "wait_ms": 50})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.client.get("/health", headers=HEADERS).json["queue_depth"], 0)

    def test_invalid_queue_controls(self):
        for option in ({"priority": "admin"}, {"wait_ms": -1}, {"wait_ms": True},
                       {"wait_ms": 999999}, {"wait_ms": "5"}):
            with self.subTest(option=option):
                self.assertEqual(self.post({"image": fixture(), **option}).status_code, 400)
        self.assertEqual(self.calls, [])

    def test_residency_and_matching_context(self):
        self.assertEqual(self.post({"image":fixture(),"keep_alive":300,"num_ctx":2048}).status_code,200)
        self.assertEqual(self.calls[0][1]["keep_alive"],300)
        self.assertEqual(self.calls[0][1]["options"]["num_ctx"],2048)
        self.assertFalse(self.calls[0][1]["think"])
    def test_residency_limits(self):
        for extra in ({"keep_alive":-1},{"keep_alive":True},{"keep_alive":"300s"},{"keep_alive":86400},{"num_ctx":131072},{"num_ctx":True}):
            with self.subTest(extra=extra):
                self.assertEqual(self.post({"image":fixture(),**extra}).status_code,400)
        self.assertEqual(self.calls,[])
    def test_runtime_no_loading_or_private_models(self):
        result=self.client.get("/runtime",headers=HEADERS)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json["settings_api"],1)
        self.assertEqual(result.json["vision_models"],[DEFAULT_MODEL])
        self.assertEqual(len(result.json["loaded"]),1)
        self.assertEqual([x[0] for x in self.calls],["/api/tags","/api/ps"])
        self.assertEqual(self.client.get("/runtime").status_code,200)
    def test_generic_people_without_identity(self):
        self.assertEqual(self.post({"image":fixture(),"mode":"scene"}).status_code,200)
        system=self.calls[0][1]["messages"][0]["content"]
        instruction=self.calls[0][1]["messages"][1]["content"]
        self.assertIn("sichtbare Personen allgemein",system)
        self.assertIn("keine Namen oder Identitäten",system)
        self.assertIn("getragener Gegenstände",instruction)
    def test_invalid_model_mode_and_extra(self):
        for extra in ({"model":"remote-cloud"}, {"mode":"identify"}, {"url":"https://example.org"}, {"question":"free text"}, {"mode":[]}, {"model":{}}):
            with self.subTest(extra=extra):
                self.assertEqual(self.post({"image": fixture(), **extra}).status_code, 400)
        self.assertEqual(self.calls, [])
    def test_invalid_image(self):
        for image in ("invalid", "a" * (MAX_BYTES * 2), base64.b64encode(b"not an image").decode(), None):
            with self.subTest():
                self.assertIn(self.post({"image": image}).status_code, (400,413))
        self.assertEqual(self.calls, [])
    def test_offline_missing_model(self):
        def fail(*args, **kwargs):
            raise ModelUnavailable()
        c = create_app( call=fail).test_client()
        self.assertEqual(c.post("/describe", json={"image":fixture()}, headers=HEADERS).status_code, 503)
        self.assertEqual(c.get("/health",headers=HEADERS).status_code,503)
    def test_no_auth_header_required(self):
        self.assertEqual(self.client.get("/health").status_code,200)

    def test_structured_detection(self):
        detection={"person_count":1,"dog_count":0,"age_groups":["adult"],"genders":["woman"],"uncertain":False}
        calls=[]
        def fake(path,data=None,timeout=8):
            calls.append(data)
            return {"message":{"content":json.dumps(detection)}}
        client=create_app(call=fake).test_client()
        response=client.post("/detect",json={"image":fixture(),"keep_alive":300,"num_ctx":2048},headers=HEADERS)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json["labels"],["person","adult","woman"])
        self.assertEqual(calls[0]["format"]["additionalProperties"],False)
        self.assertFalse(calls[0]["think"])
        self.assertEqual(calls[0]["keep_alive"],300)
        self.assertEqual(calls[0]["options"]["num_ctx"],2048)
        self.assertIn("Never identify",calls[0]["messages"][0]["content"])
        self.assertIn("genders",calls[0]["format"]["properties"])
        self.assertEqual(client.post("/detect",json={"image":fixture()}).status_code,200)

    def test_invalid_or_uncertain_detection_never_selects_an_action(self):
        from detection import validate, labels
        valid={"person_count":1,"dog_count":1,"age_groups":["unknown"],"genders":["unknown"],"uncertain":True}
        self.assertEqual(labels(validate(valid)),[])
        for invalid in ({**valid,"person_count":True},{**valid,"person_count":-1},{**valid,"age_groups":["man"]},
                {**valid,"name":"Michael"},{**valid,"age_groups":[]},{**valid,"age_groups":["adult","adult"]},{**valid,"genders":["male"]},{**valid,"genders":[]},{**valid,"person_count":0,"age_groups":[],"genders":["man"]},
                {**valid,"person_count":0,"age_groups":["child"]}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):validate(invalid)
        def fake(*args,**kwargs):return {"message":{"content":'go open a door'}}
        client=create_app(call=fake).test_client()
        self.assertEqual(client.post("/detect",json={"image":fixture()},headers=HEADERS).status_code,503)
        self.assertEqual(client.post("/detect",json={"image":fixture(),"action":"script.anything"},headers=HEADERS).status_code,400)

if __name__ == "__main__":
    unittest.main()
