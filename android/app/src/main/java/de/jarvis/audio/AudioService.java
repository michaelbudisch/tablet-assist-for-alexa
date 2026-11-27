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
    private VoiceTrace.Playback activeProbe;
    private int fileUnmutePosition=-1;
    private boolean fileProgressObserved;
    static volatile String ui="stopped", keepaliveStatus="off", streamDiagnostics="";
    static volatile boolean running=false, haConnected=false;
    private static final String NATIVE_JOB_READY="native_job_ready";
    /** Wake an explicitly running player; never reconnect a stopped player. */
    static boolean notifyNativeJobReady(Context context){
        if(!running)return false;
        try{
            context.startService(new Intent(context,AudioService.class).setAction(NATIVE_JOB_READY));
            return true;
        }catch(RuntimeException stopped){return false;}
    }
    private BluetoothKeepalive keepalive;
    private volatile BluetoothPcmOutput pcmOutput;
    private String playbackMode=AudioOutputMode.AUTO;
    private int fileOutputType;
    private final SharedPreferences.OnSharedPreferenceChangeListener outputPreferenceListener=(p,key)->{
        if(AudioOutputMode.KEY.equals(key)||"keepalive_enabled".equals(key))updateKeepalive();
    };
    private void updateKeepalive(){
        if(keepalive!=null)keepalive.setEnabled(!AudioOutputMode.TABLET.equals(AudioOutputMode.get(this))&&
            getSharedPreferences(MainActivity.PREF,0).getBoolean("keepalive_enabled",false));
    }
    private AudioDeviceInfo selectedOutput(){return AudioOutputMode.find(am,AudioOutputMode.select(am,AudioOutputMode.get(this)));}
    // Direct TAFA multiroom playback is the only supported audio transport.
    static final Pattern PATH=Pattern.compile("/api/tts_proxy/[A-Za-z0-9_.~-]{1,200}");
    final Handler main=new Handler(Looper.getMainLooper());
    final ScheduledExecutorService io=Executors.newSingleThreadScheduledExecutor();
    // The native Bluetooth player and microphone may be started independently.
    // Enroll on a separate executor so HA device registration cannot delay
    // room audio polling, voice playback or the Android main thread.
    final ScheduledExecutorService enrollmentIo=Executors.newSingleThreadScheduledExecutor(r->{
        Thread thread=new Thread(r,"TAFA-Tablet-Enrollment");
        thread.setDaemon(true);
        return thread;
    });
    private volatile boolean tabletEnrolled=false;
    private StreamingSession streaming;
    private Runnable streamWatchdog;
    volatile boolean active=false,busy=false; volatile String id="", cachedStatus="";
    private final RoomPollWakeup pollWakeup=new RoomPollWakeup(io,()->active&&!busy,this::poll);
    String base,token,httpConsent; long heartbeat=0;
    private String roomSession="";
    private volatile String roomTerminal="";
    private long roomRetryAt=0;
    MediaPlayer player; File file; AudioManager am; AudioFocusRequest focus; boolean audible=false,seeked=false,preferredAccepted=false; int preferredId=-1,routeAttempts=0; long checkUntil=0,playUntil=0,routeRetryAt=0;
    @Override public IBinder onBind(Intent i){return null;}
    @Override public void onCreate() {
        super.onCreate();
        File[] stale=getCacheDir().listFiles((dir,name)->name.startsWith("jarvis-")&&name.endsWith(".audio"));
        if(stale!=null)for(File f:stale)f.delete();
        am=(AudioManager)getSystemService(AUDIO_SERVICE);
        keepalive=new BluetoothKeepalive(this, status -> keepaliveStatus=status);
        AudioOutputMode.prefs(this).registerOnSharedPreferenceChangeListener(outputPreferenceListener);
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
        if(NATIVE_JOB_READY.equals(action)){
            if(active)pollWakeup.request();
            else stopSelf(startId);
            return START_NOT_STICKY;
        }
        if(active){
            if("update_keepalive".equals(action))updateKeepalive();
            return START_NOT_STICKY;
        }
        try{
            var prefs=getSharedPreferences(MainActivity.PREF,0);
            httpConsent=prefs.getString(MainActivity.HTTP_CONSENT,"");
            base=HaAddress.validateStored(prefs.getString("base",""),httpConsent);
            token=MainActivity.decrypt(prefs.getString("secret",""));
            active=true;ui="connecting";
            updateKeepalive();
            io.scheduleWithFixedDelay(this::poll,0,900,TimeUnit.MILLISECONDS);
            // The first successful room connection is sufficient to enroll
            // this tablet, even if native wakeword is not yet enabled.
            enrollmentIo.scheduleWithFixedDelay(this::syncTabletEnrollment,
                2,20,TimeUnit.SECONDS);
        }catch(Exception e){ui="credentials_error";stopSelf();}
        return START_NOT_STICKY;
    }
    private HttpURLConnection connection(String path,String method)throws Exception{String approved=HaAddress.validateStored(base,httpConsent);HttpURLConnection c=(HttpURLConnection)new URL(approved+path).openConnection();c.setConnectTimeout(5000);c.setReadTimeout(15000);c.setInstanceFollowRedirects(false);c.setRequestMethod(method);c.setRequestProperty("Authorization","Bearer "+token);return c;}
    private void publish(String status)throws Exception{reportRoom(status);}
    private void state(String status){cachedStatus=status;ui=status;if(!io.isShutdown())io.execute(()->{if(active)try{publish(status);}catch(Exception ignored){}});}
    AudioDeviceInfo bluetooth(){for(AudioDeviceInfo d:am.getDevices(AudioManager.GET_DEVICES_OUTPUTS))if(d.getType()==AudioDeviceInfo.TYPE_BLUETOOTH_A2DP)return d;return null;}
    private void poll(){if(active)pollRoom();}

    private void syncTabletEnrollment(){
        // The room connection must have succeeded before we attempt device
        // enrollment. This is an explicit player-start, not silent discovery.
        if(!active||!haConnected)return;
        try{
            if(!tabletEnrolled){
                WakePilotSettings.register(this);
                tabletEnrolled=true;
            }
            try{WakePilotSettings.syncAudioOutput(this);}catch(Exception ignored){/* Local playback remains usable with older HA versions. */}
            // Only the wakeword service should report live mic state when it
            // is running. Audio-only tablets still publish online telemetry.
            if(!WakeWordService.running){
                WakePilotSettings.report(this,"audio_ready","inactive");
            }
        }catch(Exception error){
            // After a server reset, the device may have been deleted. Retry
            // idempotent registration rather than losing the tablet forever.
            tabletEnrolled=false;
            android.util.Log.w("TAFAEnrollment",
                "Noncritical HA device enrollment retry: "+error.getClass().getSimpleName());
        }
    }
    private JSONObject roomApi(JSONObject body)throws Exception {
        HttpURLConnection c=connection("/api/tablet_assist_for_alexa/room_audio","POST");
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
        if(status.equals(roomTerminal))roomTerminal="";
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
            if(!roomTerminal.isEmpty())reportRoom(roomTerminal);
            boolean ready=!busy&&selectedOutput()!=null;
            JSONObject job=roomApi(new JSONObject().put("action","poll").put("session",roomSession).put("ready",ready));
            String next=job.optString("id"),path=job.optString("path");
            if(next.matches("[a-f0-9]{32}")){
                if(job.optBoolean("stop")){
                    if(next.equals(id)&&busy)main.post(()->finish("cancelled"));
                    else roomApi(new JSONObject().put("action","report").put("session",roomSession).put("id",next).put("stage","cancelled"));
                }else if(ready&&PATH.matcher(path).matches()){
                    VoiceDiagnostics.playback(this,next).mark(VoiceTrace.Point.JOB_RECEIVED);
                    busy=true;id=next;state(id+"|buffering");main.post(()->startStreaming(next,path));
                }else if(!busy){
                    roomApi(new JSONObject().put("action","report").put("session",roomSession).put("id",next).put("stage","error"));
                }
            }
            if(!busy){AudioDeviceInfo output=selectedOutput();ui=output==null?"no_bluetooth|"+now:"ready|"+now+"|"+AudioOutputMode.label(output.getType());}
            else if(!cachedStatus.isEmpty()&&now-heartbeat>5000){heartbeat=now;reportRoom(cachedStatus);}
            haConnected=true;
        }catch(Exception e){
            haConnected=false;
            String msg=e.getMessage()==null?"":e.getMessage();
            if(msg.contains("403")||msg.contains("409")){
                roomSession="";roomTerminal="";roomRetryAt=System.currentTimeMillis()+3000;
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
        activeProbe=VoiceDiagnostics.playback(this,request);
        activeProbe.fact(VoiceTrace.Fact.ENGINE,"pcm");
        activeProbe.fact(VoiceTrace.Fact.START_BUFFER_MS,StreamingSession.START_BUFFER_MS);
        playbackMode=AudioOutputMode.get(this);
        if(AudioOutputMode.find(am,AudioOutputMode.select(am,playbackMode))==null){finish("error_route_unavailable");return;}
        if(!takeSpeechFocus()){finish("error_focus");return;}
        activeProbe.mark(VoiceTrace.Point.AUDIO_FOCUS);
        streamDiagnostics="mode=preparing; startup_buffer_ms="+StreamingSession.START_BUFFER_MS;
        StreamCallbacks callbacks=new StreamCallbacks(request);
        streaming=new StreamingSession(getCacheDir(),()->connection(path,"GET"),
                first->new AndroidMp3Decoder(first,()->!active||!busy||!request.equals(id)),
                stopped->{BluetoothPcmOutput output=new BluetoothPcmOutput(am,stopped,playbackMode,VoiceDiagnostics.enabled()?callbacks.probe:null);pcmOutput=output;return output;},callbacks);
        callbacks.owner=streaming;
        StreamingSession session=streaming;
        streamWatchdog=()->{if(streaming==session&&busy)finish("error_stream_timeout");};
        main.postDelayed(streamWatchdog,120000);
        session.start();
    }

    private final class StreamCallbacks implements StreamingSession.Listener {
        final String request;
        StreamingSession owner;
        final VoiceTrace.Playback probe;
        StreamCallbacks(String request){this.request=request;this.probe=VoiceDiagnostics.playback(AudioService.this,request);}
        @Override public void timing(VoiceTrace.Point point){probe.mark(point);}
        @Override public void metric(VoiceTrace.Fact fact,long value){probe.fact(fact,value);}
        boolean current(){return active&&busy&&request.equals(id)&&streaming==owner;}
        public void onPlaying(String diagnostic){main.post(()->{if(current()){streamDiagnostics=diagnostic;state(id+"|playing|"+(pcmOutput==null?AudioOutputMode.label(AudioOutputMode.select(am,playbackMode)):pcmOutput.routeLabel()));}});}
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
        fileUnmutePosition=-1;fileProgressObserved=false;
        if(activeProbe!=null)activeProbe.fact(VoiceTrace.Fact.ENGINE,"file");
        try {
            fileOutputType=AudioOutputMode.select(am,playbackMode);
            if (AudioOutputMode.find(am,fileOutputType)==null) { finish("error_route_unavailable"); return; }
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
            requestOutputRoute(player);
            player.setOnErrorListener((p, what, extra) -> {
                if (p == player) finish("error_media_" + what + "_" + extra);
                return true;
            });
            player.setOnCompletionListener(p -> { if (p == player) finish(audible ? "done" : "error_route_short_audio"); });
            player.setOnPreparedListener(p -> {
                if (p != player || !busy || !active) return;
                try {
                    requestOutputRoute(p);
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

    private void requestOutputRoute(MediaPlayer target) {
        routeAttempts++;
        AudioDeviceInfo device = AudioOutputMode.find(am,fileOutputType);
        try { preferredAccepted = device != null && target.setPreferredDevice(device); }
        catch (RuntimeException e) { preferredAccepted = false; }
        // A rejected preference is not proof of a bad route. Android may already be using A2DP.
    }
    final Runnable routeCheck=new Runnable(){public void run(){
        if(!active||!busy||player==null)return;
        try{
            AudioDeviceInfo d=player.getRoutedDevice();boolean routed=d!=null&&d.getType()==fileOutputType&&(!audible||d.getId()==preferredId);
            long now=SystemClock.elapsedRealtime();if(now>playUntil){finish("error_play_timeout");return;}
            if(audible){if(!routed){player.setVolume(0,0);finish("error_route_lost");return;}
                if(activeProbe!=null&&!fileProgressObserved&&player.isPlaying()&&player.getCurrentPosition()>fileUnmutePosition){
                    fileProgressObserved=true;
                    activeProbe.fact(VoiceTrace.Fact.OUTPUT_QUALITY,"mediaplayer_position_100ms");
                    activeProbe.mark(VoiceTrace.Point.OUTPUT_PROGRESS);
                }
                main.postDelayed(this,100);return;}
            if(!routed){
                if(AudioOutputMode.AUTO.equals(playbackMode)&&fileOutputType==AudioDeviceInfo.TYPE_BLUETOOTH_A2DP&&
                        (AudioOutputMode.find(am,fileOutputType)==null||now>=checkUntil)){
                    fileOutputType=AudioDeviceInfo.TYPE_BUILTIN_SPEAKER;routeAttempts=0;checkUntil=now+4000;requestOutputRoute(player);
                }
                if(now>=checkUntil){finish("error_route_"+(d==null?"unknown":"type_"+d.getType())+(preferredAccepted?"_preferred_ok":"_preferred_rejected"));return;}if(routeAttempts<3&&now>=routeRetryAt)requestOutputRoute(player);main.postDelayed(this,60);return;}
            if(seeked){preferredId=d.getId();fileUnmutePosition=player.getCurrentPosition();player.setVolume(1,1);audible=true;
                if(activeProbe!=null){
                    activeProbe.fact(VoiceTrace.Fact.OUTPUT,AudioOutputMode.label(fileOutputType));
                    activeProbe.mark(VoiceTrace.Point.ROUTE_READY);
                    activeProbe.mark(VoiceTrace.Point.OUTPUT_SUBMITTED);
                }
                state(id+"|playing|"+AudioOutputMode.label(fileOutputType));main.postDelayed(this,100);return;}
            // Establish routing silently, then restart at the beginning of the buffered file.
            player.pause();
            player.setOnSeekCompleteListener(p->{if(p!=player||!busy||audible)return;try{seeked=true;checkUntil=SystemClock.elapsedRealtime()+2000;p.start();main.post(this);}catch(RuntimeException e){finish("error_player_restart");}});
            player.seekTo(0,MediaPlayer.SEEK_CLOSEST);
            MediaPlayer waiting=player;main.postDelayed(()->{if(busy&&player==waiting&&!seeked)finish("error_seek");},2000);
        }catch(Exception e){finish("error_route");}
    }};
    private void finish(String result){if(!busy)return;
        if(activeProbe!=null&&"done".equals(result))activeProbe.mark(VoiceTrace.Point.PLAYBACK_END);
        activeProbe=null;fileUnmutePosition=-1;main.removeCallbacks(routeCheck);if(streamWatchdog!=null)main.removeCallbacks(streamWatchdog);streamWatchdog=null;StreamingSession current=streaming;streaming=null;pcmOutput=null;if(current!=null)current.cancel();if(player!=null){try{player.setVolume(0,0);player.release();}catch(Exception ignored){}player=null;}if(focus!=null){am.abandonAudioFocusRequest(focus);focus=null;}if(file!=null){file.delete();file=null;}audible=false;seeked=false;preferredAccepted=false;preferredId=-1;routeAttempts=0;routeRetryAt=0;checkUntil=0;playUntil=0;String ended=id;busy=false;heartbeat=System.currentTimeMillis();roomTerminal=ended+"|"+result;state(ended+"|"+result);if(active)pollWakeup.request();}
    @Override public void onDestroy(){AudioOutputMode.prefs(this).unregisterOnSharedPreferenceChangeListener(outputPreferenceListener);active=false;running=false;haConnected=false;enrollmentIo.shutdownNow();if(keepalive!=null)keepalive.close();finish("cancelled");try{io.execute(()->{try{if(!roomSession.isEmpty())roomApi(new JSONObject().put("action","disconnect").put("session",roomSession));}catch(Exception ignored){}});}catch(RejectedExecutionException ignored){}io.shutdown();main.removeCallbacksAndMessages(null);ui="stopped";stopForeground(true);super.onDestroy();}
}
