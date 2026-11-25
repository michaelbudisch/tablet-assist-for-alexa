package de.jarvis.audio;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Authenticated per-tablet HA helpers. 4 explicit slots, bound to one installation each.
 * A different device cannot reuse a claimed slot until its helper is cleared in HA.
 * Audio is never transferred; only control values and event metadata are exchanged.
 */
final class WakePilotSettings {
    static final String[] CHOICES={"hey_jarvis","jarvis","alexa","all"};
    static final String[] DISPLAY={"Hey Jarvis","Jarvis","Alexa","Alle drei"};
    private WakePilotSettings(){}

    static String entity(String key,int slot){
        if(slot<1||slot>4)throw new IllegalArgumentException("Invalid tablet slot");
        String prefix="jarvis_wake_tablet_"+slot+"_";
        switch(key){
            case "muted":return "input_boolean."+prefix+"stumm";
            case "word":return "input_select."+prefix+"rufwort";
            case "strict":return "input_number."+prefix+"strenge";
            case "cooldown":return "input_number."+prefix+"sperrzeit";
            case "hold":return "input_number."+prefix+"ubergabe";
            case "owner":return "input_text."+prefix+"geratekennung";
            default:throw new IllegalArgumentException("Unknown Wake Pilot setting");
        }
    }

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
            conn.setConnectTimeout(2200);
            conn.setReadTimeout(2800);
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
                java.io.ByteArrayOutputStream buffer=new java.io.ByteArrayOutputStream();
                byte[] chunk=new byte[4096];int n,total=0;
                while((n=stream.read(chunk))!=-1){
                    total+=n;if(total>1024*1024)throw new java.io.IOException("HA settings too large");
                    buffer.write(chunk,0,n);
                }
                return new JSONObject(new String(buffer.toByteArray(),StandardCharsets.UTF_8));
            }
        }finally{if(conn!=null)conn.disconnect();}
    }

    static String state(Context ctx,String entityId) throws Exception {
        return request(ctx,"/api/states/"+entityId,null).getString("state");
    }

    /** Claim the selected slot, or reject it if another installation owns it. */
    static void ensureOwner(Context ctx) throws Exception {
        int slot=WakeDeviceIdentity.slot(ctx);
        String ownerEntity=entity("owner",slot);
        String device=WakeDeviceIdentity.get(ctx);
        String current=state(ctx,ownerEntity);
        if("unavailable".equals(current)||"unknown".equals(current))
            throw new IllegalStateException("Tablet slot helper unavailable");
        if(current.isEmpty()){
            JSONObject data=new JSONObject().put("entity_id",ownerEntity).put("value",device);
            request(ctx,"/api/services/input_text/set_value",data);
            current=state(ctx,ownerEntity);
        }
        if(!device.equals(current))
            throw new IllegalStateException("Tablet "+slot+" already assigned to another Wake Pilot");
    }

    static boolean readMute(Context ctx) throws Exception {
        ensureOwner(ctx);
        String state=state(ctx,entity("muted",WakeDeviceIdentity.slot(ctx)));
        if(!"on".equals(state)&&!"off".equals(state))
            throw new IllegalStateException("Wake Pilot mute state unavailable");
        return "on".equals(state);
    }

    static Snapshot readFull(Context ctx) throws Exception {
        ensureOwner(ctx);
        int slot=WakeDeviceIdentity.slot(ctx);
        boolean muted=readMute(ctx);
        String word=choiceFor(state(ctx,entity("word",slot)));
        int strict=clamp((int)Math.round(Double.parseDouble(state(ctx,entity("strict",slot)))),1,3);
        int cooldown=clamp((int)Math.round(Double.parseDouble(state(ctx,entity("cooldown",slot)))),3,30);
        int hold=clamp((int)Math.round(Double.parseDouble(state(ctx,entity("hold",slot)))),10,90);
        SharedPreferences prefs=ctx.getSharedPreferences(MainActivity.PREF,0);
        prefs.edit().putBoolean("wake_muted",muted).putString("wake_choice",word)
            .putInt("wake_strict",strict).putInt("wake_cooldown",cooldown)
            .putInt("wake_hold",hold).apply();
        return new Snapshot(muted,word,strict,cooldown,hold);
    }

    static void write(Context ctx,String key,Object value) throws Exception {
        ensureOwner(ctx);
        String domain,service;
        JSONObject data=new JSONObject();
        if("muted".equals(key)){
            domain="input_boolean";service=Boolean.TRUE.equals(value)?"turn_on":"turn_off";
        }else if("word".equals(key)){
            domain="input_select";service="select_option";
            data.put("option",displayFor((String)value));
        }else if("strict".equals(key)||"cooldown".equals(key)||"hold".equals(key)){
            domain="input_number";service="set_value";
            data.put("value",((Number)value).intValue());
        }else throw new IllegalArgumentException("Unknown Wake Pilot setting");
        data.put("entity_id",entity(key,WakeDeviceIdentity.slot(ctx)));
        request(ctx,"/api/services/"+domain+"/"+service,data);
    }
}
