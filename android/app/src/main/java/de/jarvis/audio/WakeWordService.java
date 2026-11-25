package de.jarvis.audio;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.os.*;
import android.util.Log;
import org.json.JSONObject;
import org.vosk.Model;
import org.vosk.Recognizer;
import org.vosk.android.RecognitionListener;
import org.vosk.android.SpeechService;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Experimental, explicitly enabled, offline wakeword recognition.
 * Only the matched phrase is sent to the configured Home Assistant.
 * Raw microphone audio and ordinary speech are never uploaded or saved.
 */
public final class WakeWordService extends Service implements RecognitionListener {
    static final String START="de.jarvis.audio.WAKE_START",STOP="de.jarvis.audio.WAKE_STOP";
    static volatile boolean running=false;
    static volatile String status="off";
    private static final String CHANNEL="jarvis-wake",TAG="JarvisWake";
    private static final long SYNC_INTERVAL_MS=2500;
    private final Handler main=new Handler(Looper.getMainLooper());
    private boolean enabled=false,loading=false,muted=true;
    private String wordChoice="hey_jarvis";
    private int strictness=1,cooldownSeconds=12,holdSeconds=50;
    private final WakeTriggerGate triggerGate=new WakeTriggerGate();
    private ScheduledExecutorService settingsExecutor;
    private long lastFullSync=0;
    private int activeSettingsSlot=0;
    private Model model;
    private Recognizer recognizer;
    private SpeechService speech;
    private long holdUntil=0,lastHit=0;
    private final Runnable rearm=this::startRecognition;

    @Override public IBinder onBind(Intent intent){return null;}

    @Override public void onCreate(){
        super.onCreate();
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel(CHANNEL,
            getString(R.string.wake_title),NotificationManager.IMPORTANCE_LOW));
    }

    private Notification notification(){
        Intent open=new Intent(this,MainActivity.class);
        PendingIntent launch=PendingIntent.getActivity(this,81,open,PendingIntent.FLAG_IMMUTABLE);
        PendingIntent stop=PendingIntent.getService(this,82,
                new Intent(this,WakeWordService.class).setAction(STOP),PendingIntent.FLAG_IMMUTABLE);
        return new Notification.Builder(this,CHANNEL)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(getString(R.string.wake_title))
            .setContentText(getString(R.string.wake_running))
            .setContentIntent(launch)
            .addAction(new Notification.Action.Builder(null,getString(R.string.wake_stop),stop).build())
            .setOngoing(true).build();
    }

    @Override public int onStartCommand(Intent intent,int flags,int startId){
        if(intent!=null&&STOP.equals(intent.getAction())){
            enabled=false;
            stopSelf();
            return START_NOT_STICKY;
        }
        if(enabled)return START_NOT_STICKY;
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
            status="permission_required";stopSelf();return START_NOT_STICKY;
        }
        if(!WakeModelInstaller.installed(this)){
            status="model_missing";stopSelf();return START_NOT_STICKY;
        }
        wordChoice=getSharedPreferences(MainActivity.PREF,0).getString("wake_choice","hey_jarvis");
        try{
            if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.Q)
                startForeground(43,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE);
            else startForeground(43,notification());
        }catch(Exception e){
            status="foreground_error: "+e.getClass().getSimpleName();
            stopSelf();return START_NOT_STICKY;
        }
        enabled=true;running=true;muted=true;status="loading";
        loading=true;
        startSettingsSync();
        new Thread(()->{
            try{
                Model newModel=new Model(WakeModelInstaller.modelDir(this).getAbsolutePath());
                main.post(()->{
                    loading=false;
                    if(!enabled){newModel.close();return;}
                    model=newModel;
                    startRecognition();
                });
            }catch(Exception e){
                Log.w(TAG,"Offline model loading failed",e);
                main.post(()->{loading=false;status="model_error: "+e.getClass().getSimpleName();stopSelf();});
            }
        },"JarvisWakeModel").start();
        return START_NOT_STICKY;
    }

    private void startSettingsSync(){
        if(settingsExecutor!=null)return;
        settingsExecutor=Executors.newSingleThreadScheduledExecutor(r->{
            Thread t=new Thread(r,"JarvisWakeHASettings");
            t.setDaemon(true);return t;
        });
        settingsExecutor.scheduleWithFixedDelay(()->{
            if(!enabled)return;
            try{
                int currentSlot=WakeDeviceIdentity.slot(this);
                boolean full=currentSlot!=activeSettingsSlot||SystemClock.elapsedRealtime()-lastFullSync>=12000;
                if(full){
                    WakePilotSettings.Snapshot settings=WakePilotSettings.readFull(this);
                    lastFullSync=SystemClock.elapsedRealtime();
                    activeSettingsSlot=currentSlot;
                    main.post(()->{
                        if(!enabled)return;
                        wordChoice=settings.word;
                        strictness=settings.strictness;
                        cooldownSeconds=settings.cooldownSeconds;
                        holdSeconds=settings.holdSeconds;
                        setMuted(settings.muted);
                    });
                }else{
                    boolean remoteMute=WakePilotSettings.readMute(this);
                    main.post(()->{if(enabled)setMuted(remoteMute);});
                }
            }catch(Exception e){
                // Fail closed: if HA is unreachable, the remote mute switch cannot
                // be honored reliably, so release the microphone.
                main.post(()->{
                    if(!enabled)return;
                    setMuted(true);
                    status="ha_settings_error: "+e.getClass().getSimpleName();
                });
            }
        },0,SYNC_INTERVAL_MS,TimeUnit.MILLISECONDS);
    }

    private void setMuted(boolean shouldMute){
        if(!enabled)return;
        if(shouldMute){
            if(!muted||speech!=null){
                muted=true;
                releaseRecognizer();
                triggerGate.reset();
            }
            status="muted";
        }else{
            boolean wasMuted=muted;
            muted=false;
            if(wasMuted||speech==null)startRecognition();
        }
    }

    private void startRecognition(){
        main.removeCallbacks(rearm);
        if(!enabled||model==null||loading||muted)return;
        long remaining=holdUntil-SystemClock.elapsedRealtime();
        if(remaining>0){
            main.postDelayed(rearm,Math.max(500,remaining));
            return;
        }
        if(speech!=null)return;
        wordChoice=getSharedPreferences(MainActivity.PREF,0).getString("wake_choice","hey_jarvis");
        try{
            String grammar="["+ 
                "\"hey jarvis\",\"jarvis\",\"alexa\",\"hey jarwis\",\"jarwis\","+
                "\"hei jarvis\",\"[unk]\"]";
            recognizer=new Recognizer(model,16000f,grammar);
            speech=new SpeechService(recognizer,16000f);
            if(!speech.startListening(this))throw new IllegalStateException("Recorder not started");
            status="listening: "+wordChoice;
        }catch(Exception e){
            Log.w(TAG,"Wakeword microphone unavailable",e);
            status="microphone_error: "+e.getClass().getSimpleName();
            releaseRecognizer();
            main.postDelayed(rearm,5000);
        }
    }

    private void releaseRecognizer(){
        SpeechService old=speech;
        speech=null;
        if(old!=null){
            try{old.cancel();}catch(Exception ignored){}
            try{old.shutdown();}catch(Exception ignored){}
        }
        Recognizer r=recognizer;recognizer=null;
        if(r!=null)try{r.close();}catch(Exception ignored){}
    }

    private void candidate(String json,String key){
        if(!enabled||speech==null||muted)return;
        String transcript;
        try{transcript=new JSONObject(json).optString(key,"");}catch(Exception e){return;}
        String hit=WakeWordMatcher.matched(transcript,wordChoice);
        if(hit==null){triggerGate.reset();return;}
        if(!triggerGate.confirm(hit,strictness))return;
        long now=SystemClock.elapsedRealtime();
        if(now-lastHit<cooldownSeconds*1000L)return;
        triggerGate.reset();
        lastHit=now;holdUntil=now+holdSeconds*1000L;
        // Release microphone BEFORE telling the browser to start its STT pipeline.
        releaseRecognizer();
        status="detected: "+hit;
        sendWakeEvent(hit);
        main.postDelayed(rearm,holdSeconds*1000L);
    }

    @Override public void onPartialResult(String text){candidate(text,"partial");}
    @Override public void onResult(String text){candidate(text,"text");}
    @Override public void onFinalResult(String text){candidate(text,"text");}
    @Override public void onError(Exception e){
        Log.w(TAG,"Wakeword recognition error",e);
        if(enabled){
            status="recognition_error: "+e.getClass().getSimpleName();
            releaseRecognizer();
            main.postDelayed(rearm,5000);
        }
    }
    @Override public void onTimeout(){
        if(enabled){
            releaseRecognizer();
            main.postDelayed(rearm,1000);
        }
    }

    private void sendWakeEvent(String word){
        new Thread(()->{
            HttpURLConnection conn=null;
            try{
                var prefs=getSharedPreferences(MainActivity.PREF,0);
                String base=HaAddress.validateStored(
                    prefs.getString("base",""),prefs.getString(MainActivity.HTTP_CONSENT,""));
                String token=MainActivity.decrypt(prefs.getString("secret",""));
                URL url=new URL(base+"/api/events/jarvis_android_wakeword");
                conn=(HttpURLConnection)url.openConnection();
                conn.setInstanceFollowRedirects(false);
                conn.setRequestMethod("POST");
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(8000);
                conn.setRequestProperty("Authorization","Bearer "+token);
                conn.setRequestProperty("Content-Type","application/json");
                conn.setDoOutput(true);
                byte[] body=new JSONObject().put("source","android_echo_relay")
                    .put("version",2)
                    .put("device_id",WakeDeviceIdentity.get(this))
                    .put("slot",WakeDeviceIdentity.slot(this))
                    .put("room",WakeDeviceIdentity.room(this))
                    .put("wakeword",word).put("timestamp_ms",System.currentTimeMillis())
                    .toString().getBytes(StandardCharsets.UTF_8);
                conn.setFixedLengthStreamingMode(body.length);
                try(java.io.OutputStream out=conn.getOutputStream()){out.write(body);}
                int statusCode=conn.getResponseCode();
                if(statusCode<200||statusCode>=300)throw new java.io.IOException("HA HTTP "+statusCode);
                status="sent: "+word;
            }catch(Exception e){
                Log.w(TAG,"HA wake event failed",e);
                status="delivery_error: "+e.getClass().getSimpleName();
            }finally{if(conn!=null)conn.disconnect();}
        },"JarvisWakeEvent").start();
    }

    @Override public void onDestroy(){
        enabled=false;running=false;muted=true;
        main.removeCallbacks(rearm);
        if(settingsExecutor!=null){settingsExecutor.shutdownNow();settingsExecutor=null;}
        releaseRecognizer();
        if(model!=null){try{model.close();}catch(Exception ignored){}model=null;}
        if(status.startsWith("listening")||status.startsWith("detected")||status.startsWith("sent"))
            status="off";
        super.onDestroy();
    }
}
