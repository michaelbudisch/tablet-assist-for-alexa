package de.jarvis.audio;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.*;
import android.util.Log;
import org.json.JSONObject;
import org.vosk.Model;
import org.vosk.Recognizer;
import org.vosk.android.RecognitionListener;
import org.vosk.android.SpeechService;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.util.ArrayDeque;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Foreground, on-device wakeword detector for the one TAFA speech transport.
 * Native wakeword or opt-in local speech activity starts the existing HA Assist
 * websocket. No recordings or transcripts are stored.
 */
public final class WakeWordService extends Service implements RecognitionListener {
    static final String START="de.jarvis.audio.WAKE_START",STOP="de.jarvis.audio.WAKE_STOP",
        NATIVE_SETTINGS="de.jarvis.audio.NATIVE_SETTINGS",
        NATIVE_TEST="de.jarvis.audio.NATIVE_TEST";
    static volatile boolean running=false;
    static volatile String status="off";
    private static final String CHANNEL="jarvis-wake",TAG="JarvisWake";
    private static final long SYNC_INTERVAL_MS=500;
    private final Handler main=new Handler(Looper.getMainLooper());
    private boolean enabled=false,loading=false;
    static volatile boolean muted=true;
    private String wordChoice="hey_jarvis";
    private String voiceMode="wake";
    private volatile boolean continuousRunning=false;
    private volatile AudioRecord continuousRecorder;
    private volatile long continuousGeneration=0;
    private Thread continuousThread;
    private int strictness=1,cooldownSeconds=12,holdSeconds=50;
    private final WakeTriggerGate triggerGate=new WakeTriggerGate();
    private ScheduledExecutorService settingsExecutor;
    private NativeSettingsSocket settingsSocket;
    private long lastFullSync=0;
    private volatile boolean registered=false;
    private Model model;
    private Recognizer recognizer;
    private SpeechService speech;
    private long holdUntil=0,lastHit=0;
    private final Runnable rearm=this::startRecognition;
    private NativeAssistSession nativeSession;
    private String nativeConversationId="";
    private int completedFollowups=0;
    private boolean followupPending=false,manualPending=false;
    private final Runnable followup=()->{
        followupPending=false;
        // Settings can change between playback completion and this callback.
        if(FollowupPolicy.shouldContinue(true,completedFollowups,followupLimit()))
            beginNativeAssist("",true);
        else endConversation();
    };

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
            .setContentText(getString(status.startsWith("native_")?
                R.string.native_busy_notification:R.string.wake_running))
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
        if(intent!=null&&NATIVE_SETTINGS.equals(intent.getAction())){
            endConversation();
            return START_NOT_STICKY;
        }
        if(intent!=null&&NATIVE_TEST.equals(intent.getAction())){
            if(enabled){
                if(!muted&&nativeSession==null){
                    resetConversation();
                    manualPending=true;
                    startRecognition();
                }
                return START_NOT_STICKY;
            }
            // Explicit foreground action may start the service, but waits for
            // both the offline model and HA's authoritative mute state.
            manualPending=true;
        }
        if(enabled)return START_NOT_STICKY;
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
            status="permission_required";stopSelf();return START_NOT_STICKY;
        }
        if(!WakeModelInstaller.installed(this)&&
                !"continuous".equals(getSharedPreferences(MainActivity.PREF,0)
                    .getString("native_voice_mode","wake"))){
            status="model_missing";stopSelf();return START_NOT_STICKY;
        }
        voiceMode=WakePilotSettings.modeFor(getSharedPreferences(MainActivity.PREF,0)
            .getString("native_voice_mode","wake"));
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
        loading=!"continuous".equals(voiceMode);
        startSettingsSync();
        if(!loading){startRecognition();return START_NOT_STICKY;}
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
        settingsSocket=new NativeSettingsSocket(this,new NativeSettingsSocket.Listener(){
            @Override public void onReady(){
                lastFullSync=0;
            }
            @Override public void onSettings(org.json.JSONObject update){
                final boolean nextMuted=update.optBoolean("muted",true);
                final String nextMode=update.optString("voice_mode","wake");
                final int nextFollowups=update.optInt("followup_limit",-1);
                if(nextFollowups < -1 || nextFollowups > 100)return;
                main.post(()->{
                    if(!enabled)return;
                    getSharedPreferences(MainActivity.PREF,0).edit()
                        .putInt("native_followup_limit",nextFollowups)
                        .putBoolean("wake_muted",nextMuted)
                        .putString("native_voice_mode",nextMode).apply();
                    setVoiceSettings(nextMuted,nextMode);
                });
            }
        });
        settingsExecutor=Executors.newSingleThreadScheduledExecutor(r->{
            Thread t=new Thread(r,"JarvisWakeHASettings");
            t.setDaemon(true);return t;
        });
        settingsExecutor.scheduleWithFixedDelay(()->{
            if(!enabled)return;
            try{
                if(!registered){WakePilotSettings.register(this);registered=true;}
                settingsSocket.connectIfNeeded();
                // Healthy WebSocket: no repetitive HTTP requests. If push is
                // disconnected, reconcile mute/mode every 500 ms.
                boolean full=SystemClock.elapsedRealtime()-lastFullSync>=12000;
                if(!full&&settingsSocket.isSubscribed())return;
                if(full){
                    WakePilotSettings.Snapshot settings=WakePilotSettings.readFull(this);
                    lastFullSync=SystemClock.elapsedRealtime();
                    try{WakePilotSettings.report(this,status,muted?"muted":
                        nativeSession!=null?"assist":continuousRunning?"continuous":speech!=null?"wakeword":"idle");}
                    catch(Exception e){Log.w(TAG,"Noncritical telemetry failed",e);}
                    main.post(()->{
                        if(!enabled)return;
                        wordChoice=settings.word;
                        strictness=settings.strictness;
                        cooldownSeconds=settings.cooldownSeconds;
                        holdSeconds=settings.holdSeconds;
                        setVoiceSettings(settings.muted,settings.voiceMode);
                    });
                }else{
                    WakePilotSettings.MicState remote=WakePilotSettings.readMic(this);
                    main.post(()->{if(enabled)setVoiceSettings(remote.muted,remote.voiceMode);});
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

    private void setVoiceSettings(boolean shouldMute,String nextMode){
        String target=WakePilotSettings.modeFor(nextMode);
        boolean changed=!target.equals(voiceMode);
        if(changed){
            voiceMode=target;
            releaseRecognizer();
            stopContinuousMonitor();
            if(nativeSession!=null){nativeSession.close();nativeSession=null;}
            resetConversation();
        }
        setMuted(shouldMute);
        if(changed&&!shouldMute)startRecognition();
    }

    private void setMuted(boolean shouldMute){
        if(!enabled)return;
        if(shouldMute){
            manualPending=false;
            if(!muted||speech!=null||continuousRunning||followupPending||nativeSession!=null){
                muted=true;
                releaseRecognizer();
                stopContinuousMonitor();
                if(nativeSession!=null){nativeSession.close();nativeSession=null;}
                resetConversation();
                triggerGate.reset();
            }
            status="muted";
        }else{
            boolean wasMuted=muted;
            muted=false;
            if(nativeSession==null&&(wasMuted||(speech==null&&!continuousRunning)))startRecognition();
        }
    }

    private void startRecognition(){
        main.removeCallbacks(rearm);
        if(!enabled||loading||muted||nativeSession!=null||followupPending)return;
        if(manualPending){
            manualPending=false;
            beginNativeAssist("",false);
            return;
        }
        long remaining=holdUntil-SystemClock.elapsedRealtime();
        if(remaining>0){
            main.postDelayed(rearm,Math.max(500,remaining));
            return;
        }
        if("continuous".equals(voiceMode)){
            startContinuousMonitor();
            return;
        }
        if(model==null){status="model_missing";return;}
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
            NotificationManager manager=getSystemService(NotificationManager.class);
            if(manager!=null)manager.notify(43,notification());
        }catch(Exception e){
            Log.w(TAG,"Wakeword microphone unavailable",e);
            status="microphone_error: "+e.getClass().getSimpleName();
            releaseRecognizer();
            main.postDelayed(rearm,5000);
        }
    }

    /**
     * Low-cost native VAD. Unlike the old browser implementation it never
     * submits silence or a wakeword guess to GPU Whisper.
     * The microphone is released before the existing Assist capture begins.
     */
    private void startContinuousMonitor(){
        if(continuousRunning||muted||nativeSession!=null||!enabled||
                !"continuous".equals(voiceMode))return;
        if(continuousThread!=null&&continuousThread.isAlive()){
            main.postDelayed(rearm,350);
            return;
        }
        final long generation=++continuousGeneration;
        continuousRunning=true;
        status="listening: continuous";
        NotificationManager notifications=getSystemService(NotificationManager.class);
        if(notifications!=null)notifications.notify(43,notification());
        continuousThread=new Thread(()->{
            AudioRecord recorder=null;
            byte[] question=null;
            try{
                int min=AudioRecord.getMinBufferSize(16000,
                    AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT);
                if(min<=0)throw new IllegalStateException("microphone_unavailable");
                if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED)
                    throw new SecurityException("microphone_permission");
                recorder=new AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION,
                    16000,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT,
                    Math.max(4096,min*2));
                if(recorder.getState()!=AudioRecord.STATE_INITIALIZED)
                    throw new IllegalStateException("microphone_unavailable");
                continuousRecorder=recorder;
                recorder.startRecording();
                ContinuousSpeechTrigger gate=new ContinuousSpeechTrigger();
                NativeSpeechEndpoint endpoint=new NativeSpeechEndpoint(1700,8000);
                ArrayDeque<byte[]> preroll=new ArrayDeque<>(30);
                ByteArrayOutputStream pending=new ByteArrayOutputStream(32000);
                boolean started=false;
                short[] pcm=new short[320];
                while(continuousRunning&&continuousGeneration==generation&&enabled&&!muted&&
                      "continuous".equals(voiceMode)){
                    int count=recorder.read(pcm,0,pcm.length,AudioRecord.READ_BLOCKING);
                    if(count<0)throw new IllegalStateException("microphone_read_failed");
                    if(count!=320)continue;
                    byte[] frame=new byte[count*2];
                    for(int i=0;i<count;i++){
                        frame[i*2]=(byte)pcm[i];
                        frame[i*2+1]=(byte)(pcm[i]>>>8);
                    }
                    NativeSpeechEndpoint.Decision decision=endpoint.feed(pcm,count);
                    if(started){
                        pending.write(frame,0,frame.length);
                    }else{
                        preroll.addLast(frame);
                        if(preroll.size()>30)preroll.removeFirst();
                        if(gate.feed(pcm,count)){
                            started=true;
                            for(byte[] saved:preroll)pending.write(saved,0,saved.length);
                            preroll.clear();
                        }
                    }
                    if(decision==NativeSpeechEndpoint.Decision.EMPTY){
                        gate=new ContinuousSpeechTrigger();
                        endpoint=new NativeSpeechEndpoint(1700,8000);
                        preroll.clear();pending.reset();started=false;
                    }else if(decision==NativeSpeechEndpoint.Decision.END||
                            decision==NativeSpeechEndpoint.Decision.LIMIT){
                        if(started&&endpoint.hasSpeech()&&pending.size()>=16000)
                            question=pending.toByteArray();
                        break;
                    }
                }
            }catch(Exception e){
                if(continuousGeneration==generation&&enabled&&!muted){
                    Log.w(TAG,"Continuous native microphone unavailable",e);
                    main.post(()->{
                        if(enabled&&!muted&&"continuous".equals(voiceMode)){
                            status="microphone_error: "+e.getClass().getSimpleName();
                            main.postDelayed(rearm,5000);
                        }
                    });
                }
            }finally{
                if(recorder!=null){
                    try{recorder.stop();}catch(Exception ignored){}
                    recorder.release();
                }
                if(continuousGeneration==generation){
                    continuousRunning=false;
                    continuousRecorder=null;
                    final byte[] captured=question;
                    main.post(()->{
                        if(!enabled||muted||!"continuous".equals(voiceMode)||
                                nativeSession!=null||followupPending)return;
                        if(captured!=null){
                            resetConversation();
                            beginNativeAssist("",false,captured);
                        }else main.postDelayed(rearm,300);
                    });
                }
            }
        },"TAFA-ContinuousVAD");
        continuousThread.setDaemon(true);
        continuousThread.start();
    }

    private void stopContinuousMonitor(){
        continuousGeneration++;
        continuousRunning=false;
        AudioRecord recorder=continuousRecorder;
        if(recorder!=null)try{recorder.stop();}catch(Exception ignored){}
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
        lastHit=now;
        // Release the Vosk recorder before opening a separate native recorder.
        releaseRecognizer();
        status="detected: "+hit;
        resetConversation();
        // The native capture owns the complete request. Do not launch
        // a competing browser or old wake-event microphone path.
        beginNativeAssist(hit,false);
    }

    /** Launch only while the explicitly started foreground wake service runs. */
    private void beginNativeAssist(String hit,boolean nextQuestion){
        beginNativeAssist(hit,nextQuestion,null);
    }

    private void beginNativeAssist(String hit,boolean nextQuestion,byte[] capturedPcm){
        if(!enabled||muted||nativeSession!=null)return;
        if(nextQuestion){
            if(!FollowupPolicy.shouldContinue(true,completedFollowups,followupLimit())){
                endConversation();return;
            }
            completedFollowups++;
        }
        // Exclusive recorder ownership, including the follow-up after playback.
        releaseRecognizer();
        stopContinuousMonitor();
        var prefs=getSharedPreferences(MainActivity.PREF,0);
        // TAFA supports one speech mode: native microphone → HA Assist
        // and authenticated multiroom Bluetooth playback.
        status=nextQuestion?"native_followup":"native_connecting";
        final NativeAssistSession[] holder=new NativeAssistSession[1];
        NativeAssistSession session=new NativeAssistSession(this,hit,
            nextQuestion?nativeConversationId:"",
            prefs.getInt("native_pause_ms",1700),nextQuestion,
            new NativeAssistSession.Listener(){
                @Override public void state(String stage){
                    main.post(()->{
                        if(enabled&&nativeSession==holder[0]){
                            status="native_"+stage;
                            NotificationManager manager=getSystemService(NotificationManager.class);
                            if(manager!=null)manager.notify(43,notification());
                        }
                    });
                }
                @Override public void finished(boolean answered,String conversationId){
                    main.post(()->{
                        if(nativeSession!=holder[0])return;
                        nativeSession=null;
                        if(!enabled||muted)return;
                        if(answered){
                            nativeConversationId=conversationId;
                            status="native_answer_completed";
                        }else {
                            nativeConversationId="";
                            if(!status.startsWith("native_error:"))status="native_no_reply";
                        }
                        if(FollowupPolicy.shouldContinue(answered,completedFollowups,followupLimit())){
                            main.removeCallbacks(followup);
                            followupPending=true;
                            main.postDelayed(followup,850);
                        }else endConversation();
                    });
                }
            },capturedPcm);
        holder[0]=session;
        nativeSession=session;
        session.start();
    }

    private int followupLimit(){
        var prefs=getSharedPreferences(MainActivity.PREF,0);
        return FollowupPolicy.effectiveLimit(
            prefs.getInt(FollowupPolicy.LOCAL_LIMIT,0),
            prefs.getInt("native_followup_limit",-1));
    }

    private void resetConversation(){
        main.removeCallbacks(followup);
        main.removeCallbacks(rearm);
        followupPending=false;manualPending=false;
        completedFollowups=0;nativeConversationId="";holdUntil=0;
    }

    private void endConversation(){
        if(nativeSession!=null){
            NativeAssistSession old=nativeSession;nativeSession=null;old.close();
        }
        resetConversation();
        if(enabled&&!muted)main.postDelayed(rearm,"continuous".equals(voiceMode)?1500:650);
    }

    @Override public void onPartialResult(String text){candidate(text,"partial");}
    @Override public void onResult(String text){candidate(text,"text");}
    @Override public void onFinalResult(String text){candidate(text,"text");}
    @Override public void onError(Exception e){
        if(nativeSession!=null||followupPending||speech==null)return;
        Log.w(TAG,"Wakeword recognition error",e);
        if(enabled){
            status="recognition_error: "+e.getClass().getSimpleName();
            releaseRecognizer();
            main.postDelayed(rearm,5000);
        }
    }
    @Override public void onTimeout(){
        if(enabled&&nativeSession==null&&!followupPending&&speech!=null){
            releaseRecognizer();
            main.postDelayed(rearm,1000);
        }
    }

    @Override public void onDestroy(){
        enabled=false;running=false;muted=true;
        main.removeCallbacks(rearm);
        main.removeCallbacks(followup);
        if(nativeSession!=null){nativeSession.close();nativeSession=null;}
        if(settingsSocket!=null){settingsSocket.close();settingsSocket=null;}
        if(settingsExecutor!=null){settingsExecutor.shutdownNow();settingsExecutor=null;}
        releaseRecognizer();
        stopContinuousMonitor();
        if(model!=null){try{model.close();}catch(Exception ignored){}model=null;}
        if(status.startsWith("listening")||status.startsWith("detected")||status.startsWith("sent"))
            status="off";
        super.onDestroy();
    }
}
