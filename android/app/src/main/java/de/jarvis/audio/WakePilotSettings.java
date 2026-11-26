package de.jarvis.audio;

import android.content.Context;
import android.content.SharedPreferences;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.os.BatteryManager;
import android.provider.Settings;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Authenticated device settings, dynamically stored in the HA integration. */
final class WakePilotSettings {
    static final String ENDPOINT="/api/tablet_assist_for_alexa/wake_devices";
    static final String[] CHOICES={"hey_jarvis","jarvis","alexa","all"};
    static final String[] DISPLAY={"Hey Jarvis","Jarvis","Alexa","Alle drei"};
    private WakePilotSettings(){}

    static final class Snapshot {
        final boolean muted;
        final String word;
        final String room;
        final int strictness,cooldownSeconds,holdSeconds,followupLimit,pauseMs,micGain,brightness;
        final boolean screenAwake,displayControl;
        Snapshot(boolean muted,String word,String room,int strictness,int cooldownSeconds,int holdSeconds,int followupLimit,
                 int pauseMs,int micGain,int brightness,boolean screenAwake,boolean displayControl){
            this.muted=muted;this.word=word;this.room=room;
            this.strictness=strictness;
            this.cooldownSeconds=cooldownSeconds;this.holdSeconds=holdSeconds;
            this.followupLimit=followupLimit;
            this.pauseMs=pauseMs;this.micGain=micGain;this.brightness=brightness;
            this.screenAwake=screenAwake;this.displayControl=displayControl;
        }
    }

    static String choiceFor(String text){
        for(int i=0;i<DISPLAY.length;i++)if(DISPLAY[i].equals(text))return CHOICES[i];
        return "hey_jarvis";
    }
    static String displayFor(String key){
        for(int i=0;i<CHOICES.length;i++)if(CHOICES[i].equals(key))return DISPLAY[i];
        return DISPLAY[0];
    }
    static int clamp(int v,int lo,int hi){return Math.max(lo,Math.min(hi,v));}

    private static JSONObject request(Context ctx,JSONObject body) throws Exception {
        SharedPreferences prefs=ctx.getSharedPreferences(MainActivity.PREF,0);
        String base=HaAddress.validateStored(prefs.getString("base",""),
            prefs.getString(MainActivity.HTTP_CONSENT,""));
        String secret=prefs.getString("secret","");
        if(secret.isEmpty())throw new IllegalStateException("Home Assistant token not configured");
        String token=MainActivity.decrypt(secret);
        HttpURLConnection conn=null;
        try{
            conn=(HttpURLConnection)new URL(base+ENDPOINT).openConnection();
            conn.setInstanceFollowRedirects(false);
            conn.setConnectTimeout(2500);
            conn.setReadTimeout(3200);
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Authorization","Bearer "+token);
            conn.setRequestProperty("Content-Type","application/json");
            conn.setRequestProperty("Accept","application/json");
            conn.setDoOutput(true);
            byte[] data=body.toString().getBytes(StandardCharsets.UTF_8);
            conn.setFixedLengthStreamingMode(data.length);
            try(java.io.OutputStream out=conn.getOutputStream()){out.write(data);}
            int code=conn.getResponseCode();
            if(code<200||code>=300)throw new java.io.IOException("Wake devices HTTP "+code);
            try(java.io.InputStream stream=conn.getInputStream()){
                java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
                byte[] buf=new byte[4096];int n,total=0;
                while((n=stream.read(buf))!=-1){
                    total+=n;if(total>1024*1024)throw new java.io.IOException("Wake settings too large");
                    out.write(buf,0,n);
                }
                return new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));
            }
        }finally{if(conn!=null)conn.disconnect();}
    }

    private static JSONObject body(Context ctx,String action) throws Exception {
        return new JSONObject().put("action",action)
            .put("device_id",WakeDeviceIdentity.get(ctx));
    }

    static void register(Context ctx) throws Exception {
        request(ctx,body(ctx,"register").put("room",WakeDeviceIdentity.room(ctx)));
    }

    static Snapshot readFull(Context ctx) throws Exception {
        JSONObject dev=request(ctx,body(ctx,"get")).getJSONObject("device");
        Snapshot s=new Snapshot(
            dev.getBoolean("muted"),choiceFor(dev.getString("word")),
            dev.optString("room","Jarvis Tablet"),
            clamp(dev.getInt("strict"),1,3),
            clamp(dev.getInt("cooldown"),3,30),
            clamp(dev.getInt("hold"),10,90),
            clamp(dev.optInt("followup_limit",-1),-1,100),
            clamp(dev.optInt("pause_ms",1700),900,3200),
            clamp(dev.optInt("mic_gain",100),50,200),
            clamp(dev.optInt("brightness",80),1,100),
            dev.optBoolean("screen_awake",true),
            dev.optBoolean("display_control_enabled",false)
        );
        ctx.getSharedPreferences(MainActivity.PREF,0).edit()
            .putBoolean("wake_muted",s.muted).putString("wake_choice",s.word)
            .putInt("wake_strict",s.strictness).putInt("wake_cooldown",s.cooldownSeconds)
            .putInt("wake_hold",s.holdSeconds)
            .putInt("native_followup_limit",s.followupLimit)
            .putInt("native_pause_ms",s.pauseMs).putInt("mic_gain",s.micGain)
            .putInt("display_brightness",s.brightness)
            .putBoolean("screen_awake",s.screenAwake)
            .putBoolean("display_control_enabled",s.displayControl).apply();
        applyDisplay(ctx,s);
        return s;
    }

    // WRITE_SETTINGS is explicitly opted into; brightness does not power down
    // or wake the physical screen, which remains under Android's control.
    private static void applyDisplay(Context ctx,Snapshot s){
        if(!s.displayControl||!Settings.System.canWrite(ctx))return;
        try{
            int value=s.screenAwake?Math.max(1,Math.round(s.brightness*255f/100f)):1;
            Settings.System.putInt(ctx.getContentResolver(),Settings.System.SCREEN_BRIGHTNESS,value);
        }catch(SecurityException ignored){}
    }

    static void report(Context ctx,String wakeStatus,String microphone) throws Exception{
        JSONObject details=new JSONObject().put("wake_status",wakeStatus)
            .put("microphone",microphone).put("audio",AudioService.ui)
            .put("display",ctx.getSharedPreferences(MainActivity.PREF,0)
                .getBoolean("display_control_enabled",false)?"brightness_control":"android_managed");
        AudioManager am=(AudioManager)ctx.getSystemService(Context.AUDIO_SERVICE);
        boolean bluetooth=false;
        if(am!=null)for(AudioDeviceInfo device:am.getDevices(AudioManager.GET_DEVICES_OUTPUTS))
            if(device.getType()==AudioDeviceInfo.TYPE_BLUETOOTH_A2DP)bluetooth=true;
        details.put("bluetooth",bluetooth?"connected":"disconnected");
        BatteryManager battery=(BatteryManager)ctx.getSystemService(Context.BATTERY_SERVICE);
        if(battery!=null){
            int percent=battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
            if(percent>=0&&percent<=100)details.put("battery",percent);
        }
        try{details.put("app_version",ctx.getPackageManager()
            .getPackageInfo(ctx.getPackageName(),0).versionName);}catch(Exception ignored){}
        request(ctx,body(ctx,"report").put("telemetry",details));
    }

    static boolean readMute(Context ctx) throws Exception {
        return request(ctx,body(ctx,"get")).getJSONObject("device").getBoolean("muted");
    }

    /** User edits apply only to this installation. */
    static void write(Context ctx,String key,Object value) throws Exception {
        register(ctx);
        JSONObject setting=new JSONObject();
        if("muted".equals(key)&&value instanceof Boolean){
            setting.put("muted",value);
        }else if("word".equals(key)&&value instanceof String){
            setting.put("word",displayFor((String)value));
        }else if(("strict".equals(key)||"cooldown".equals(key)||"hold".equals(key)||
                  "pause_ms".equals(key)||"mic_gain".equals(key)||"brightness".equals(key))&&value instanceof Number){
            setting.put(key,((Number)value).intValue());
        }else if("room".equals(key)&&value instanceof String){
            setting.put("room",value);
        }else throw new IllegalArgumentException("Unknown Wake Pilot setting");
        request(ctx,body(ctx,"configure").put("settings",setting));
    }

    static boolean sendWake(Context ctx,String word) throws Exception {
        JSONObject response=request(ctx,body(ctx,"wake")
            .put("wakeword",word).put("timestamp_ms",System.currentTimeMillis()));
        return response.optBoolean("accepted",false);
    }
}
