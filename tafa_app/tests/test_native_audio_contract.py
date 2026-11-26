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
    def test_player_enrolls_even_without_wakeword(self):
        audio=read("android/app/src/main/java/de/jarvis/audio/AudioService.java")
        self.assertIn("enrollmentIo.scheduleWithFixedDelay(this::syncTabletEnrollment",audio)
        self.assertIn("WakePilotSettings.register(this);",audio)
        self.assertIn('WakePilotSettings.report(this,"audio_ready","inactive");',audio)
        self.assertIn("if(!active||!haConnected)return;",audio)
        self.assertIn("enrollmentIo.shutdownNow()",audio)
        self.assertIn("if(!WakeWordService.running)",audio)

    def test_bluetooth_keepalive_visible_and_recovers(self):
        layout=read("android/app/src/main/res/layout/activity_main.xml")
        service=read("android/app/src/main/java/de/jarvis/audio/BluetoothKeepalive.java")
        player=read("android/app/src/main/java/de/jarvis/audio/AudioService.java")
        self.assertEqual(layout.count('android:id="@+id/keepalive"'),1)
        self.assertIn('android:id="@+id/keepalive_status"',layout)
        self.assertNotIn('android:id="@+id/bluetooth_advanced"',layout)
        self.assertIn('retryAt = SystemClock.elapsedRealtime()',service)
        self.assertIn('KeepaliveRetry.delayMs(failures)',service)
        self.assertIn('current.setLooping(true)',service)
        self.assertIn('current.setVolume(1, 1)',service)
        self.assertIn('keepalive.setEnabled(prefs.getBoolean("keepalive_enabled",false))',player)
        self.assertIn("enrollmentIo.scheduleWithFixedDelay",player)
        self.assertNotIn("enabled = false;",service.split("void pauseForFocus()",1)[1].split("void close()",1)[0])

    def test_camera_uses_tafa_only(self):
        cam=read("android/app/src/main/java/de/jarvis/audio/CameraUploadClient.java")
        svc=read("android/app/src/main/java/de/jarvis/audio/CameraRelayService.java")
        smoke=read("android/app/src/androidTest/java/de/jarvis/audio/CameraRelaySmoke.java")
        self.assertIn('API="/api/tablet_assist_for_alexa/room_camera"',cam)
        self.assertNotIn("/api/jarvis_echo_relay",cam+svc+smoke)
        self.assertNotIn("room_audio_enabled",svc)
        self.assertIn("POST /api/tablet_assist_for_alexa/room_camera/register",smoke)
        self.assertIn("POST /api/tablet_assist_for_alexa/room_camera/frame",smoke)

    def test_unified_settings_and_motion_binary_sensor(self):
        layout=read("android/app/src/main/res/layout/activity_main.xml")
        main=read("android/app/src/main/java/de/jarvis/audio/MainActivity.java")
        camera=read("android/app/src/main/java/de/jarvis/audio/CameraRelayService.java")
        binary=read("custom_components/tablet_assist_for_alexa/relay/binary_sensor.py")
        manifest=read("android/app/src/main/AndroidManifest.xml")
        self.assertEqual(layout.count('android:id="@+id/nav_status"'),1)
        self.assertEqual(layout.count('android:id="@+id/nav_connection"'),1)
        self.assertEqual(layout.count('android:id="@+id/nav_settings"'),1)
        for id in ("player_start","player_stop","keepalive","display_permission",
                   "camera_relay_start","camera_relay_stop","camera_motion","camera_refresh_rate"):
            self.assertEqual(layout.count('android:id="@+id/'+id+'"'),1)
        self.assertIn('android:id="@+id/section_settings"',layout)
        self.assertNotIn('android:id="@+id/nav_help"',layout)
        self.assertNotIn('android:id="@+id/nav_voice"',layout)
        self.assertNotIn('android:id="@+id/camera_preview"',layout)
        self.assertNotIn('android:id="@+id/camera_capture"',layout)
        self.assertNotIn('<activity android:name=".CameraActivity"',manifest)
        self.assertIn('getBoolean("camera_motion",false)',camera)
        self.assertIn("BinarySensorDeviceClass.MOTION",binary)
        self.assertIn("RoomRelayMotion",binary)
        self.assertIn("R.id.section_settings",main)

    def test_version_contract(self):
        self.assertIn('version: "0.3.40"',read("tafa_app/config.yaml"))
        self.assertEqual(read("VERSION").strip(),"0.4.24")
        self.assertEqual(read("android/VERSION").strip(),"1.1.0")

if __name__=="__main__":
    unittest.main()
