package de.jarvis.audio;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.ComponentName;
import android.content.Intent;
import android.graphics.Bitmap;
import android.media.MediaPlayer;
import android.content.res.AssetFileDescriptor;
import android.os.Bundle;
import android.view.View;
import android.widget.*;
import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;

/** Runs on an isolated emulator. No real token, HA server or Bluetooth device is used. */
public class UiSmokeInstrumentation extends Instrumentation {
    private String layout = "phone";
    private boolean streamOnly;
    private boolean cameraOnly;
    private boolean relayOnly;
    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        if (args != null) layout = args.getString("layout", "phone");
        streamOnly = args != null && args.getString("stream_only", "false").equals("true");
        cameraOnly = args != null && args.getString("camera_only", "false").equals("true");
        relayOnly = args != null && args.getString("relay_only", "false").equals("true");
        start();
    }
    private void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    @Override public void onStart() {
        Bundle result = new Bundle();
        Activity screen = null;
        try {
            if(relayOnly){result.putString("stream", CameraRelaySmoke.run(this));finish(Activity.RESULT_OK,result);return;}
            if (cameraOnly) {
                result.putString("stream", CameraSmoke.run(this));
                finish(Activity.RESULT_OK, result);
                return;
            }
            if (streamOnly) {
                result.putString("stream", StreamingSmoke.run(this));
                finish(Activity.RESULT_OK, result);
                return;
            }
            getTargetContext().getSharedPreferences(MainActivity.PREF, 0).edit().clear().putString("ui_language", "de").commit();
            MediaPlayer silenceDecoder = new MediaPlayer();
            try (AssetFileDescriptor source = getTargetContext().getResources().openRawResourceFd(R.raw.keepalive_silence)) {
                silenceDecoder.setDataSource(source.getFileDescriptor(), source.getStartOffset(), source.getLength());
                silenceDecoder.prepare();
                check(silenceDecoder.getDuration() == 1000, "Bundled silent WAV decodes without playing audio");
            } finally { silenceDecoder.release(); }
            Intent launch = new Intent().setComponent(new ComponentName(getTargetContext(), MainActivity.class)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            screen = startActivitySync(launch);
            waitForIdleSync();
            Activity german = screen;
            runOnMainSync(() -> {
                check(german.getString(R.string.player_start).equals("Player starten"), "German resources");
                check(!((CheckBox) german.findViewById(R.id.keepalive)).isChecked(), "Keepalive defaults off");
                check(german.getString(R.string.app_name).equals("TAFA Device Bridge"), "Rebranded app name");
                check(german.findViewById(R.id.section_connection).getVisibility() == View.VISIBLE, "First setup opens Connect");
                german.findViewById(R.id.nav_settings).performClick();
                check(german.findViewById(R.id.section_settings).getVisibility() == View.VISIBLE, "Settings navigation opens");
                check(german.findViewById(R.id.section_connection).getVisibility() == View.GONE, "Only selected section is shown");
                check(!german.findViewById(R.id.wake_advanced).isShown(),"Advanced settings start collapsed");
                View advanced=german.findViewById(R.id.section_settings).findViewWithTag("settings_group_3");
                check(advanced!=null,"Advanced settings group exists");
                advanced.performClick();
                check(german.findViewById(R.id.wake_advanced).isShown(),"Advanced controls expand");
                View audioGroup=german.findViewById(R.id.section_settings).findViewWithTag("settings_group_0");
                audioGroup.performClick();
                Spinner output=german.findViewById(R.id.audio_output_mode);
                check(output.isShown()&&output.getAdapter().getCount()==3,"Three audio output modes");
                check(output.getSelectedItemPosition()==0,"Automatic output default");
                check(!german.findViewById(R.id.wake_advanced).isShown(),"Only one settings group expands");
                audioGroup.performClick();
                check(german.findViewById(R.id.camera_relay_start).getVisibility()==View.VISIBLE,
                        "Camera controls are included in Settings");
                check(german.findViewById(R.id.display_permission).getVisibility()==View.VISIBLE,
                        "Display permission is included in Settings");
                Spinner followups=german.findViewById(R.id.native_followup_limit);
                check(followups.getAdapter().getCount()==15,"Wakeword only, finite limits through 100 and unlimited");
                check(followups.getAdapter().getItem(13).toString().equals(
                        german.getResources().getQuantityString(R.plurals.followup_count,100,100)),
                        "100 follow-ups available");
                check(followups.getAdapter().getItem(14).toString().equals(german.getString(R.string.followup_unlimited)),
                        "Unlimited follow-ups require an explicit choice");
                check(followups.getSelectedItemPosition()==0,"Every question requires wakeword by default");
                german.findViewById(R.id.nav_status).performClick();
                check(german.findViewById(R.id.status_connect).isShown(),"Status offers Connect");
                check(german.findViewById(R.id.status_speak).isShown(),"Status offers Speak now");
                check(german.findViewById(R.id.status_wake).isShown(),"Status offers wakeword start");
                german.findViewById(R.id.status_connect).performClick();
                check(german.findViewById(R.id.section_connection).isShown(),"Missing credentials open Connect");
                check(!AudioService.running&&!WakeWordService.running,"Invalid quick connection starts no services");
                german.findViewById(R.id.nav_connection).performClick();
                int orientation = ((LinearLayout) german.findViewById(R.id.columns)).getOrientation();
                check(orientation == (layout.equals("tablet") ? LinearLayout.HORIZONTAL : LinearLayout.VERTICAL), "Responsive layout");
                EditText address = german.findViewById(R.id.server_address);
                address.setText("http://192.168.1.20:8123");
                CheckBox consent = german.findViewById(R.id.allow_http);
                consent.setChecked(true);
                address.setText("http://192.168.1.21:8123");
                check(!consent.isChecked(), "Changing the origin resets HTTP consent");
                ((EditText) german.findViewById(R.id.token)).setText("header.payload.test-signature");
                german.findViewById(R.id.nav_settings).performClick();
                check(((EditText)german.findViewById(R.id.token)).getText().toString().equals("header.payload.test-signature"), "Tab switches retain unsaved token in memory");
            });
            runOnMainSync(() -> german.findViewById(R.id.section_settings)
                    .findViewWithTag("settings_group_1").performClick());
            waitForIdleSync();
            runOnMainSync(() -> {
                Spinner followups=german.findViewById(R.id.native_followup_limit);
                check(followups.isShown(),"Follow-up selector is visible in the voice group");
                followups.setSelection(3);
            });
            waitForIdleSync();
            runOnMainSync(() -> check(german.getSharedPreferences(MainActivity.PREF,0)
                    .getInt(FollowupPolicy.LOCAL_LIMIT,0)==3,"Visible follow-up selection persists"));
            screenshot(german, "de-" + layout);
            runOnMainSync(() -> german.findViewById(R.id.nav_status).performClick());
            screenshot(german, "de-" + layout + "-status");
            runOnMainSync(() -> german.findViewById(R.id.nav_connection).performClick());
            screenshot(german, "de-" + layout + "-connection");
            runOnMainSync(() -> german.findViewById(R.id.nav_settings).performClick());

            ActivityMonitor languageChange = addMonitor(MainActivity.class.getName(), null, false);
            runOnMainSync(() -> german.findViewById(R.id.language_en).performClick());
            screen = waitForMonitorWithTimeout(languageChange, 10000);
            removeMonitor(languageChange);
            check(screen != null, "Language change recreated the screen");
            waitForIdleSync();
            Activity english = screen;
            runOnMainSync(() -> {
                check(english.getString(R.string.player_start).equals("Start player"), "English resources");
                check(((Spinner)english.findViewById(R.id.native_followup_limit)).getSelectedItemPosition()==3,
                        "Local follow-up ceiling survives language change");
                check(english.getSharedPreferences(MainActivity.PREF,0).getInt(FollowupPolicy.LOCAL_LIMIT,0)==3,
                        "Local follow-up selection persists independently of HA");
                ((Spinner)english.findViewById(R.id.native_followup_limit)).setSelection(0);
                check(english.findViewById(R.id.section_settings).getVisibility() == View.VISIBLE, "Selected tab survives language change");
                check(english.findViewById(R.id.wake_advanced).getVisibility() == View.VISIBLE, "Settings remain visible after recreation");
                check(((EditText) english.findViewById(R.id.token)).getText().toString().equals("header.payload.test-signature"), "Language change retains unsaved token in memory");
                check(((EditText) english.findViewById(R.id.server_address)).getText().toString().equals("http://192.168.1.21:8123"), "Address survives language change");
                check(!((CheckBox) english.findViewById(R.id.allow_http)).isChecked(), "Consent remains reset after language change");
                ((EditText) english.findViewById(R.id.token)).setText("");
                english.findViewById(R.id.nav_settings).performClick();
                english.findViewById(R.id.player_start).performClick();
                check(((TextView) english.findViewById(R.id.setup_message)).getText().toString()
                        .equals(english.getString(R.string.http_consent_required)), "Localized HTTP error");
                english.findViewById(R.id.help_toggle).performClick();
                check(english.findViewById(R.id.help_details).getVisibility()==View.VISIBLE,
                        "Help is part of Settings");
                CheckBox keepalive = english.findViewById(R.id.keepalive);
                keepalive.setChecked(true);
                check(english.getSharedPreferences(MainActivity.PREF, 0).getBoolean("keepalive_enabled", false), "Keepalive choice persists");
                check(!AudioService.running && AudioService.keepaliveStatus.equals("off"), "Keepalive never starts the player by itself");
                keepalive.setChecked(false);
                ArrayList<String> statuses = new ArrayList<>();
                BluetoothKeepalive loop = new BluetoothKeepalive(english, statuses::add);
                loop.setEnabled(true);
                check(statuses.contains("waiting"), "No Bluetooth means waiting, no fallback to speaker");
                loop.close();
                check(statuses.get(statuses.size()-1).equals("off"), "Closing keepalive releases it");
            });
            screenshot(english, "en-" + layout);
            runOnMainSync(() -> ((ScrollView) english.findViewById(R.id.page_content).getParent()).fullScroll(View.FOCUS_DOWN));
            waitForIdleSync();
            screenshot(english, "en-" + layout + "-settings");
            runOnMainSync(() -> {
                english.findViewById(R.id.nav_settings).performClick();
                Spinner intervals=english.findViewById(R.id.camera_refresh_rate);
                check(intervals.getAdapter().getCount()==5,
                        "Camera refresh options retained directly in Settings");
                check(english.findViewById(R.id.camera_motion).getVisibility()==View.VISIBLE,
                        "Motion detection switch is in Settings");
                english.findViewById(R.id.nav_status).performClick();
                check(english.findViewById(R.id.section_settings).getVisibility()==View.GONE,
                        "Status hides Settings");
            });
            screenshot(english,"en-"+layout+"-status");
            result.putString("stream", "UI smoke passed: status quick actions, wakeword-only default, bounded follow-up settings, TAFA branding, navigation, disclosure/recreation, DE/EN, responsive layout, HTTP consent, transient token, keepalive opt-in and no-Bluetooth cleanup.\n");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable error) {
            result.putString("stream", "UI SMOKE FAILED: " + error + "\n");
            finish(Activity.RESULT_CANCELED, result);
        }
    }
    private void screenshot(Activity activity, String name) throws Exception {
        waitForIdleSync();
        if (android.os.Build.VERSION.SDK_INT >= 29) {
            java.util.concurrent.CountDownLatch frame = new java.util.concurrent.CountDownLatch(1);
            runOnMainSync(() -> {
                View decor = activity.getWindow().getDecorView();
                decor.getViewTreeObserver().registerFrameCommitCallback(frame::countDown);
                decor.invalidate();
            });
            check(frame.await(5, java.util.concurrent.TimeUnit.SECONDS), "Screenshot frame rendered");
        }
        getUiAutomation().waitForIdle(100, 5000);
        Bitmap bitmap = getUiAutomation().takeScreenshot();
        check(bitmap != null, "Screenshot available");
        try (FileOutputStream file = new FileOutputStream(new File(getTargetContext().getCacheDir(), name + ".png"))) {
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, file);
        }
        bitmap.recycle();
    }
}
