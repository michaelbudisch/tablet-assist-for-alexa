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
    private CheckBox allowHttp, roomAudio;
    private String consentForAddress = "";
    private TextView setupMessage, searchMessage;
    private Button searchButton;
    private LinearLayout searchResults;
    private HaDiscovery discovery;
    private boolean didAutoSearch;
    private int resultCount;
    private String selectedSection = "connection";

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
        roomAudio = findViewById(R.id.room_audio_enabled);
        roomAudio.setChecked(prefs.getBoolean("room_audio_enabled",false));
        setupMessage = findViewById(R.id.setup_message);
        searchButton = findViewById(R.id.search);
        searchMessage = findViewById(R.id.search_message);
        searchResults = findViewById(R.id.search_results);
        urlInput.setText(state == null ? prefs.getString("base", "") : state.getString("setup_base", ""));
        Object pendingToken = getLastNonConfigurationInstance();
        if (pendingToken instanceof String) tokenInput.setText((String) pendingToken);
        ((TextView) findViewById(R.id.token_note)).setText(prefs.contains("secret") ? R.string.token_saved : R.string.token_storage);
        ((TextView) findViewById(R.id.footer)).setText(getString(R.string.footer, BuildConfig.VERSION_NAME));
        ((TextView) findViewById(R.id.app_version)).setText(getString(R.string.app_version,BuildConfig.VERSION_NAME,BuildConfig.VERSION_CODE));

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
        findViewById(R.id.camera_open).setOnClickListener(v -> startActivity(new Intent(this, CameraActivity.class)));
        findViewById(R.id.camera_main_stop).setOnClickListener(v -> stopService(new Intent(this, CameraRelayService.class)));
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
                    stopService(new Intent(this, WakeWordService.class));
                    stopService(new Intent(this, CameraRelayService.class));
                    stopDiscovery();
                    prefs.edit().remove("base").remove("secret").remove(HTTP_CONSENT).remove("room_audio_enabled").remove("wake_choice").apply();
                    roomAudio.setChecked(false);
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
        initializeNativeWake();
        initializeNativeAssistControls();
        languageButton(R.id.language_de, "de");
        languageButton(R.id.language_en, "en");
        didAutoSearch = state != null && state.getBoolean("did_auto_search", false);
        initializeNavigation(state);
    }


    private void initializeNavigation(Bundle state) {
        String initial = getSharedPreferences(PREF, 0).contains("secret") ? "status" : "connection";
        for (String section : new String[]{"status", "connection", "voice", "help"}) {
            int id = section.equals("status") ? R.id.nav_status : section.equals("connection")
                    ? R.id.nav_connection : section.equals("voice") ? R.id.nav_voice : R.id.nav_help;
            findViewById(id).setOnClickListener(v -> showSection(section, true));
        }
        findViewById(R.id.edit_connection).setOnClickListener(v -> showSection("connection", true));
        findViewById(R.id.open_voice).setOnClickListener(v -> showSection("voice", true));
        findViewById(R.id.connection_start).setOnClickListener(v -> {
            startPlayer();
            showSection("status", true);
        });
        bindDisclosure(R.id.bluetooth_advanced_toggle, R.id.bluetooth_advanced,
                R.string.bluetooth_advanced_title, R.string.bluetooth_advanced_collapse,
                state != null && state.getBoolean("bluetooth_advanced_open", false));
        bindDisclosure(R.id.wake_advanced_toggle, R.id.wake_advanced,
                R.string.wake_advanced_title, R.string.wake_advanced_collapse,
                state != null && state.getBoolean("wake_advanced_open", false));
        if (state != null) {
            findViewById(R.id.diagnostics_text).setVisibility(
                    state.getBoolean("diagnostics_open", false) ? View.VISIBLE : View.GONE);
            boolean helpOpen = state.getBoolean("help_open", false);
            findViewById(R.id.help_details).setVisibility(helpOpen ? View.VISIBLE : View.GONE);
            ((Button)findViewById(R.id.help_toggle)).setText(helpOpen ? R.string.help_collapse : R.string.help_expand);
        }
        showSection(state == null ? initial : state.getString("visible_section", initial), false);
    }

    private void bindDisclosure(int buttonId, int panelId, int closedText, int openText, boolean open) {
        Button button = findViewById(buttonId);
        findViewById(panelId).setVisibility(open ? View.VISIBLE : View.GONE);
        button.setText(open ? openText : closedText);
        button.setOnClickListener(v -> {
            boolean expanded = toggle(panelId);
            button.setText(expanded ? openText : closedText);
        });
    }

    private void showSection(String section, boolean scrollToTop) {
        if (!section.equals("status") && !section.equals("connection")
                && !section.equals("voice") && !section.equals("help")) section = "status";
        selectedSection = section;
        int[] panels = {R.id.section_status, R.id.section_connection, R.id.section_voice, R.id.section_help};
        int[] tabs = {R.id.nav_status, R.id.nav_connection, R.id.nav_voice, R.id.nav_help};
        int[] titles = {R.string.section_status_title, R.string.section_connection_title,
                R.string.section_voice_title, R.string.section_help_title};
        int[] descriptions = {R.string.section_status_description, R.string.section_connection_description,
                R.string.section_voice_description, R.string.section_help_description};
        String[] keys = {"status", "connection", "voice", "help"};
        for (int i = 0; i < keys.length; i++) {
            boolean active = keys[i].equals(section);
            findViewById(panels[i]).setVisibility(active ? View.VISIBLE : View.GONE);
            findViewById(tabs[i]).setSelected(active);
            if (active) {
                ((TextView)findViewById(R.id.section_heading)).setText(titles[i]);
                ((TextView)findViewById(R.id.section_description)).setText(descriptions[i]);
            }
        }
        if (scrollToTop) {
            View focused = getCurrentFocus();
            if (focused != null) {
                android.view.inputmethod.InputMethodManager keyboard =
                        getSystemService(android.view.inputmethod.InputMethodManager.class);
                if (keyboard != null) keyboard.hideSoftInputFromWindow(focused.getWindowToken(), 0);
                focused.clearFocus();
            }
            findViewById(R.id.page_content).requestFocus();
            findViewById(R.id.main_scroll).post(() -> ((ScrollView)findViewById(R.id.main_scroll)).scrollTo(0, 0));
        }
    }

    private void refreshBridgeOverview() {
        String state = WakeWordService.status;
        int label = R.string.wake_stopped;
        int color = R.color.muted;
        if (state.contains("error")) { label = R.string.wake_error_state; color = R.color.warn; }
        else if (WakeWordService.running) {
            color = R.color.secondary;
            if (state.equals("loading")) label = R.string.wake_loading_state;
            else if (state.equals("muted")) label = R.string.wake_muted_state;
            else if (state.startsWith("listening:")) label = R.string.wake_listening;
            else label = R.string.wake_handoff_state;
        }
        for (int id : new int[]{R.id.overview_wake_status, R.id.wake_runtime_status}) {
            TextView view = findViewById(id);
            view.setText(label);
            view.setTextColor(getColor(color));
        }
        if (!wakeDownloading) {
            ((TextView)findViewById(R.id.wake_model_status)).setText(
                    WakeModelInstaller.installed(this) ? R.string.wake_ready : R.string.wake_model_missing);
        }
        wakeInstall.setEnabled(!wakeDownloading && !WakeWordService.running);
        findViewById(R.id.wake_start).setEnabled(!WakeWordService.running && !wakeDownloading);
        findViewById(R.id.wake_stop).setEnabled(WakeWordService.running);
        findViewById(R.id.wake_mute_toggle).setEnabled(WakeWordService.running);
        refreshNativeAssistStatus();
    }

    private static final int WAKE_MICROPHONE_PERMISSION = 120;
    private static final String[] WAKE_KEYS={"hey_jarvis","jarvis","alexa","all"};
    private Spinner wakeChoice;
    private EditText wakeRoomName;
    private Button wakeInstall;
    private TextView wakeStatus;
    private boolean wakeDownloading=false;
    private SeekBar wakeStrictSlider,wakeCooldownSlider,wakeHoldSlider;
    private Button wakeMuteButton;
    private boolean wakeSliderBeingDragged=false;

    private void configureWakeSlider(SeekBar slider,String pref,int min,int step,int label){
        final android.content.SharedPreferences prefs=getSharedPreferences(PREF,0);
        int def=pref.equals("wake_strict")?1:pref.equals("wake_cooldown")?12:50;
        slider.setProgress((prefs.getInt(pref,def)-min)/step);
        slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar bar,int progress,boolean fromUser){
                updateWakeSliderLabel(label,min+progress*step);
            }
            public void onStartTrackingTouch(SeekBar bar){wakeSliderBeingDragged=true;}
            public void onStopTrackingTouch(SeekBar bar){
                wakeSliderBeingDragged=false;
                int value=min+bar.getProgress()*step;
                prefs.edit().putInt(pref,value).apply();
                remoteWakeSetting(pref.equals("wake_strict")?"strict":
                    pref.equals("wake_cooldown")?"cooldown":"hold",value);
            }
        });
        updateWakeSliderLabel(label,min+slider.getProgress()*step);
    }

    private void updateWakeSliderLabel(int label,int value){
        TextView target=findViewById(label);
        if(label==R.id.wake_strict_label)
            target.setText(getString(R.string.wake_strict_label).replace("1 of 3",value+" of 3").replace("1 von 3",value+" von 3"));
        else if(label==R.id.wake_cooldown_label)
            target.setText(getString(R.string.wake_cooldown_label).replace("12",Integer.toString(value)));
        else target.setText(getString(R.string.wake_hold_label).replace("50",Integer.toString(value)));
    }

    private void remoteWakeSetting(String setting,Object value){
        new Thread(()->{
            try{
                WakePilotSettings.write(this,setting,value);
            }catch(Exception e){
                android.util.Log.w("JarvisWake","Unable to save HA wakeword setting",e);
                runOnUiThread(()->wakeStatus.setText(getString(R.string.wake_save_error,
                    e.getClass().getSimpleName())));
            }
        },"JarvisWakeSettingsUpdate").start();
    }

    private void refreshWakeConfigUi(){
        if(wakeChoice==null||wakeSliderBeingDragged)return;
        var prefs=getSharedPreferences(PREF,0);
        String choice=prefs.getString("wake_choice","hey_jarvis");
        for(int i=0;i<WAKE_KEYS.length;i++){
            if(WAKE_KEYS[i].equals(choice)&&wakeChoice.getSelectedItemPosition()!=i){
                wakeChoice.setSelection(i);
                break;
            }
        }
        int strict=prefs.getInt("wake_strict",1),cooldown=prefs.getInt("wake_cooldown",12),hold=prefs.getInt("wake_hold",50);
        if(wakeStrictSlider.getProgress()!=strict-1)wakeStrictSlider.setProgress(strict-1);
        if(wakeCooldownSlider.getProgress()!=cooldown-3)wakeCooldownSlider.setProgress(cooldown-3);
        if(wakeHoldSlider.getProgress()!=(hold-10)/5)wakeHoldSlider.setProgress((hold-10)/5);
        wakeMuteButton.setText(prefs.getBoolean("wake_muted",true)?
            R.string.wake_unmute_button:R.string.wake_mute_button);
    }



    private void initializeNativeWake(){
        var preferences=getSharedPreferences(PREF,0);
        wakeRoomName=findViewById(R.id.wake_room_name);
        wakeRoomName.setText(preferences.getString("wake_room_name",""));
        wakeRoomName.setOnFocusChangeListener((v,focus)->{
            if(!focus&&WakeWordService.running){
                remoteWakeSetting("room",wakeRoomName.getText().toString().trim());
            }
        });
        wakeRoomName.addTextChangedListener(new TextWatcher(){
            @Override public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            @Override public void onTextChanged(CharSequence s,int start,int before,int count){}
            @Override public void afterTextChanged(Editable e){
                preferences.edit().putString("wake_room_name",e.toString().trim()).apply();
            }
        });
        ((TextView)findViewById(R.id.wake_device_id)).setText(
            getString(R.string.wake_device_id,WakeDeviceIdentity.get(this).substring(0,12)));
        wakeChoice=findViewById(R.id.wake_choice);
        wakeInstall=findViewById(R.id.wake_model_install);
        wakeStatus=findViewById(R.id.wake_status);
        ArrayAdapter<CharSequence> adapter=ArrayAdapter.createFromResource(this,R.array.wake_choices,
                R.layout.spinner_selected);
        adapter.setDropDownViewResource(R.layout.spinner_dropdown);
        wakeChoice.setAdapter(adapter);
        String saved=preferences.getString("wake_choice","hey_jarvis");
        for(int i=0;i<WAKE_KEYS.length;i++)if(WAKE_KEYS[i].equals(saved))wakeChoice.setSelection(i);
        wakeChoice.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,View view,int index,long id){
                if(index>=0&&index<WAKE_KEYS.length){
                    String newChoice=WAKE_KEYS[index];
                    if(!newChoice.equals(preferences.getString("wake_choice","hey_jarvis"))){
                        preferences.edit().putString("wake_choice",newChoice).apply();
                        remoteWakeSetting("word",newChoice);
                    }
                }
            }
        });
        wakeInstall.setOnClickListener(v->{
            if(wakeDownloading||WakeWordService.running)return;
            wakeDownloading=true;wakeInstall.setEnabled(false);
            wakeStatus.setText(R.string.wake_model_missing);
            new Thread(()->{
                try{
                    WakeModelInstaller.install(this,progress->runOnUiThread(()->{
                        wakeStatus.setText(progress);
                        ((TextView)findViewById(R.id.wake_model_status)).setText(progress);
                    }));
                    runOnUiThread(()->wakeStatus.setText(R.string.wake_ready));
                }catch(Exception e){
                    runOnUiThread(()->wakeStatus.setText(getString(R.string.wake_download_failed,
                        e.getMessage()==null?e.getClass().getSimpleName():e.getMessage())));
                }finally{
                    runOnUiThread(()->{wakeDownloading=false;wakeInstall.setEnabled(true);});
                }
            },"JarvisWakeModelDownload").start();
        });
        wakeStrictSlider=findViewById(R.id.wake_strict_slider);
        wakeCooldownSlider=findViewById(R.id.wake_cooldown_slider);
        wakeHoldSlider=findViewById(R.id.wake_hold_slider);
        configureWakeSlider(wakeStrictSlider,"wake_strict",1,1,R.id.wake_strict_label);
        configureWakeSlider(wakeCooldownSlider,"wake_cooldown",3,1,R.id.wake_cooldown_label);
        configureWakeSlider(wakeHoldSlider,"wake_hold",10,5,R.id.wake_hold_label);
        wakeMuteButton=findViewById(R.id.wake_mute_toggle);
        wakeMuteButton.setOnClickListener(v->{
            boolean newMuted=!preferences.getBoolean("wake_muted",true);
            preferences.edit().putBoolean("wake_muted",newMuted).apply();
            remoteWakeSetting("muted",newMuted);
            refreshWakeConfigUi();
        });
        refreshWakeConfigUi();
        findViewById(R.id.wake_start).setOnClickListener(v->startNativeWake());
        findViewById(R.id.wake_stop).setOnClickListener(v->{
            stopService(new Intent(this,WakeWordService.class));
            wakeStatus.setText("");
        });
    }

    private void initializeNativeAssistControls(){
        var preferences=getSharedPreferences(PREF,0);
        CheckBox enabled=findViewById(R.id.native_assist_enabled);
        CheckBox followups=findViewById(R.id.native_followup_enabled);
        SeekBar pause=findViewById(R.id.native_pause_slider);
        TextView pauseLabel=findViewById(R.id.native_pause_label);
        Button test=findViewById(R.id.native_assist_test);
        enabled.setChecked(preferences.getBoolean("native_assist_enabled",false));
        followups.setChecked(preferences.getBoolean("native_followup_enabled",false));
        followups.setEnabled(enabled.isChecked());
        int value=Math.max(900,Math.min(3200,preferences.getInt("native_pause_ms",1700)));
        pause.setProgress((value-900)/100);
        pauseLabel.setText(getString(R.string.native_pause_label,value));
        enabled.setOnCheckedChangeListener((button,isChecked)->{
            if(isChecked&&!roomAudio.isChecked()){
                button.setChecked(false);
                Toast.makeText(this,R.string.native_assist_requirements,Toast.LENGTH_LONG).show();
                return;
            }
            preferences.edit().putBoolean("native_assist_enabled",isChecked).apply();
            followups.setEnabled(isChecked);
            if(WakeWordService.running)startService(
                new Intent(this,WakeWordService.class).setAction(WakeWordService.NATIVE_SETTINGS));
            refreshNativeAssistStatus();
        });
        followups.setOnCheckedChangeListener((button,isChecked)->
            preferences.edit().putBoolean("native_followup_enabled",isChecked).apply());
        pause.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            @Override public void onProgressChanged(SeekBar bar,int progress,boolean fromUser){
                int ms=900+100*progress;
                pauseLabel.setText(getString(R.string.native_pause_label,ms));
                if(fromUser)preferences.edit().putInt("native_pause_ms",ms).apply();
            }
            @Override public void onStartTrackingTouch(SeekBar bar){}
            @Override public void onStopTrackingTouch(SeekBar bar){}
        });
        test.setOnClickListener(v->{
            if(!WakeWordService.running||
                    !preferences.getBoolean("native_assist_enabled",false)||
                    !AudioService.running){
                Toast.makeText(this,R.string.native_assist_requirements,Toast.LENGTH_LONG).show();
                return;
            }
            startService(new Intent(this,WakeWordService.class).setAction(WakeWordService.NATIVE_TEST));
        });
        refreshNativeAssistStatus();
    }

    private void refreshNativeAssistStatus(){
        TextView current=findViewById(R.id.native_assist_status);
        if(current==null)return;
        String stage=WakeWordService.status;
        if(!getSharedPreferences(PREF,0).getBoolean("native_assist_enabled",false)){
            current.setText(R.string.native_assist_inactive);
        }else if(stage.startsWith("native_error:")){
            current.setText(getString(R.string.native_state_error)+": "+stage.substring(13));
        }else if(stage.startsWith("native_")){
            int label;
            switch(stage){
                case "native_connecting": case "native_connected":
                    label=R.string.native_state_connecting;break;
                case "native_followup":label=R.string.native_state_followup;break;
                case "native_authenticating":label=R.string.native_state_authenticating;break;
                case "native_waiting_for_stt":case "native_starting_microphone":
                    label=R.string.native_state_waiting;break;
                case "native_listening":label=R.string.native_state_listening;break;
                case "native_transcribing":label=R.string.native_state_transcribing;break;
                case "native_thinking":case "native_processing":
                    label=R.string.native_state_thinking;break;
                case "native_generating_voice":label=R.string.native_state_voice;break;
                case "native_sending_audio":case "native_waiting_for_playback":
                    label=R.string.native_state_playback;break;
                case "native_buffering":label=R.string.native_state_buffering;break;
                case "native_playing":label=R.string.native_state_playing;break;
                case "native_answer_completed":label=R.string.native_state_done;break;
                case "native_no_speech":case "native_no_reply":
                    label=R.string.native_state_no_reply;break;
                default:label=R.string.native_state_waiting;break;
            }
            current.setText(label);
        }else current.setText(stage.startsWith("listening:")?
            getString(R.string.native_state_ready):stage);
        Button test=findViewById(R.id.native_assist_test);
        if(test!=null)test.setEnabled(WakeWordService.running&&AudioService.running
            &&getSharedPreferences(PREF,0).getBoolean("native_assist_enabled",false));
    }

    private boolean saveConnectionForWake(){
        try{
            String base=HaAddress.validate(urlInput.getText().toString(),
                allowHttp.isChecked()&&normalizedInput().equals(consentForAddress));
            var prefs=getSharedPreferences(PREF,0);
            String token=tokenInput.getText().toString().trim();
            if(token.isEmpty()&&!prefs.contains("secret"))
                throw new IllegalArgumentException("token_required");
            if(token.isEmpty()&&!base.equals(HaAddress.normalize(prefs.getString("base",""))))
                throw new IllegalArgumentException("token_server_changed");
            var editor=prefs.edit().putString("base",base);
            if(HaAddress.isHttp(base))editor.putString(HTTP_CONSENT,base);
            else editor.remove(HTTP_CONSENT);
            if(!token.isEmpty())editor.putString("secret",encrypt(token));
            editor.apply();
            tokenInput.setText("");
            ((TextView)findViewById(R.id.token_note)).setText(R.string.token_saved);
            // Saving the wakeword connection does not opt into audio playback.
            return true;
        }catch(Exception error){
            wakeStatus.setText(AppLanguage.error(this,error));
            return false;
        }
    }

    private void startNativeWake(){
        if(!WakeModelInstaller.installed(this)){
            wakeStatus.setText(R.string.wake_model_missing);return;
        }
        if(!saveConnectionForWake())return;
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
            wakeStatus.setText(R.string.wake_permission);
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},WAKE_MICROPHONE_PERMISSION);
            return;
        }
        try{
            stopService(new Intent(this,WakeWordService.class));
            startForegroundService(new Intent(this,WakeWordService.class).setAction(WakeWordService.START));
            wakeStatus.setText("");
        }catch(Exception error){
            wakeStatus.setText(getString(R.string.wake_download_failed,
                error.getMessage()==null?error.getClass().getSimpleName():error.getMessage()));
        }
    }

    @Override public void onRequestPermissionsResult(int requestCode,String[] permissions,int[] grants){
        super.onRequestPermissionsResult(requestCode,permissions,grants);
        if(requestCode!=WAKE_MICROPHONE_PERMISSION)return;
        if(grants.length>0&&grants[0]==PackageManager.PERMISSION_GRANTED)startNativeWake();
        else wakeStatus.setText(R.string.wake_permission);
    }

    private void configureColumns() {
        int width = getResources().getConfiguration().screenWidthDp;
        int tabColumns = getResources().getConfiguration().fontScale >= 1.3f || width < 360 ? 2 : 4;
        GridLayout navigation = findViewById(R.id.section_tabs);
        navigation.setColumnCount(tabColumns);
        int[] tabIds = {R.id.nav_status, R.id.nav_connection, R.id.nav_voice, R.id.nav_help};
        for (int i = 0; i < tabIds.length; i++) {
            GridLayout.LayoutParams tab = new GridLayout.LayoutParams(
                    GridLayout.spec(i / tabColumns), GridLayout.spec(i % tabColumns, 1f));
            tab.width = 0;
            tab.height = dp(tabColumns == 2 ? 56 : 48);
            tab.setMargins(dp(2), dp(2), dp(2), dp(2));
            findViewById(tabIds[i]).setLayoutParams(tab);
        }
        if (width < 380 || getResources().getConfiguration().fontScale >= 1.3f) {
            ((LinearLayout)findViewById(R.id.brand_header)).setOrientation(LinearLayout.VERTICAL);
            findViewById(R.id.brand_logo).setLayoutParams(new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, dp(80)));
            LinearLayout tools = findViewById(R.id.brand_tools);
            tools.setLayoutParams(new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
            tools.setOrientation(LinearLayout.HORIZONTAL);
            tools.setGravity(Gravity.CENTER_VERTICAL);
            findViewById(R.id.app_version).setLayoutParams(new LinearLayout.LayoutParams(
                    0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        }
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
            if (CameraRelayService.running) startService(new Intent(this, CameraRelayService.class).setAction("refresh_ui"));
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
            var edit = prefs.edit().putString("base", base).putBoolean("room_audio_enabled",roomAudio.isChecked());
            if(CameraRelayService.running&&(!base.equals(prefs.getString("base",""))||!token.isEmpty()))
                stopService(new Intent(this,CameraRelayService.class));
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
        refreshWakeConfigUi();
        refreshBridgeOverview();
        ((TextView)findViewById(R.id.camera_main_status)).setText(CameraActivity.relayMessage(this));
        findViewById(R.id.camera_main_stop).setVisibility(CameraRelayService.running?View.VISIBLE:View.GONE);
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
        ((TextView) findViewById(R.id.diagnostics_text)).setText(raw + "\n" + AudioService.streamDiagnostics);
        String keepalive = AudioService.keepaliveStatus;
        int keepaliveText = keepalive.equals("active") ? R.string.keepalive_active : keepalive.equals("waiting")
                ? R.string.keepalive_waiting : keepalive.equals("starting") ? R.string.keepalive_starting
                : keepalive.equals("error") ? R.string.keepalive_error : R.string.keepalive_off;
        ((TextView) findViewById(R.id.keepalive_status)).setText(keepaliveText);
        findViewById(R.id.player_stop).setEnabled(AudioService.running);
        if(wakeStatus!=null&&!wakeDownloading){
            wakeStatus.setText(WakeWordService.running?WakeWordService.status:
                (WakeModelInstaller.installed(this)?getString(R.string.wake_ready)+" · "+getString(R.string.wake_stopped):
                    getString(R.string.wake_model_missing)));
            findViewById(R.id.wake_start).setEnabled(!WakeWordService.running&&WakeModelInstaller.installed(this));
            findViewById(R.id.wake_stop).setEnabled(WakeWordService.running);
            wakeChoice.setEnabled(true);
            wakeInstall.setEnabled(!WakeWordService.running);
        }
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
        showSection("connection", true);
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
        state.putString("visible_section", selectedSection);
        state.putBoolean("wake_advanced_open", findViewById(R.id.wake_advanced).getVisibility() == View.VISIBLE);
        state.putBoolean("bluetooth_advanced_open", findViewById(R.id.bluetooth_advanced).getVisibility() == View.VISIBLE);
        state.putBoolean("help_open", findViewById(R.id.help_details).getVisibility() == View.VISIBLE);
        state.putBoolean("diagnostics_open", findViewById(R.id.diagnostics_text).getVisibility() == View.VISIBLE);
        super.onSaveInstanceState(state);
    }

    // Preserve unsaved input across a language change only in memory, never in saved instance state.
    @Override public Object onRetainNonConfigurationInstance() { return tokenInput.getText().toString(); }
}
