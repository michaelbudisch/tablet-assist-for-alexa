"""Portable TAFA Dashboard packaging and shared HA storage configuration.

No private home entity IDs or automation changes may be bundled.
"""
import ast
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"tafa_app"
HA=ROOT/"custom_components/tablet_assist_for_alexa"
BUNDLE=APP/"bundle/tablet_assist_for_alexa"


def validators():
    path=HA/"dashboard_config.py"
    src=path.read_text(encoding="utf-8")
    module=ast.parse(src)
    names={"MODULES","ROLE_DOMAINS","DEFAULT_MODULES","ENTITY","PIPELINE"}
    funcs={"default_dashboard","validate_dashboard"}
    nodes=[]
    for node in module.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(target,ast.Name) and target.id in names
            for target in node.targets):
            nodes.append(node)
        if isinstance(node,ast.FunctionDef) and node.name in funcs:
            node.decorator_list=[]
            nodes.append(node)
    scope={"re":re}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
                 str(path),"exec"),scope)
    return scope


class DashboardDelivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime=validators()

    def test_default_card_is_portable_and_valid(self):
        raw=self.runtime["default_dashboard"]()
        clean=self.runtime["validate_dashboard"](raw)
        self.assertEqual(clean["title"],"TAFA Dashboard")
        self.assertIn("assist",clean["modules"])
        self.assertEqual(clean["bindings"]["lights"],[])
        self.assertEqual(clean["type"],"custom:tafa-home-dashboard")

    def test_entity_bindings_are_per_role_and_strictly_checked(self):
        raw=self.runtime["default_dashboard"]()
        raw["bindings"]["lights"]=["light.office_lamp"]
        raw["bindings"]["solar_power"]=["sensor.pv_power"]
        raw["bindings"]["cameras"]=["camera.front_door"]
        clean=self.runtime["validate_dashboard"](raw)
        self.assertEqual(clean["bindings"]["solar_power"],["sensor.pv_power"])
        for key,wrong in [
            ("lights","sensor.not_a_light"),
            ("cameras","http://evil.test"),
            ("solar_power","sensor.invalid!"),
        ]:
            candidate=json.loads(json.dumps(raw))
            candidate["bindings"][key]=[wrong]
            with self.subTest(role=key),self.assertRaises(ValueError):
                self.runtime["validate_dashboard"](candidate)

    def test_duplicate_and_unknown_roles_rejected(self):
        raw=self.runtime["default_dashboard"]()
        for case in [
            {"bindings":{"nonexistent":["sensor.secret"]}},
            {"modules":["lights","lights"]},
            {"modules":["lights","automations"]},
            {"assist":{"malicious":"123"}},
            {"type":"custom:other-card"},
        ]:
            candidate={**raw,**case}
            with self.subTest(case=case),self.assertRaises(ValueError):
                self.runtime["validate_dashboard"](candidate)

    def test_modules_stored_in_ha_not_local_or_automation(self):
        src=(HA/"dashboard_config.py").read_text()
        self.assertIn("from homeassistant.helpers.storage import Store",src)
        self.assertIn("async_save(parsed)",src)
        self.assertIn("@websocket_api.require_admin",src)
        self.assertNotIn("automation.",src)
        self.assertNotIn("localStorage",src)

    def test_shipped_assets_are_mirrored_byte_for_byte(self):
        files=["dashboard_config.py","__init__.py","frontend/panel.js",
               "frontend/dashboard.js","frontend/dashboard_model.js",
               "frontend/voice_tools.js"]
        for p in files:
            with self.subTest(file=p):
                self.assertEqual((HA/p).read_bytes(),(BUNDLE/p).read_bytes())
        for p in ["frontend/dashboard.js","frontend/dashboard_model.js",
                  "frontend/panel.js","frontend/voice_tools.js"]:
            body=(HA/p).read_text()
            self.assertNotIn("sensor.hauptstr",body)
            self.assertNotIn("sensor.tibber_pulse_",body)
            self.assertNotIn("camera.haustur",body)
            self.assertNotIn("sensor.michas",body)
            self.assertNotIn("http://192.168.",body)

    def test_native_sidebar_opens_dashboard_not_old_voice_landing(self):
        src=(HA/"__init__.py").read_text()
        self.assertIn('sidebar_title="TAFA Dashboard"',src)
        self.assertIn('module_url="/tablet_assist_for_alexa/panel.js?v=0.4.16"',src)
        self.assertIn("async_get_dashboard",src)
        self.assertIn("async_set_dashboard",src)
        for js in ["panel.js","dashboard.js","dashboard_model.js","voice_tools.js"]:
            self.assertIn('"/tablet_assist_for_alexa/'+js+'"',src)
        panel=(HA/"frontend/panel.js").read_text()
        self.assertIn('document.createElement("tafa-integrated-dashboard")',panel)
        self.assertIn('document.createElement("tablet-assist-voice-tools")',panel)
        self.assertIn('type:"tablet_assist_for_alexa/dashboard/set"',panel)
        self.assertIn("dashboard.js?v=0.4.16",panel)
        dashboard=(HA/"frontend/dashboard.js").read_text()
        self.assertIn("./dashboard_model.js?v=0.4.16",dashboard)
        self.assertIn("tafa-open-voice-tools",dashboard)
        self.assertIn('customElements.define("tafa-integrated-dashboard"',dashboard)
        self.assertNotIn('customElements.define("tafa-home-dashboard"',dashboard)
        self.assertIn('tafa-integrated-dashboard-editor',panel)

    def test_version_and_docs_consistent(self):
        self.assertIn('version: "0.3.31"',(APP/"config.yaml").read_text())
        self.assertEqual((ROOT/"VERSION").read_text().strip(),"0.4.16")
        self.assertIn('"version": "0.4.16"',(HA/"manifest.json").read_text())
        self.assertIn("0.3.31",(APP/"CHANGELOG.md").read_text())


if __name__=="__main__":
    unittest.main()
