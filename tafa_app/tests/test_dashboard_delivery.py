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
    names={"MODULES","ROLE_DOMAINS","DEFAULT_MODULES","PRESENTATION_DEFAULTS","ENTITY","PIPELINE"}
    funcs={"default_dashboard","validate_dashboard","migrate_saved_dashboard"}
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

    def test_legacy_dashboard_is_repaired_without_overwriting_valid_choices(self):
        legacy=self.runtime["default_dashboard"]()
        legacy["modules"]=["assist","fuel","retired_feature"]
        legacy["bindings"]["fuel_volume"]=["sensor.oil_actual"]
        legacy["bindings"]["obsolete_role"]=["sensor.not_used"]
        legacy["presentation"]["unusedSetting"]=True
        legacy["unknown_legacy_key"]="leave in snapshot"
        restored=self.runtime["migrate_saved_dashboard"](legacy)
        self.assertEqual(restored["modules"],["assist","fuel"])
        self.assertEqual(restored["bindings"]["fuel_volume"],["sensor.oil_actual"])
        self.assertEqual(restored["presentation"]["captions"],True)
        self.assertNotIn("obsolete_role",restored["bindings"])
        self.assertNotIn("unknown_legacy_key",restored)
        backend=(HA/"dashboard_config.py").read_text()
        self.assertIn('dashboard_backup_store(hass).async_save(existing)',backend)
        self.assertIn('migrate_saved_dashboard(data)',backend)

    def test_central_voice_sources_offer_dashboard_fallback_links(self):
        backend=(HA/"dashboard_config.py").read_text()
        self.assertIn('"heizoel": "fuel_volume"',backend)
        self.assertIn('"vorlauf": "heating_temperature"',backend)
        self.assertIn('linked_source_bindings(hass)',backend)
        panel=(HA/"frontend/panel.js").read_text()
        self.assertIn("_effectiveConfig()",panel)
        self.assertIn('result.linked_bindings||{}',panel)

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

    def test_no_sidebar_dashboard_is_created(self):
        src=(HA/"__init__.py").read_text()
        self.assertNotIn('sidebar_title="TAFA Dashboard"',src)
        self.assertNotIn("async_register_panel(",src)
        self.assertIn("async_get_dashboard",src)
        self.assertIn("async_set_dashboard",src)
        self.assertIn('active_platforms = PLATFORMS',src)
        self.assertIn('await setup_relay_camera(hass, entry)',src)
        self.assertNotIn('if legacy_present else PLATFORMS',src)
        self.assertIn('active_platforms',src)
        self.assertIn('async_unload_platforms(entry, active_platforms)',src)
        for js in ["panel.js","dashboard.js","dashboard_model.js","voice_tools.js","response_overlay.js"]:
            self.assertIn('"/tablet_assist_for_alexa/'+js+'"',src)
        panel=(HA/"frontend/panel.js").read_text()
        self.assertIn('document.createElement("tafa-integrated-dashboard")',panel)
        self.assertIn('document.createElement("tablet-assist-voice-tools")',panel)
        self.assertIn('type:"tablet_assist_for_alexa/dashboard/set"',panel)
        self.assertIn("dashboard.js?v=0.4.38-search-recipe",panel)
        dashboard=(HA/"frontend/dashboard.js").read_text()
        self.assertIn("./dashboard_model.js?v=0.4.32",dashboard)
        self.assertIn("installTafaResponseOverlay",dashboard)
        self.assertIn("response_overlay.js?v=0.4.38",dashboard)
        self.assertIn("data-presentation",dashboard)
        overlay=(HA/"frontend/response_overlay.js").read_text()
        self.assertIn("tafa_assist_response",overlay)
        self.assertIn("data-source",overlay)
        self.assertIn("tablet_assist_for_alexa/search",overlay)
        self.assertIn("knowledgeMedia",overlay)
        self.assertIn("tafa-open-voice-tools",dashboard)
        # "TAFA" now stays in the native dashboard navigation, not in a
        # separate fullscreen page with an unrelated header.
        self.assertIn('const voice=document.createElement("tablet-assist-voice-tools")',dashboard)
        self.assertIn("voice.embedded=true",dashboard)
        self.assertIn("this.voiceTools?.isConnected",dashboard)
        self.assertNotIn('if(id==="assist"&&this.cfg.modules.includes("assist"))',dashboard)
        self.assertIn("d.panel=this._panel",panel)
        self.assertIn('window.location.search',panel)
        self.assertIn('get("view")==="voice"',panel)
        voice=(HA/"frontend/voice_tools.js").read_text()
        self.assertIn("TAFA_VOICE_STYLE",voice)
        self.assertIn(":host([embedded])",voice)
        self.assertIn("var(--card,#1b2430)",voice)
        self.assertIn("var(--acc,#38c5ae)",voice)
        self.assertIn("voice-standalone-link",voice)
        self.assertIn("view=voice",voice)

        self.assertIn('tafa-open-dashboard-editor',dashboard)
        self.assertIn('d.addEventListener("tafa-open-dashboard-editor"',panel)
        self.assertNotIn('className="toolbar"',panel)
        self.assertIn('className="subview-nav"',panel)
        self.assertIn('if(this._mode==="voice"||this._editing)',panel)
        self.assertIn('if(this.page==="assist")return "";',dashboard)
        self.assertIn('if(this.page==="assist"){\n  this.clearAssist();',dashboard)
        self.assertIn('if(id==="settings"&&this.h?.user?.is_admin)',dashboard)

        self.assertIn('customElements.define("tafa-integrated-dashboard"',dashboard)
        self.assertNotIn('customElements.define("tafa-home-dashboard"',dashboard)
        self.assertIn('tafa-integrated-dashboard-editor',panel)

    def test_dashboard_microphone_is_native_websocket_backed(self):
        dashboard=(HA/"frontend/dashboard.js").read_text()
        self.assertIn('action:"configure",device_id:selected.device_id,settings',dashboard)
        self.assertIn('voice_mode:next==="off"?"continuous":next',dashboard)
        self.assertIn('this.micNext(this.micMode(selected))',dashboard)
        self.assertIn('this.micModeText(mode,de)',dashboard)
        self.assertIn('control?.pending',dashboard)
        self.assertIn('Nicht von App bestätigt',dashboard)
        self.assertIn('Date.now()-requested',dashboard)
        self.assertIn('this.showMicChoice(devices)',dashboard)
        self.assertIn('this.micIndicator().icon',dashboard)
        self.assertIn('void this.refreshMic(true)',dashboard)
        self.assertNotIn('getUserMedia(',dashboard)
        self.assertNotIn('jarvis_tablet_audio/wake_devices',dashboard)

    def test_optional_search_and_visual_response_contracts(self):
        import ast
        for name in ("web_search.py","local_data.py","conversation.py","dashboard_config.py"):
            ast.parse((HA/name).read_text(), filename=name)
            self.assertEqual((HA/name).read_text(),(APP/"bundle/tablet_assist_for_alexa"/name).read_text())
        backend=(HA/"conversation.py").read_text()
        self.assertIn('"tafa_assist_response"',backend)
        self.assertIn("self._announce_response(user_input, speech, chat_log)",backend)
        self.assertIn("search_command", (HA/"__init__.py").read_text())
        self.assertIn('"search_base"', (HA/"app_settings.py").read_text())
        self.assertIn("PRESENTATION_DEFAULTS", (HA/"dashboard_config.py").read_text())
        self.assertIn('search_base: str',(APP/"config.yaml").read_text())
        self.assertIn('family_name_child: str',(APP/"config.yaml").read_text())

    def test_version_and_docs_consistent(self):
        self.assertIn('version: "0.4.40"',(APP/"config.yaml").read_text())
        self.assertEqual((ROOT/"VERSION").read_text().strip(),"0.4.40")
        self.assertIn('"version": "0.4.40"',(HA/"manifest.json").read_text())
        self.assertIn("0.3.52",(APP/"CHANGELOG.md").read_text())


if __name__=="__main__":
    unittest.main()
