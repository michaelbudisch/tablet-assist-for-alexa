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
import java.util.concurrent.ExecutorService;
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
    private volatile boolean enabled=false;
    private boolean loading=false;
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
    private ExecutorService phaseExecutor;
    private WakePhaseReporter phaseReporter;
    private NativeSettingsSocket settingsSocket;
    private volatile long lastFullSync=0;
    private volatile int lastAckRevision=-1;
    private volatile String lastAckChannel="";
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
        if(FollowupPolicy.shouldContinue(true,true,completedFollowups,followupLimit()))
            beginNativeAssist("",true);
        else endConversation();
    };

    @Override public IBinder onBind(Intent intent){return null;}

    @Override public void onCreate(){
        super.onCreate();
        VoiceDiagnostics.init(this);
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel(CHANNEL,
            getString(R.string.wake_title),NotificationManager.IMPORTANCE_LOW));
    }

    // Voice phase changes are sent immediately without blocking any audio callback.
    // This is independent of the 12-second configuration reconciliation.
    private void updateStatus(String next){
        if(next==null||next.equals(status))return;
        status=next;
        publishCurrentStatus();
    }

    private void publishCurrentStatus(){
        WakePhaseReporter reporter=phaseReporter;
        if(enabled&&reporter!=null)reporter.submit(status);
    }

    private void publishPhase(String phase){
        if(!enabled)return;
        String microphone;
        if(muted)microphone="muted";
        else if(phase.startsWith("detected:")||
            (phase.startsWith("native_")&&!phase.equals("native_answer_completed")
            &&!phase.equals("native_no_reply")&&!phase.startsWith("native_error:")))
            microphone="assist";
        else if("listening: continuous".equals(phase))microphone="continuous";
        else if(phase.startsWith("listening:"))microphone="wakeword";
        else microphone="idle";
        try{WakePilotSettings.report(this,phase,microphone,controlChannel());}
        catch(Exception e){Log.w(TAG,"Live voice phase report unavailable",e);}
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
            updateStatus("permission_required");stopSelf();return START_NOT_STICKY;
        }
        if(!WakeModelInstaller.installed(this)&&
                !"continuous".equals(getSharedPreferences(MainActivity.PREF,0)
                    .getString("native_voice_mode","wake"))){
            updateStatus("model_missing");stopSelf();return START_NOT_STICKY;
        }
        voiceMode=WakePilotSettings.modeFor(getSharedPreferences(MainActivity.PREF,0)
            .getString("native_voice_mode","wake"));
        wordChoice=getSharedPreferences(MainActivity.PREF,0).getString("wake_choice","hey_jarvis");
        try{
            if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.Q)
                startForeground(43,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE);
            else startForeground(43,notification());
        }catch(Exception e){
            updateStatus("foreground_error: "+e.getClass().getSimpleName());
            stopSelf();return START_NOT_STICKY;
        }
        enabled=true;running=true;muted=true;
        phaseExecutor=Executors.newSingleThreadExecutor(r->{
            Thread thread=new Thread(r,"TAFA-LiveVoicePhase");
            thread.setDaemon(true);return thread;
        });
        phaseReporter=new WakePhaseReporter(phaseExecutor,this::publishPhase);
        updateStatus("loading");
        loading=false;
        startSettingsSync();
        startRecognition();
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
                final int revision=update.optInt("revision",0);
                final String nextWord=WakePilotSettings.choiceFor(
                    update.optString("word","Hey Jarvis"));
                final int nextStrict=WakePilotSettings.clamp(update.optInt("strict",1),1,3);
                final int nextCooldown=WakePilotSettings.clamp(update.optInt("cooldown",12),3,30);
                final int nextHold=WakePilotSettings.clamp(update.optInt("hold",50),10,90);
                final int nextPause=WakePilotSettings.clamp(update.optInt("pause_ms",1700),900,3200);
                final int nextGain=WakePilotSettings.clamp(update.optInt("mic_gain",100),50,200);
                if(nextFollowups < -1 || nextFollowups > 100)return;
                main.post(()->{
                    if(!enabled)return;
                    AudioOutputMode.applyRemote(WakeWordService.this,update.optString(AudioOutputMode.KEY,""));
                     boolean newWord=!wordChoice.equals(nextWord);
                    wordChoice=nextWord;
                    strictness=nextStrict;
                    cooldownSeconds=nextCooldown;
                    holdSeconds=nextHold;
                    getSharedPreferences(MainActivity.PREF,0).edit()
                        .putInt("native_followup_limit",nextFollowups)
                        .putString("wake_choice",nextWord)
                        .putInt("wake_strict",nextStrict)
                        .putInt("wake_cooldown",nextCooldown)
                        .putInt("wake_hold",nextHold)
                        .putInt("native_pause_ms",nextPause)
                        .putInt("mic_gain",nextGain)
                        .putBoolean("wake_muted",nextMuted)
                        .putString("native_voice_mode",nextMode).apply();
                    setVoiceSettings(nextMuted,nextMode);
                    acknowledgeSettings(revision,"websocket");
                    if(newWord&&!muted&&"wake".equals(voiceMode)&&nativeSession==null){
                        releaseRecognizer();
                        startRecognition();
                    }
                    // Acknowledge applied changes promptly in HA telemetry so
                    // the Control Center doesn't display a stale microphone state.
                    publishCurrentStatus();
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
                    // Periodic recovery uses the same ordered queue: no stale
                    // heartbeat may overwrite a newer live phase.
                    publishCurrentStatus();
                    main.post(()->{
                        if(!enabled)return;
                        wordChoice=settings.word;
                        strictness=settings.strictness;
                        cooldownSeconds=settings.cooldownSeconds;
                        holdSeconds=settings.holdSeconds;
                        setVoiceSettings(settings.muted,settings.voiceMode);
                        acknowledgeSettings(settings.revision,controlChannel());
                    });
                }else{
                    WakePilotSettings.MicState remote=WakePilotSettings.readMic(this);
                    main.post(()->{
                        if(!enabled)return;
                        setVoiceSettings(remote.muted,remote.voiceMode);
                        acknowledgeSettings(remote.revision,"poll");
                    });
                }
            }catch(Exception e){
                // Fail closed: if HA is unreachable, the remote mute switch cannot
                // be honored reliably, so release the microphone.
                main.post(()->{
                    if(!enabled)return;
                    setMuted(true);
                    updateStatus("ha_settings_error: "+e.getClass().getSimpleName());
                });
            }
        },0,SYNC_INTERVAL_MS,TimeUnit.MILLISECONDS);
    }

    private String controlChannel(){
        return settingsSocket!=null&&settingsSocket.isSubscribed()?"websocket":"poll";
    }

    /** Send ACK only after the main-thread control state has been applied. */
    private void acknowledgeSettings(int revision,String channel){
        if(revision<0||!enabled)return;
        if(revision==lastAckRevision&&channel.equals(lastAckChannel))return;
        ScheduledExecutorService worker=settingsExecutor;
        if(worker==null||worker.isShutdown())return;
        worker.execute(()->{
            if(!enabled)return;
            try{
                if(WakePilotSettings.acknowledge(this,revision,channel)){
                    lastAckRevision=revision;
                    lastAckChannel=channel;
                }
            }catch(Exception e){Log.w(TAG,"Control ACK deferred to next sync");}
        });
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
            updateStatus("muted");
        }else{
            boolean wasMuted=muted;
            muted=false;
            if(nativeSession==null&&(wasMuted||(speech==null&&!continuousRunning)))startRecognition();
        }
    }

    private void loadWakeModel(){
        if(model!=null||loading)return;
        if(!WakeModelInstaller.installed(this)){updateStatus("model_missing");return;}
        loading=true;
        new Thread(()->{
            try{
                Model loaded=new Model(WakeModelInstaller.modelDir(this).getAbsolutePath());
                main.post(()->{
                    loading=false;
                    if(!enabled){loaded.close();return;}
                    model=loaded;
                    startRecognition();
                });
            }catch(Exception error){
                main.post(()->{
                    loading=false;
                    updateStatus("model_error: "+error.getClass().getSimpleName());
                });
            }
        },"TAFA-WakeModel").start();
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
        if(model==null){loadWakeModel();return;}
        if(speech!=null)return;
        wordChoice=getSharedPreferences(MainActivity.PREF,0).getString("wake_choice","hey_jarvis");
        try{
            String grammar="["+ 
                "\"hey jarvis\",\"jarvis\",\"alexa\",\"hey jarwis\",\"jarwis\","+
                "\"hei jarvis\",\"[unk]\"]";
            recognizer=new Recognizer(model,16000f,grammar);
            speech=new SpeechService(recognizer,16000f);
            if(!speech.startListening(this))throw new IllegalStateException("Recorder not started");
            updateStatus("listening: "+wordChoice);
            NotificationManager manager=getSystemService(NotificationManager.class);
            if(manager!=null)manager.notify(43,notification());
        }catch(Exception e){
            Log.w(TAG,"Wakeword microphone unavailable",e);
            updateStatus("microphone_error: "+e.getClass().getSimpleName());
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
        final int capturePauseMs=Math.max(900,Math.min(3200,
            getSharedPreferences(MainActivity.PREF,0).getInt("native_pause_ms",1700)));
        final long generation=++continuousGeneration;
        continuousRunning=true;
        updateStatus("listening: continuous");
        NotificationManager notifications=getSystemService(NotificationManager.class);
        if(notifications!=null)notifications.notify(43,notification());
        continuousThread=new Thread(()->{
            AudioRecord recorder=null;
            byte[] question=null;
            VoiceTrace measurement=null;
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
                NativeSpeechEndpoint endpoint=new NativeSpeechEndpoint(capturePauseMs,8000);
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
                            measurement=VoiceDiagnostics.begin(this,VoiceTrace.Kind.CONTINUOUS);
                            measurement.mark(VoiceTrace.Point.SPEECH_START);
                            measurement.fact(VoiceTrace.Fact.MIC_PREOPENED,1);
                            measurement.fact(VoiceTrace.Fact.PAUSE_MS,capturePauseMs);
                            measurement.fact(VoiceTrace.Fact.MIC_GAIN,100);
                            for(byte[] saved:preroll)pending.write(saved,0,saved.length);
                            preroll.clear();
                        }
                    }
                    if(measurement!=null&&endpoint.voicedFrame())measurement.mark(VoiceTrace.Point.SPEECH_END);
                    if(decision==NativeSpeechEndpoint.Decision.EMPTY){
                        gate=new ContinuousSpeechTrigger();
                        endpoint=new NativeSpeechEndpoint(capturePauseMs,8000);
                        preroll.clear();pending.reset();started=false;
                    }else if(decision==NativeSpeechEndpoint.Decision.END||
                            decision==NativeSpeechEndpoint.Decision.LIMIT){
                        if(measurement!=null){
                            measurement.mark(VoiceTrace.Point.CAPTURE_END);
                            measurement.fact(VoiceTrace.Fact.CAPTURED_MS,pending.size()/32L);
                        }
                        if(started&&endpoint.hasSpeech()&&pending.size()>=16000)
                            question=pending.toByteArray();
                        break;
                    }
                }
            }catch(Exception e){
                if(continuousGeneration==generation&&enabled&&!muted){
                    if(measurement!=null)VoiceDiagnostics.finish(measurement,VoiceTrace.Status.ERROR,"microphone_capture_failed");
                    Log.w(TAG,"Continuous native microphone unavailable",e);
                    main.post(()->{
                        if(enabled&&!muted&&"continuous".equals(voiceMode)){
                            updateStatus("microphone_error: "+e.getClass().getSimpleName());
                            main.postDelayed(rearm,5000);
                        }
                    });
                }
            }finally{
                if(recorder!=null){
                    try{recorder.stop();}catch(Exception ignored){}
                    recorder.release();
                }
                if(continuousGeneration!=generation&&measurement!=null)
                    VoiceDiagnostics.finish(measurement,VoiceTrace.Status.CANCELLED,"");
                if(continuousGeneration==generation){
                    continuousRunning=false;
                    continuousRecorder=null;
                    final byte[] captured=question;
                    final VoiceTrace measured=measurement;
                    main.post(()->{
                        if(!enabled||muted||!"continuous".equals(voiceMode)||
                                nativeSession!=null||followupPending){
                            if(measured!=null)VoiceDiagnostics.finish(measured,VoiceTrace.Status.CANCELLED,"");
                            return;
                        }
                        if(captured!=null){
                            resetConversation();
                            beginNativeAssist("",false,captured,measured);
                        }else {
                            if(measured!=null)VoiceDiagnostics.finish(measured,VoiceTrace.Status.NO_REPLY,"");
                            main.postDelayed(rearm,300);
                        }
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
        VoiceTrace measurement=VoiceDiagnostics.begin(this,VoiceTrace.Kind.WAKEWORD);
        // Release the Vosk recorder before opening a separate native recorder.
        releaseRecognizer();
        updateStatus("detected: "+hit);
        resetConversation();
        // The native capture owns the complete request. Do not launch
        // a competing browser or old wake-event microphone path.
        beginNativeAssist(hit,false,null,measurement);
    }

    /** Launch only while the explicitly started foreground wake service runs. */
    private void beginNativeAssist(String hit,boolean nextQuestion){
        beginNativeAssist(hit,nextQuestion,null);
    }

    private void beginNativeAssist(String hit,boolean nextQuestion,byte[] capturedPcm){
        beginNativeAssist(hit,nextQuestion,capturedPcm,null);
    }
    private void beginNativeAssist(String hit,boolean nextQuestion,byte[] capturedPcm,VoiceTrace measurement){
        if(!enabled||muted||nativeSession!=null){
            if(measurement!=null)VoiceDiagnostics.finish(measurement,VoiceTrace.Status.CANCELLED,"");
            return;
        }
        if(nextQuestion){
            if(!FollowupPolicy.shouldContinue(true,true,completedFollowups,followupLimit())){
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
        updateStatus(nextQuestion?"native_followup":"native_connecting");
        final NativeAssistSession[] holder=new NativeAssistSession[1];
        NativeAssistSession session=new NativeAssistSession(this,hit,
            nextQuestion?nativeConversationId:"",
            prefs.getInt("native_pause_ms",1700),nextQuestion,
            new NativeAssistSession.Listener(){
                @Override public void state(String stage){
                    main.post(()->{
                        if(enabled&&nativeSession==holder[0]){
                            updateStatus("native_"+stage);
                            NotificationManager manager=getSystemService(NotificationManager.class);
                            if(manager!=null)manager.notify(43,notification());
                        }
                    });
                }
                @Override public void finished(boolean answered,String conversationId,boolean invited){
                    main.post(()->{
                        if(nativeSession!=holder[0])return;
                        nativeSession=null;
                        if(!enabled||muted)return;
                        if(answered){
                            nativeConversationId=conversationId;
                            updateStatus("native_answer_completed");
                        }else {
                            nativeConversationId="";
                            if(!status.startsWith("native_error:"))updateStatus("native_no_reply");
                        }
                        if(FollowupPolicy.shouldContinue(answered,invited,completedFollowups,followupLimit())){
                            main.removeCallbacks(followup);
                            followupPending=true;
                            main.postDelayed(followup,850);
                        }else endConversation();
                    });
                }
            },capturedPcm,measurement);
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
            updateStatus("recognition_error: "+e.getClass().getSimpleName());
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
        if(phaseReporter!=null){phaseReporter.close();phaseReporter=null;}
        if(phaseExecutor!=null){phaseExecutor.shutdownNow();phaseExecutor=null;}
        releaseRecognizer();
        stopContinuousMonitor();
        if(model!=null){try{model.close();}catch(Exception ignored){}model=null;}
        if(status.startsWith("listening")||status.startsWith("detected")||status.startsWith("sent"))
            status="off";
        super.onDestroy();
    }
}
