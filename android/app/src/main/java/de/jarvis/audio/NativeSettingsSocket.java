package de.jarvis.audio;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.SystemClock;
import android.util.Log;
import java.util.concurrent.TimeUnit;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;
import org.json.JSONObject;

/**
 * Authenticated, per-tablet HA WebSocket control push.
 * A lost push falls back to REST without changing the Assist/audio sockets.
 */
final class NativeSettingsSocket extends WebSocketListener implements AutoCloseable {
    interface Listener {
        void onSettings(JSONObject settings);
        void onReady();
    }
    private static final String TAG="TAFA-SettingsWS";
    private static final int SUBSCRIBE_ID=1;
    private static final OkHttpClient CLIENT=new OkHttpClient.Builder()
        .connectTimeout(5,TimeUnit.SECONDS).readTimeout(0,TimeUnit.MILLISECONDS)
        .pingInterval(20,TimeUnit.SECONDS).build();
    private final Context context;
    private final Listener listener;
    private final String deviceId;
    private volatile WebSocket socket;
    private volatile String token;
    private volatile boolean subscribed=false;
    private boolean connecting=false,closed=false;
    private long retryAt=0;

    NativeSettingsSocket(Context context,Listener listener){
        this.context=context.getApplicationContext();
        this.listener=listener;
        deviceId=WakeDeviceIdentity.get(context);
    }
    boolean isSubscribed(){return subscribed;}
    synchronized void connectIfNeeded(){
        if(closed||subscribed||connecting||SystemClock.elapsedRealtime()<retryAt)return;
        retryAt=SystemClock.elapsedRealtime()+3000;
        connecting=true;
        try{
            SharedPreferences prefs=context.getSharedPreferences(MainActivity.PREF,0);
            String base=HaAddress.validateStored(prefs.getString("base",""),
                prefs.getString(MainActivity.HTTP_CONSENT,""));
            token=MainActivity.decrypt(prefs.getString("secret",""));
            if(token==null||token.isEmpty())throw new IllegalStateException("Missing HA credentials");
            String uri=(base.startsWith("https://")?"wss://":"ws://")+
                base.substring(base.indexOf("://")+3)+"/api/websocket";
            socket=CLIENT.newWebSocket(new Request.Builder().url(uri).build(),this);
        }catch(Exception problem){
            connecting=false;subscribed=false;
            Log.w(TAG,"Settings channel unavailable: "+problem.getClass().getSimpleName());
        }
    }
    @Override public void onMessage(WebSocket ws,String message){
        if(closed||ws!=socket)return;
        try{
            JSONObject packet=new JSONObject(message);
            String type=packet.optString("type","");
            if("auth_required".equals(type)){
                ws.send(new JSONObject().put("type","auth").put("access_token",token).toString());
            }else if("auth_ok".equals(type)){
                ws.send(new JSONObject().put("id",SUBSCRIBE_ID)
                    .put("type","tablet_assist_for_alexa/device_settings_subscribe")
                    .put("device_id",deviceId).toString());
            }else if("result".equals(type)&&packet.optInt("id",-1)==SUBSCRIBE_ID){
                if(!packet.optBoolean("success",false)){
                    ws.close(1000,"subscription_unavailable");return;
                }
                synchronized(this){if(!closed){subscribed=true;connecting=false;}}
                listener.onReady();
            }else if("event".equals(type)&&packet.optInt("id",-1)==SUBSCRIBE_ID){
                JSONObject event=packet.optJSONObject("event");
                if(event==null||!deviceId.equals(event.optString("device_id","")))return;
                if(!event.has("muted")||!event.has("voice_mode"))return;
                if(!"wake".equals(event.optString("voice_mode"))&&
                   !"continuous".equals(event.optString("voice_mode")))return;
                listener.onSettings(event);
            }else if("auth_invalid".equals(type)){
                ws.close(1000,"authentication_failed");
            }
        }catch(Exception ex){
            Log.w(TAG,"Invalid settings event: "+ex.getClass().getSimpleName());
        }
    }
    private synchronized void offline(WebSocket ws){
        // A late callback from an old socket may not clear a newer connection.
        if(socket!=ws)return;
        connecting=false;subscribed=false;socket=null;token=null;
    }
    @Override public void onFailure(WebSocket ws,Throwable failure,Response response){offline(ws);}
    @Override public void onClosed(WebSocket ws,int code,String reason){offline(ws);}
    @Override public synchronized void close(){
        closed=true;subscribed=false;connecting=false;
        WebSocket existing=socket;socket=null;token=null;
        if(existing!=null)existing.close(1000,"stopped");
    }
}
