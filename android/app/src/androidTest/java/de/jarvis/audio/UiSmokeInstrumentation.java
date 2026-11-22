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
    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        if (args != null) layout = args.getString("layout", "phone");
        start();
    }
    private void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    @Override public void onStart() {
        Bundle result = new Bundle();
        Activity screen = null;
        try {
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
                int orientation = ((LinearLayout) german.findViewById(R.id.columns)).getOrientation();
                check(orientation == (layout.equals("tablet") ? LinearLayout.HORIZONTAL : LinearLayout.VERTICAL), "Responsive layout");
                EditText address = german.findViewById(R.id.server_address);
                address.setText("http://192.168.1.20:8123");
                CheckBox consent = german.findViewById(R.id.allow_http);
                consent.setChecked(true);
                address.setText("http://192.168.1.21:8123");
                check(!consent.isChecked(), "Changing the origin resets HTTP consent");
                ((EditText) german.findViewById(R.id.token)).setText("header.payload.test-signature");
            });
            screenshot(german, "de-" + layout);
            ActivityMonitor languageChange = addMonitor(MainActivity.class.getName(), null, false);
            runOnMainSync(() -> german.findViewById(R.id.language_en).performClick());
            screen = waitForMonitorWithTimeout(languageChange, 10000);
            removeMonitor(languageChange);
            check(screen != null, "Language change recreated the screen");
            waitForIdleSync();
            Activity english = screen;
            runOnMainSync(() -> {
                check(english.getString(R.string.player_start).equals("Start player"), "English resources");
                check(((EditText) english.findViewById(R.id.token)).getText().toString().equals("header.payload.test-signature"), "Language change retains unsaved token in memory");
                check(((EditText) english.findViewById(R.id.server_address)).getText().toString().equals("http://192.168.1.21:8123"), "Address survives language change");
                check(!((CheckBox) english.findViewById(R.id.allow_http)).isChecked(), "Consent remains reset after language change");
                ((EditText) english.findViewById(R.id.token)).setText("");
                english.findViewById(R.id.player_start).performClick();
                check(((TextView) english.findViewById(R.id.setup_message)).getText().toString().equals(english.getString(R.string.http_consent_required)), "Localized HTTP error");
                english.findViewById(R.id.help_toggle).performClick();
                check(english.findViewById(R.id.help_details).getVisibility() == View.VISIBLE, "Help opens");
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
            screenshot(english, "en-" + layout + "-help");
            result.putString("stream", "UI smoke passed: DE/EN, responsive layout, HTTP consent, transient token, keepalive opt-in and no-Bluetooth cleanup.\n");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable error) {
            result.putString("stream", "UI SMOKE FAILED: " + error + "\n");
            finish(Activity.RESULT_CANCELED, result);
        }
    }
    private void screenshot(Activity activity, String name) throws Exception {
        waitForIdleSync();
        Bitmap bitmap = getUiAutomation().takeScreenshot();
        check(bitmap != null, "Screenshot available");
        try (FileOutputStream file = new FileOutputStream(new File(getTargetContext().getCacheDir(), name + ".png"))) {
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, file);
        }
        bitmap.recycle();
    }
}
