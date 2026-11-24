package de.jarvis.audio;

import android.app.*;
import android.content.*;
import android.media.*;
import android.os.*;
import org.json.JSONObject;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import java.util.regex.Pattern;

public class AudioService extends Service {
    static volatile String ui="stopped", keepaliveStatus="off", streamDiagnostics="";
    static volatile boolean running=false, haConnected=false;
    private BluetoothKeepalive keepalive;
    static final String COMMAND="input_text.jarvis_native_audio_command", STATUS="input_text.jarvis_native_audio_status";
    static final Pattern PATH=Pattern.compile("/api/tts_proxy/[A-Za-z0-9_.~-]{1,200}");
    final Handler main=new Handler(Looper.getMainLooper());
    final ScheduledExecutorService io=Executors.newSingleThreadScheduledExecutor();
    private StreamingSession streaming;
    private Runnable streamWatchdog;
    volatile boolean active=false,busy=false; volatile String id="", cachedStatus="";
    String base,token,httpConsent,lastCommand=""; boolean baseline=false; long heartbeat=0;
    private boolean roomMode=false;
    private String roomSession="";
    private long roomRetryAt=0;
    MediaPlayer player; File file; AudioManager am; AudioFocusRequest focus; boolean audible=false,seeked=false,preferredAccepted=false; int preferredId=-1,routeAttempts=0; long checkUntil=0,playUntil=0,routeRetryAt=0;
    @Override public IBinder onBind(Intent i){return null;}
    @Override public void onCreate() {
        super.onCreate();
        File[] stale=getCacheDir().listFiles((dir,name)->name.startsWith("jarvis-")&&name.endsWith(".audio"));
        if(stale!=null)for(File f:stale)f.delete();
        am=(AudioManager)getSystemService(AUDIO_SERVICE);
        keepalive=new BluetoothKeepalive(this, status -> keepaliveStatus=status);
        running=true;
        updateNotification();
    }

    private void updateNotification() {
        Context localized=AppLanguage.wrap(this);
        NotificationManager notifications=getSystemService(NotificationManager.class);
        notifications.createNotificationChannel(new NotificationChannel("player",localized.getString(R.string.notification_channel),NotificationManager.IMPORTANCE_LOW));
        PendingIntent open=PendingIntent.getActivity(this,1,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE);
        PendingIntent stop=PendingIntent.getService(this,2,new Intent(this,AudioService.class).setAction("stop"),PendingIntent.FLAG_IMMUTABLE);
        startForeground(42,new Notification.Builder(this,"player").setContentTitle(localized.getString(R.string.app_name))
                .setContentText(localized.getString(R.string.notification_text)).setSmallIcon(R.drawable.ic_notification)
                .setContentIntent(open).addAction(new Notification.Action.Builder(null,localized.getString(R.string.notification_stop),stop).build())
                .setOngoing(true).build());
    }

    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        String action=intent==null?"":intent.getAction();
        if("stop".equals(action)){stopSelf();return START_NOT_STICKY;}
        if("refresh_ui".equals(action)){updateNotification();return START_NOT_STICKY;}
        if(active){
            if("update_keepalive".equals(action))keepalive.setEnabled(getSharedPreferences(MainActivity.PREF,0).getBoolean("keepalive_enabled",false));
            return START_NOT_STICKY;
        }
        try{
            var prefs=getSharedPreferences(MainActivity.PREF,0);
            httpConsent=prefs.getString(MainActivity.HTTP_CONSENT,"");
            base=HaAddress.validateStored(prefs.getString("base",""),httpConsent);
            token=MainActivity.decrypt(prefs.getString("secret",""));
            roomMode=prefs.getBoolean("room_audio_enabled",false);
            active=true;ui="connecting";
            keepalive.setEnabled(prefs.getBoolean("keepalive_enabled",false));
            io.scheduleWithFixedDelay(this::poll,0,900,TimeUnit.MILLISECONDS);
        }catch(Exception e){ui="credentials_error";stopSelf();}
        return START_NOT_STICKY;
    }
    private HttpURLConnection connection(String path,String method)throws Exception{String approved=HaAddress.validateStored(base,httpConsent);HttpURLConnection c=(HttpURLConnection)new URL(approved+path).openConnection();c.setConnectTimeout(5000);c.setReadTimeout(15000);c.setInstanceFollowRedirects(false);c.setRequestMethod(method);c.setRequestProperty("Authorization","Bearer "+token);return c;}
    private String readCommand()throws Exception{HttpURLConnection c=connection("/api/states/"+COMMAND,"GET");try{if(c.getResponseCode()!=200)throw new IOException("HA HTTP "+c.getResponseCode());try(InputStream in=c.getInputStream()){ByteArrayOutputStream b=new ByteArrayOutputStream();byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1){if(b.size()+n>32768)throw new IOException("HA response too large");b.write(buf,0,n);}return new JSONObject(new String(b.toByteArray(),StandardCharsets.UTF_8)).getString("state");}}finally{c.disconnect();}}
    private void publish(String status)throws Exception{if(roomMode){reportRoom(status);return;}HttpURLConnection c=connection("/api/services/input_text/set_value","POST");try{c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");byte[] data=new JSONObject().put("entity_id",STATUS).put("value",status).toString().getBytes(StandardCharsets.UTF_8);try(OutputStream out=c.getOutputStream()){out.write(data);}if(c.getResponseCode()!=200)throw new IOException("HA status HTTP "+c.getResponseCode());}finally{c.disconnect();}}
    private void state(String status){cachedStatus=status;ui=status; if(!io.isShutdown())io.execute(()->{if(active)try{publish(status);}catch(Exception ignored){}});}
    AudioDeviceInfo bluetooth(){for(AudioDeviceInfo d:am.getDevices(AudioManager.GET_DEVICES_OUTPUTS))if(d.getType()==AudioDeviceInfo.TYPE_BLUETOOTH_A2DP)return d;return null;}
    private void poll(){if(!active)return;if(roomMode){pollRoom();return;}try{String cmd=readCommand();if(!baseline){lastCommand=cmd;baseline=true;}else if(!cmd.equals(lastCommand)){lastCommand=cmd;try{JSONObject j=new JSONObject(cmd);String next=j.optString("id"),path=j.optString("path");long age=System.currentTimeMillis()-j.optLong("ts",0);if(next.matches("[a-zA-Z0-9-]{1,40}")&&age>=-5000&&age<15000){if(j.optBoolean("stop")){if(next.equals(id))main.post(()->finish("cancelled"));}else if(!busy&&PATH.matcher(path).matches()){busy=true;id=next;state(id+"|buffering");main.post(()->startStreaming(next,path));}}}catch(Exception ignored){}}
        long now=System.currentTimeMillis();if(!busy&&now-heartbeat>5000){heartbeat=now;String status=bluetooth()!=null?"ready|"+now:"no_bluetooth|"+now;publish(status);ui=status;}else if(busy&&now-heartbeat>6000){heartbeat=now;if(!cachedStatus.isEmpty())publish(cachedStatus);}
        haConnected=true;
      }catch(Exception e){haConnected=false;if(!busy)ui=e.getMessage()!=null&&(e.getMessage().contains("401")||e.getMessage().contains("403"))?"credentials_error":"connection_error|"+e.getClass().getSimpleName();}}
    private JSONObject roomApi(JSONObject body)throws Exception {
        HttpURLConnection c=connection("/api/jarvis_echo_relay/room_audio","POST");
        try{
            c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");
            byte[] bytes=body.toString().getBytes(StandardCharsets.UTF_8);
            try(OutputStream out=c.getOutputStream()){out.write(bytes);}
            int code=c.getResponseCode();
            if(code!=200)throw new IOException("Room HTTP "+code);
            try(InputStream in=c.getInputStream()){
                ByteArrayOutputStream out=new ByteArrayOutputStream();
                byte[] buffer=new byte[2048];int n;
                while((n=in.read(buffer))!=-1){if(out.size()+n>32768)throw new IOException("Room response too large");out.write(buffer,0,n);}
                return new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));
            }
        }finally{c.disconnect();}
    }
    private void reportRoom(String status)throws Exception{
        if(roomSession.isEmpty())return;
        String[] parts=status.split("\\|",3);
        if(parts.length<2||!parts[0].matches("[a-f0-9]{32}"))return;
        String stage=parts[1];
        if(stage.startsWith("error"))stage="error";
        if(!stage.matches("buffering|playing|done|cancelled|error"))return;
        roomApi(new JSONObject().put("action","report").put("session",roomSession).put("id",parts[0]).put("stage",stage));
    }
    private void pollRoom(){
        try{
            long now=System.currentTimeMillis();
            if(roomSession.isEmpty()){
                if(now<roomRetryAt)return;
                JSONObject joined=roomApi(new JSONObject().put("action","connect"));
                String candidate=joined.optString("session");
                if(!candidate.matches("[a-f0-9]{64}"))throw new IOException("Invalid room session");
                roomSession=candidate;
            }
            boolean ready=!busy&&bluetooth()!=null;
            JSONObject job=roomApi(new JSONObject().put("action","poll").put("session",roomSession).put("ready",ready));
            String next=job.optString("id"),path=job.optString("path");
            if(next.matches("[a-f0-9]{32}")){
                if(job.optBoolean("stop")){
                    if(next.equals(id)&&busy)main.post(()->finish("cancelled"));
                    else roomApi(new JSONObject().put("action","report").put("session",roomSession).put("id",next).put("stage","cancelled"));
                }else if(ready&&PATH.matcher(path).matches()){
                    busy=true;id=next;state(id+"|buffering");main.post(()->startStreaming(next,path));
                }else if(!busy){
                    roomApi(new JSONObject().put("action","report").put("session",roomSession).put("id",next).put("stage","error"));
                }
            }
            if(!busy){ui=(bluetooth()!=null?"ready|":"no_bluetooth|")+now;}
            else if(!cachedStatus.isEmpty()&&now-heartbeat>5000){heartbeat=now;reportRoom(cachedStatus);}
            haConnected=true;
        }catch(Exception e){
            haConnected=false;
            String msg=e.getMessage()==null?"":e.getMessage();
            if(msg.contains("403")||msg.contains("409")){
                roomSession="";roomRetryAt=System.currentTimeMillis()+3000;
                if(busy)main.post(()->finish("error_room_session"));
            }
            if(!busy)ui=msg.contains("401")||msg.contains("403")?"credentials_error":"connection_error|"+e.getClass().getSimpleName();
        }
    }
    private boolean takeSpeechFocus() {
        if(focus!=null)am.abandonAudioFocusRequest(focus);
        String focusId=id;
        AudioAttributes attrs=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build();
        focus=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT).setAudioAttributes(attrs)
                .setOnAudioFocusChangeListener(change->{
                    if(change==AudioManager.AUDIOFOCUS_LOSS||change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT){
                        if(focusId.equals(id)){
                            finish("error_focus");
                            if(keepalive!=null&&getSharedPreferences(MainActivity.PREF,0).getBoolean("keepalive_enabled",false))keepalive.pauseForFocus();
                        }
                    }
                },main).build();
        return am.requestAudioFocus(focus)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED;
    }

    private void startStreaming(String request,String path) {
        if(!active||!busy||!request.equals(id))return;
        if(bluetooth()==null){finish("error_no_bluetooth");return;}
        if(!takeSpeechFocus()){finish("error_focus");return;}
        streamDiagnostics="mode=preparing; startup_buffer_ms="+StreamingSession.START_BUFFER_MS;
        StreamCallbacks callbacks=new StreamCallbacks(request);
        streaming=new StreamingSession(getCacheDir(),()->connection(path,"GET"),
                first->new AndroidMp3Decoder(first,()->!active||!busy||!request.equals(id)),
                stopped->new BluetoothPcmOutput(am,stopped),callbacks);
        callbacks.owner=streaming;
        StreamingSession session=streaming;
        streamWatchdog=()->{if(streaming==session&&busy)finish("error_stream_timeout");};
        main.postDelayed(streamWatchdog,120000);
        session.start();
    }

    private final class StreamCallbacks implements StreamingSession.Listener {
        final String request;
        StreamingSession owner;
        StreamCallbacks(String request){this.request=request;}
        boolean current(){return active&&busy&&request.equals(id)&&streaming==owner;}
        public void onPlaying(String diagnostic){main.post(()->{if(current()){streamDiagnostics=diagnostic;state(id+"|playing|bluetooth");}});}
        public void onBuffering(String diagnostic){main.post(()->{if(current()){streamDiagnostics=diagnostic;state(id+"|buffering");}});}
        public void onDone(String diagnostic){main.post(()->{if(current()){streamDiagnostics=diagnostic;finish("done");}});}
        public void onError(String error,String diagnostic){main.post(()->{if(current()){streamDiagnostics=diagnostic;finish(error);}});}
        public void onFallback(File cached,String diagnostic){
            main.post(()->{
                if(!current()){cached.delete();return;}
                streamDiagnostics=diagnostic;streaming=null;
                if(streamWatchdog!=null)main.removeCallbacks(streamWatchdog);
                streamWatchdog=null;
                state(id+"|buffering");startPlayer(cached);
            });
        }
    }
    private void startPlayer(File f) {
        file = f;
        try {
            if (bluetooth() == null) { finish("error_no_bluetooth"); return; }
            AudioAttributes attrs = new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build();
            if (!takeSpeechFocus()) {
                finish("error_focus"); return;
            }
            player = new MediaPlayer();
            player.setAudioAttributes(attrs);
            try (FileInputStream source = new FileInputStream(file)) { player.setDataSource(source.getFD()); }
            player.setVolume(0, 0);
            // setDataSource must initialize the player engine before requesting a device.
            requestBluetoothRoute(player);
            player.setOnErrorListener((p, what, extra) -> {
                if (p == player) finish("error_media_" + what + "_" + extra);
                return true;
            });
            player.setOnCompletionListener(p -> { if (p == player) finish(audible ? "done" : "error_route_short_audio"); });
            player.setOnPreparedListener(p -> {
                if (p != player || !busy || !active) return;
                try {
                    requestBluetoothRoute(p);
                    p.start();
                    long now = SystemClock.elapsedRealtime();
                    checkUntil = now + 4000;
                    playUntil = now + 120000;
                    routeRetryAt = now + 500;
                    main.post(routeCheck);
                } catch (RuntimeException e) { finish("error_player_start"); }
            });
            player.prepareAsync();
            main.postDelayed(() -> {
                if (busy && file == f && !audible && player != null && checkUntil == 0) finish("error_prepare_timeout");
            }, 15000);
        } catch (Exception e) { finish("error_player"); }
    }

    private void requestBluetoothRoute(MediaPlayer target) {
        routeAttempts++;
        AudioDeviceInfo device = bluetooth();
        try { preferredAccepted = device != null && target.setPreferredDevice(device); }
        catch (RuntimeException e) { preferredAccepted = false; }
        // A rejected preference is not proof of a bad route. Android may already be using A2DP.
    }
    final Runnable routeCheck=new Runnable(){public void run(){
        if(!active||!busy||player==null)return;
        try{
            AudioDeviceInfo d=player.getRoutedDevice();boolean routed=d!=null&&d.getType()==AudioDeviceInfo.TYPE_BLUETOOTH_A2DP&&(!audible||d.getId()==preferredId);
            long now=SystemClock.elapsedRealtime();if(now>playUntil){finish("error_play_timeout");return;}
            if(audible){if(!routed){player.setVolume(0,0);finish("error_route_lost");return;}main.postDelayed(this,100);return;}
            if(!routed){if(now>=checkUntil){finish("error_route_"+(d==null?"unknown":"type_"+d.getType())+(preferredAccepted?"_preferred_ok":"_preferred_rejected"));return;}if(routeAttempts<3&&now>=routeRetryAt)requestBluetoothRoute(player);main.postDelayed(this,60);return;}
            if(seeked){preferredId=d.getId();player.setVolume(1,1);audible=true;state(id+"|playing|bluetooth");main.postDelayed(this,100);return;}
            // Establish routing silently, then restart at the beginning of the buffered file.
            player.pause();
            player.setOnSeekCompleteListener(p->{if(p!=player||!busy||audible)return;try{seeked=true;checkUntil=SystemClock.elapsedRealtime()+2000;p.start();main.post(this);}catch(RuntimeException e){finish("error_player_restart");}});
            player.seekTo(0,MediaPlayer.SEEK_CLOSEST);
            MediaPlayer waiting=player;main.postDelayed(()->{if(busy&&player==waiting&&!seeked)finish("error_seek");},2000);
        }catch(Exception e){finish("error_route");}
    }};
    private void finish(String result){if(!busy)return;main.removeCallbacks(routeCheck);if(streamWatchdog!=null)main.removeCallbacks(streamWatchdog);streamWatchdog=null;StreamingSession current=streaming;streaming=null;if(current!=null)current.cancel();if(player!=null){try{player.setVolume(0,0);player.release();}catch(Exception ignored){}player=null;}if(focus!=null){am.abandonAudioFocusRequest(focus);focus=null;}if(file!=null){file.delete();file=null;}audible=false;seeked=false;preferredAccepted=false;preferredId=-1;routeAttempts=0;routeRetryAt=0;checkUntil=0;playUntil=0;String ended=id;busy=false;heartbeat=System.currentTimeMillis();state(ended+"|"+result);}
    @Override public void onDestroy(){active=false;running=false;haConnected=false;if(keepalive!=null)keepalive.close();finish("cancelled");io.shutdownNow();main.removeCallbacksAndMessages(null);ui="stopped";stopForeground(true);super.onDestroy();}
}
