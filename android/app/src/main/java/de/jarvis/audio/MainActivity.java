package de.jarvis.audio;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.os.Bundle;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.widget.*;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.security.KeyStore;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import com.google.zxing.client.android.Intents;
import com.journeyapps.barcodescanner.ScanOptions;

public class MainActivity extends Activity {
    static final String PREF = "jarvis_audio", KEY = "jarvis_audio_credentials", HTTP_CONSENT = "http_consent_base";
    private static final int SCAN_TOKEN = 100;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable refresh = new Runnable() {
        public void run() { refreshStatus(); handler.postDelayed(this, 1000); }
    };
    private EditText urlInput, tokenInput;
    private CheckBox allowHttp;
    private String consentForAddress = "";
    private TextView setupMessage, searchMessage;
    private Button searchButton;
    private LinearLayout searchResults;
    private HaDiscovery discovery;
    private boolean didAutoSearch;
    private int resultCount;

    @Override protected void attachBaseContext(Context base) { super.attachBaseContext(AppLanguage.wrap(base)); }

    private static SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (!store.containsAlias(KEY)) {
            KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(KEY, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
            generator.generateKey();
        }
        return (SecretKey) store.getKey(KEY, null);
    }

    static String encrypt(String value) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key());
        return Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP) + ":"
                + Base64.encodeToString(cipher.doFinal(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)), Base64.NO_WRAP);
    }

    static String decrypt(String value) throws Exception {
        String[] parts = value.split(":", 2);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)));
        return new String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), java.nio.charset.StandardCharsets.UTF_8);
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_main);
        configureColumns();
        var prefs = getSharedPreferences(PREF, 0);
        urlInput = findViewById(R.id.server_address);
        tokenInput = findViewById(R.id.token);
        allowHttp = findViewById(R.id.allow_http);
        setupMessage = findViewById(R.id.setup_message);
        searchButton = findViewById(R.id.search);
        searchMessage = findViewById(R.id.search_message);
        searchResults = findViewById(R.id.search_results);
        urlInput.setText(state == null ? prefs.getString("base", "") : state.getString("setup_base", ""));
        Object pendingToken = getLastNonConfigurationInstance();
        if (pendingToken instanceof String) tokenInput.setText((String) pendingToken);
        ((TextView) findViewById(R.id.token_note)).setText(prefs.contains("secret") ? R.string.token_saved : R.string.token_storage);
        ((TextView) findViewById(R.id.footer)).setText(getString(R.string.footer, BuildConfig.VERSION_NAME));

        allowHttp.setOnCheckedChangeListener((button, checked) -> consentForAddress = checked ? normalizedInput() : "");
        urlInput.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            public void onTextChanged(CharSequence s, int start, int before, int count) { updateHttpConsent(); }
            public void afterTextChanged(Editable s) {}
        });
        updateHttpConsent();
        String savedConsent = state == null ? prefs.getString(HTTP_CONSENT, "") : state.getString(HTTP_CONSENT, "");
        if (HaAddress.isHttp(urlInput.getText().toString()) && !savedConsent.isEmpty()
                && savedConsent.equals(normalizedInput())) allowHttp.setChecked(true);

        findViewById(R.id.bluetooth_settings).setOnClickListener(v -> startActivity(new Intent(android.provider.Settings.ACTION_BLUETOOTH_SETTINGS)));
        findViewById(R.id.scan_token).setOnClickListener(v -> scanToken());
        findViewById(R.id.player_start).setOnClickListener(v -> startPlayer());
        findViewById(R.id.player_stop).setOnClickListener(v -> {
            stopService(new Intent(this, AudioService.class));
            setupMessage.setText("");
        });
        searchButton.setOnClickListener(v -> {
            if (discovery == null) searchHomeAssistant();
            else { stopDiscovery(); searchMessage.setText(R.string.search_finished); }
        });
        findViewById(R.id.diagnostics_toggle).setOnClickListener(v -> toggle(R.id.diagnostics_text));
        findViewById(R.id.help_toggle).setOnClickListener(v -> {
            boolean visible = toggle(R.id.help_details);
            ((Button) v).setText(visible ? R.string.help_collapse : R.string.help_expand);
        });
        findViewById(R.id.forget).setOnClickListener(v -> new AlertDialog.Builder(this)
                .setTitle(R.string.forget_title).setMessage(R.string.forget_help)
                .setNegativeButton(R.string.cancel, null).setPositiveButton(R.string.forget, (dialog, which) -> {
                    stopService(new Intent(this, AudioService.class));
                    stopDiscovery();
                    prefs.edit().remove("base").remove("secret").remove(HTTP_CONSENT).apply();
                    tokenInput.setText(""); urlInput.setText("");
                    searchResults.removeAllViews(); searchMessage.setText("");
                    setupMessage.setText(R.string.credentials_removed);
                    ((TextView) findViewById(R.id.token_note)).setText(R.string.token_storage);
                }).show());
        CheckBox keepalive = findViewById(R.id.keepalive);
        keepalive.setChecked(prefs.getBoolean("keepalive_enabled", false));
        keepalive.setOnCheckedChangeListener((button, enabled) -> {
            prefs.edit().putBoolean("keepalive_enabled", enabled).apply();
            if (AudioService.running) startService(new Intent(this, AudioService.class).setAction("update_keepalive"));
        });
        languageButton(R.id.language_de, "de");
        languageButton(R.id.language_en, "en");
        didAutoSearch = state != null && state.getBoolean("did_auto_search", false);
    }

    private void configureColumns() {
        int width = getResources().getConfiguration().screenWidthDp;
        if (width >= 840 && getResources().getConfiguration().fontScale < 1.4f) {
            ((LinearLayout) findViewById(R.id.columns)).setOrientation(LinearLayout.HORIZONTAL);
            findViewById(R.id.setup_column).setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.15f));
            LinearLayout.LayoutParams right = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
            right.setMarginStart(dp(20));
            findViewById(R.id.player_column).setLayoutParams(right);
        }
        if (width > 1180) findViewById(R.id.page_content).setLayoutParams(
                new FrameLayout.LayoutParams(dp(1180), FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL));
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    private void languageButton(int id, String language) {
        Button button = findViewById(id);
        boolean selected = getResources().getConfiguration().getLocales().get(0).getLanguage().equals(language);
        button.setBackgroundResource(selected ? R.drawable.bg_primary : R.drawable.bg_button);
        button.setTextColor(getColor(selected ? R.color.accent_ink : R.color.ink));
        button.setSelected(selected);
        button.setOnClickListener(v -> {
            if (selected) return;
            getSharedPreferences(PREF, 0).edit().putString("ui_language", language).apply();
            if (AudioService.running) startService(new Intent(this, AudioService.class).setAction("refresh_ui"));
            recreate();
        });
    }

    private boolean toggle(int id) {
        View view = findViewById(id);
        boolean visible = view.getVisibility() != View.VISIBLE;
        view.setVisibility(visible ? View.VISIBLE : View.GONE);
        return visible;
    }

    private String normalizedInput() {
        try { return HaAddress.normalize(urlInput.getText().toString()); }
        catch (IllegalArgumentException e) { return ""; }
    }

    private void updateHttpConsent() {
        boolean http = HaAddress.isHttp(urlInput.getText().toString());
        findViewById(R.id.http_panel).setVisibility(http ? View.VISIBLE : View.GONE);
        if (!http || !normalizedInput().equals(consentForAddress)) allowHttp.setChecked(false);
    }

    private void startPlayer() {
        setupMessage.setText("");
        try {
            String base = HaAddress.validate(urlInput.getText().toString(), allowHttp.isChecked() && normalizedInput().equals(consentForAddress));
            String token = tokenInput.getText().toString().trim();
            var prefs = getSharedPreferences(PREF, 0);
            if (token.isEmpty() && !prefs.contains("secret")) throw new IllegalArgumentException("token_required");
            if (token.isEmpty() && !base.equals(HaAddress.normalize(prefs.getString("base", ""))))
                throw new IllegalArgumentException("token_server_changed");
            var edit = prefs.edit().putString("base", base);
            if (HaAddress.isHttp(base)) edit.putString(HTTP_CONSENT, base); else edit.remove(HTTP_CONSENT);
            if (!token.isEmpty()) edit.putString("secret", encrypt(token));
            edit.apply(); tokenInput.setText("");
            ((TextView) findViewById(R.id.token_note)).setText(R.string.token_saved);
            if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)
                requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
            stopService(new Intent(this, AudioService.class));
            startForegroundService(new Intent(this, AudioService.class));
        } catch (Exception e) { setupMessage.setText(AppLanguage.error(this, e)); }
    }

    private void searchHomeAssistant() {
        stopDiscovery(); resultCount = 0; searchResults.removeAllViews();
        searchMessage.setText(R.string.search_running); searchButton.setText(R.string.search_cancel);
        discovery = new HaDiscovery(this, new HaDiscovery.Listener() {
            public void onFound(HaDiscoveryEntry entry) {
                resultCount++;
                Button result = new Button(MainActivity.this, null, 0, R.style.Action);
                result.setText(entry.name + "\n" + entry.base + "\n" + (HaAddress.isHttp(entry.base) ? getString(R.string.http_required) : "HTTPS"));
                searchResults.addView(result);
                searchMessage.setText(R.string.search_found);
                result.setOnClickListener(v -> {
                    stopDiscovery(); urlInput.setText(entry.base);
                    searchMessage.setText("");
                    setupMessage.setText(HaAddress.isHttp(entry.base) ? R.string.address_selected_http : R.string.address_selected);
                });
            }
            public void onFinished(String error) {
                discovery = null; searchButton.setText(R.string.search);
                searchMessage.setText(error == null ? (resultCount > 0 ? R.string.search_finished : R.string.search_empty)
                        : error.equals("discovery_failed_start") ? R.string.discovery_failed_start : R.string.discovery_unavailable);
            }
        });
        discovery.start();
    }

    private void stopDiscovery() {
        if (discovery != null) { discovery.cancel(); discovery = null; }
        if (searchButton != null) searchButton.setText(R.string.search);
    }

    private void refreshStatus() {
        String raw = AudioService.ui;
        String stage = raw;
        if (raw.contains("|") && !raw.startsWith("ready|") && !raw.startsWith("no_bluetooth|") && !raw.startsWith("connection_error|"))
            stage = raw.split("\\|", 3)[1];
        int title = R.string.status_stopped, description = R.string.status_stopped_help;
        if (raw.startsWith("ready|")) { title = R.string.status_ready; description = R.string.status_ready_help; }
        else if (raw.startsWith("no_bluetooth|")) { title = R.string.status_no_bluetooth; description = R.string.status_no_bluetooth_help; }
        else if (stage.equals("connecting")) { title = R.string.status_connecting; description = R.string.status_connecting_help; }
        else if (stage.equals("buffering")) { title = R.string.status_buffering; description = R.string.status_buffering_help; }
        else if (stage.equals("playing")) { title = R.string.status_playing; description = R.string.status_playing_help; }
        else if (stage.equals("done")) { title = R.string.status_done; description = R.string.status_done_help; }
        else if (stage.equals("cancelled")) { title = R.string.status_cancelled; description = R.string.status_done_help; }
        else if (stage.contains("error")) {
            title = R.string.status_error;
            description = stage.contains("route") || stage.contains("bluetooth") ? R.string.status_route_help
                    : stage.contains("auth") || stage.contains("credentials") ? R.string.status_auth_help : R.string.status_network_help;
        }
        ((TextView) findViewById(R.id.player_status)).setText(title);
        ((TextView) findViewById(R.id.player_description)).setText(description);
        boolean bluetooth = false;
        AudioManager audio = getSystemService(AudioManager.class);
        if (audio != null) for (AudioDeviceInfo device : audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS))
            if (device.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP) bluetooth = true;
        TextView bt = findViewById(R.id.bluetooth_status);
        bt.setText(bluetooth ? R.string.connected : R.string.not_connected);
        bt.setTextColor(getColor(bluetooth ? R.color.accent : R.color.muted));
        TextView ha = findViewById(R.id.ha_status);
        ha.setText(AudioService.haConnected ? R.string.connected : AudioService.running ? R.string.not_connected : R.string.not_checked);
        ha.setTextColor(getColor(AudioService.haConnected ? R.color.accent : R.color.muted));
        ((TextView) findViewById(R.id.diagnostics_text)).setText(raw);
        String keepalive = AudioService.keepaliveStatus;
        int keepaliveText = keepalive.equals("active") ? R.string.keepalive_active : keepalive.equals("waiting")
                ? R.string.keepalive_waiting : keepalive.equals("starting") ? R.string.keepalive_starting
                : keepalive.equals("error") ? R.string.keepalive_error : R.string.keepalive_off;
        ((TextView) findViewById(R.id.keepalive_status)).setText(keepaliveText);
        findViewById(R.id.player_stop).setEnabled(AudioService.running);
    }

    private void scanToken() {
        setupMessage.setText("");
        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_CAMERA_ANY)) { setupMessage.setText(R.string.no_camera); return; }
        ScanOptions options = new ScanOptions().setCaptureActivity(TokenScanActivity.class).setDesiredBarcodeFormats(ScanOptions.QR_CODE)
                .setPrompt(getString(R.string.scan_prompt)).setBeepEnabled(false).setBarcodeImageEnabled(false).setOrientationLocked(false);
        options.addExtra(Intents.Scan.MISSING_CAMERA_PERMISSION_DIALOG_MESSAGE, getString(R.string.camera_permission));
        startActivityForResult(options.createScanIntent(this), SCAN_TOKEN);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != SCAN_TOKEN) return;
        if (resultCode != RESULT_OK || data == null) { setupMessage.setText(R.string.scan_cancelled); return; }
        try {
            tokenInput.setText(TokenQr.parse(data.getStringExtra(Intents.Scan.RESULT)));
            setupMessage.setText(R.string.scan_success);
        } catch (IllegalArgumentException e) { setupMessage.setText(R.string.invalid_qr_token); }
    }

    @Override protected void onStart() {
        super.onStart(); handler.post(refresh);
        if (!didAutoSearch && urlInput.getText().toString().trim().isEmpty()) { didAutoSearch = true; searchHomeAssistant(); }
    }

    @Override protected void onStop() {
        handler.removeCallbacks(refresh);
        if (discovery != null) { stopDiscovery(); searchMessage.setText(R.string.search_stopped); }
        super.onStop();
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        state.putString("setup_base", urlInput.getText().toString());
        state.putString(HTTP_CONSENT, allowHttp.isChecked() ? consentForAddress : "");
        state.putBoolean("did_auto_search", didAutoSearch);
        super.onSaveInstanceState(state);
    }

    // Preserve unsaved input across a language change only in memory, never in saved instance state.
    @Override public Object onRetainNonConfigurationInstance() { return tokenInput.getText().toString(); }
}
