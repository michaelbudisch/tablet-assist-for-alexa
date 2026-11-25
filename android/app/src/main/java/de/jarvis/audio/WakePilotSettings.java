package de.jarvis.audio;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** HA helpers are the shared settings for the Wake Pilot and the TAFA dashboard.
 * All HTTPS/explicitly-approved local-HTTP calls are authenticated. No audio data is exchanged.
 */
final class WakePilotSettings {
    static final String MUTE="input_boolean.jarvis_native_wake_stumm";
    static final String WORD="input_select.jarvis_native_wake_rufwort";
    static final String STRICT="input_number.jarvis_native_wake_erkennungsstrenge";
    static final String COOLDOWN="input_number.jarvis_native_wake_sperrzeit";
    static final String HOLD="input_number.jarvis_native_wake_aufnahmeubergabe";
    static final String[] CHOICES={"hey_jarvis","jarvis","alexa","all"};
    static final String[] DISPLAY={"Hey Jarvis","Jarvis","Alexa","Alle drei"};
    private WakePilotSettings(){}

    static final class Snapshot {
        final boolean muted;
        final String word;
        final int strictness,cooldownSeconds,holdSeconds;
        Snapshot(boolean muted,String word,int strictness,int cooldownSeconds,int holdSeconds){
            this.muted=muted;this.word=word;this.strictness=strictness;
            this.cooldownSeconds=cooldownSeconds;this.holdSeconds=holdSeconds;
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
    static int clamp(int value,int lo,int hi){return Math.max(lo,Math.min(hi,value));}

    private static String apiBase(Context ctx){
        SharedPreferences prefs=ctx.getSharedPreferences(MainActivity.PREF,0);
        return HaAddress.validateStored(prefs.getString("base",""),
            prefs.getString(MainActivity.HTTP_CONSENT,""));
    }
    private static String token(Context ctx) throws Exception {
        SharedPreferences prefs=ctx.getSharedPreferences(MainActivity.PREF,0);
        String secret=prefs.getString("secret","");
        if(secret.isEmpty())throw new IllegalStateException("Home Assistant token not configured");
        return MainActivity.decrypt(secret);
    }

    private static JSONObject request(Context ctx,String path,JSONObject body) throws Exception {
        HttpURLConnection conn=null;
        try{
            conn=(HttpURLConnection)new URL(apiBase(ctx)+path).openConnection();
            conn.setInstanceFollowRedirects(false);
            conn.setConnectTimeout(2000);
            conn.setReadTimeout(2500);
            conn.setRequestProperty("Authorization","Bearer "+token(ctx));
            conn.setRequestProperty("Accept","application/json");
            if(body!=null){
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type","application/json");
                conn.setDoOutput(true);
                byte[] data=body.toString().getBytes(StandardCharsets.UTF_8);
                conn.setFixedLengthStreamingMode(data.length);
                try(java.io.OutputStream out=conn.getOutputStream()){out.write(data);}
            }
            int code=conn.getResponseCode();
            if(code<200||code>=300)throw new java.io.IOException("HA HTTP "+code);
            if(body!=null)return new JSONObject();
            try(java.io.InputStream stream=conn.getInputStream()){
                return new JSONObject(new String(stream.readAllBytes(),StandardCharsets.UTF_8));
            }
        }finally{if(conn!=null)conn.disconnect();}
    }

    private static String state(Context ctx,String entityId) throws Exception {
        return request(ctx,"/api/states/"+entityId,null).getString("state");
    }

    static boolean readMute(Context ctx) throws Exception {
        return "on".equals(state(ctx,MUTE));
    }

    static Snapshot readFull(Context ctx) throws Exception {
        boolean muted=readMute(ctx);
        String word=choiceFor(state(ctx,WORD));
        int strict=clamp((int)Math.round(Double.parseDouble(state(ctx,STRICT))),1,3);
        int cooldown=clamp((int)Math.round(Double.parseDouble(state(ctx,COOLDOWN))),3,30);
        int hold=clamp((int)Math.round(Double.parseDouble(state(ctx,HOLD))),10,90);
        SharedPreferences prefs=ctx.getSharedPreferences(MainActivity.PREF,0);
        prefs.edit().putBoolean("wake_muted",muted).putString("wake_choice",word)
            .putInt("wake_strict",strict).putInt("wake_cooldown",cooldown)
            .putInt("wake_hold",hold).apply();
        return new Snapshot(muted,word,strict,cooldown,hold);
    }

    static void write(Context ctx,String key,Object value) throws Exception {
        final String domain,service,entity;
        JSONObject body=new JSONObject();
        if("muted".equals(key)){
            domain="input_boolean";service=Boolean.TRUE.equals(value)?"turn_on":"turn_off";entity=MUTE;
        }else if("word".equals(key)){
            domain="input_select";service="select_option";entity=WORD;
            body.put("option",displayFor((String)value));
        }else if("strict".equals(key)||"cooldown".equals(key)||"hold".equals(key)){
            domain="input_number";service="set_value";
            entity="strict".equals(key)?STRICT:"cooldown".equals(key)?COOLDOWN:HOLD;
            body.put("value",((Number)value).intValue());
        }else throw new IllegalArgumentException("Unknown Wake Pilot setting");
        body.put("entity_id",entity);
        request(ctx,"/api/services/"+domain+"/"+service,body);
    }
}
