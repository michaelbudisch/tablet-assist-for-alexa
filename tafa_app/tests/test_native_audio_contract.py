"""Direct tablet speech is TAFA's only conversation transport."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class NativeAudioContract(unittest.TestCase):
    def test_tafa_owned_endpoint_names_only(self):
        wake=read("custom_components/tablet_assist_for_alexa/relay/relay_wake_devices.py")
        room=read("custom_components/tablet_assist_for_alexa/relay/relay_room_adapter.py")
        admin=read("custom_components/tablet_assist_for_alexa/frontend/device_audio.js")
        self.assertIn("/api/tablet_assist_for_alexa/wake_devices",wake)
        self.assertIn("/api/tablet_assist_for_alexa/room_audio",room)
        self.assertIn("/api/tablet_assist_for_alexa/room_admin",room)
        self.assertIn("tablet_assist_for_alexa/room_admin",admin)
        for old in ["/api/jarvis_echo_relay/room_audio",
                    "/api/jarvis_tablet_audio/wake_devices"]:
            self.assertNotIn(old,wake+room)
    def test_integrated_relay_independent_of_legacy(self):
        app=read("custom_components/tablet_assist_for_alexa/__init__.py")
        self.assertIn("await setup_room_audio(hass, entry)",app)
        self.assertIn("await setup_wake_devices(hass, entry)",app)
        self.assertIn("relay_camera_started",app)
        self.assertIn("legacy_present",app)
        for name in ["relay_wake_devices.py","relay_room_adapter.py","relay_room_camera.py"]:
            f="relay/"+name
            self.assertEqual(read("custom_components/tablet_assist_for_alexa/"+f),
                             read("tafa_app/bundle/tablet_assist_for_alexa/"+f))
    def test_followups_are_per_device_and_allow_unlimited(self):
        src=read("custom_components/tablet_assist_for_alexa/relay/relay_wake_devices.py")
        self.assertIn('"followup_limit": -1',src)
        self.assertIn('"followup_limit": (-1, 100)',src)
        ui=read("custom_components/tablet_assist_for_alexa/frontend/voice_tools.js")
        self.assertIn("followupSelect",ui)
        self.assertIn("followup_limit:Number(",ui)
        service=read("android/app/src/main/java/de/jarvis/audio/WakeWordService.java")
        self.assertIn("if(answered){",service)
        self.assertNotIn("nativeFollowupCount",service)
        self.assertNotIn("native_followup_limit",service)
        self.assertNotIn("native_followup_enabled",service)
    def test_dashboard_microphone_is_a_real_ha_toggle(self):
        src=read("custom_components/tablet_assist_for_alexa/frontend/dashboard.js")
        self.assertIn("async toggleNativeMic(",src)
        self.assertIn('action:"configure",device_id:selected.device_id,settings:{muted:nextMuted}',src)
        self.assertIn("showMicChoice(devices)",src)
        self.assertIn("micDevices",src)
        self.assertIn('quick("assist",',src)
        self.assertNotIn('k==="assist"&&this.cfg.modules.includes("assist"))this.go("assist")',src)
    def test_no_old_audio_command_paths_on_android(self):
        audio=read("android/app/src/main/java/de/jarvis/audio/AudioService.java")
        native=read("android/app/src/main/java/de/jarvis/audio/NativeAssistSession.java")
        wake=read("android/app/src/main/java/de/jarvis/audio/WakePilotSettings.java")
        self.assertNotIn("input_text.jarvis_native_audio_command",audio)
        self.assertNotIn("input_text/set_value",audio)
        self.assertNotIn("jarvis_echo_relay/room_audio",audio+native)
        self.assertIn('tablet_assist_for_alexa/room_audio',audio+native)
        self.assertIn('tablet_assist_for_alexa/wake_devices',wake)
        self.assertIn("TAFA Lokal",native)
        self.assertNotIn("if(chosen==null)chosen=first",native)
    def test_version_contract(self):
        self.assertIn('version: "0.3.36"',read("tafa_app/config.yaml"))
        self.assertEqual(read("VERSION").strip(),"0.4.21")
        self.assertEqual(read("android/VERSION").strip(),"1.0.3")

if __name__=="__main__":
    unittest.main()
