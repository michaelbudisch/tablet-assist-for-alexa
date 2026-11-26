package de.jarvis.audio;

import android.Manifest;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.SystemClock;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;
import okio.ByteString;

/**
 * Direct foreground microphone → HA Assist → authenticated TAFA
 * Multiroom Android Bluetooth player.
 *
 * A session is started only after an explicitly enabled offline wake detector.
 * There is no always-on streaming, no recordings stored on disk and no token
 * in logs. There is no legacy browser-microphone fallback.
 */
final class NativeAssistSession extends WebSocketListener implements AutoCloseable {
    interface Listener {
        void state(String description);
        void finished(boolean answered, String conversationId);
    }

    static final int SAMPLE_RATE=16000,FRAME_SAMPLES=320;
    private static final int WS_PIPELINES=1,WS_RUN=2;
    private static final OkHttpClient HTTP=new OkHttpClient.Builder()
        .connectTimeout(8,TimeUnit.SECONDS).readTimeout(0,TimeUnit.SECONDS)
        .pingInterval(20,TimeUnit.SECONDS).build();
    private final Context context;
    private final Listener listener;
    private final String lastConversation, wakeWord;
    private final boolean followup;
    private final ExecutorService work=Executors.newSingleThreadExecutor(r->{
        Thread thread=new Thread(r,"TAFA-NativeAssist");
        thread.setDaemon(true);return thread;
    });
    private final AtomicBoolean ended=new AtomicBoolean(false);
    private final AtomicBoolean finished=new AtomicBoolean(false);
    private volatile boolean capture;
    private volatile AudioRecord recorder;
    private volatile WebSocket socket;
    private volatile int handler=-1;
    private volatile String ttsPath="",conversationId="";
    private volatile String haBase="",bearer="";
    private volatile boolean pipelineFailed=false;
    private volatile boolean authenticated=false;
    private volatile boolean gotSpeech=false;
    private volatile boolean didRunEnd=false;
    private volatile int pauseMs;

    NativeAssistSession(Context context,String wakeWord,String lastConversation,
                        int pauseMs,boolean followup,Listener listener){
        this.context=context.getApplicationContext();
        this.wakeWord=wakeWord==null?"":wakeWord;
        this.lastConversation=lastConversation==null?"":lastConversation;
        this.pauseMs=Math.max(900,Math.min(3200,pauseMs));
        this.followup=followup;
        this.listener=listener;
    }

    void start(){
        work.execute(()->{
            try{
                if(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                        !=PackageManager.PERMISSION_GRANTED)
                    throw new IOException("microphone_permission");
                if(!AudioService.running||!AudioService.haConnected)
                    throw new IOException("tablet_player_offline");
                SharedPreferences prefs=context.getSharedPreferences(MainActivity.PREF,0);
                haBase=HaAddress.validateStored(prefs.getString("base",""),
                    prefs.getString(MainActivity.HTTP_CONSENT,""));
                bearer=MainActivity.decrypt(prefs.getString("secret",""));
                JSONObject room=roomApi(new JSONObject().put("action","status"));
                if(!room.optBoolean("ready",false))
                    throw new IOException("room_player_not_ready");
                state("authenticating");
                String wsBase=(haBase.startsWith("https://")?"wss://":"ws://")
                    +haBase.substring(haBase.indexOf("://")+3);
                Request request=new Request.Builder().url(wsBase+"/api/websocket").build();
                if(!ended.get())socket=HTTP.newWebSocket(request,this);
            }catch(Exception e){fail(e.getMessage()==null?"connection_failed":e.getMessage());}
        });
    }

    private JSONObject roomApi(JSONObject body) throws Exception {
        if(ended.get())throw new IOException("cancelled");
        HttpURLConnection conn=(HttpURLConnection)new URL(haBase+"/api/tablet_assist_for_alexa/room_audio").openConnection();
        try{
            conn.setInstanceFollowRedirects(false);
            conn.setConnectTimeout(4500);conn.setReadTimeout(9500);
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Authorization","Bearer "+bearer);
            conn.setRequestProperty("Content-Type","application/json");
            byte[] payload=body.toString().getBytes(StandardCharsets.UTF_8);
            conn.setFixedLengthStreamingMode(payload.length);conn.setDoOutput(true);
            try(java.io.OutputStream out=conn.getOutputStream()){out.write(payload);}
            if(conn.getResponseCode()!=200)
                throw new IOException("room_http_"+conn.getResponseCode());
            try(java.io.InputStream in=conn.getInputStream()){
                ByteArrayOutputStream result=new ByteArrayOutputStream();
                byte[] buffer=new byte[1024];int n;
                while((n=in.read(buffer))!=-1){
                    if(result.size()+n>32768)throw new IOException("room_response_too_large");
                    result.write(buffer,0,n);
                }
                return new JSONObject(new String(result.toByteArray(),StandardCharsets.UTF_8));
            }
        }finally{conn.disconnect();}
    }

    private void state(String text){if(!ended.get())listener.state(text);}
    private void send(JSONObject obj) throws Exception {
        WebSocket ws=socket;
        if(ended.get()||ws==null||!ws.send(obj.toString()))throw new IOException("websocket_closed");
    }

    @Override public void onOpen(WebSocket ws,Response response){state("connected");}
    @Override public void onMessage(WebSocket ws,String message){
        if(ended.get())return;
        try{
            JSONObject packet=new JSONObject(message);
            String type=packet.optString("type","");
            if("auth_required".equals(type)){
                send(new JSONObject().put("type","auth").put("access_token",bearer));
            }else if("auth_ok".equals(type)){
                authenticated=true;
                send(new JSONObject().put("id",WS_PIPELINES)
                    .put("type","assist_pipeline/pipeline/list"));
            }else if("auth_invalid".equals(type)){
                fail("ha_auth_rejected");
            }else if("result".equals(type)){
                int id=packet.optInt("id",-1);
                if(!packet.optBoolean("success",false)){
                    fail(id==WS_PIPELINES?"pipeline_list_failed":"assist_pipeline_failed");
                }else if(id==WS_PIPELINES){
                    selectPipeline(packet.optJSONObject("result"));
                }
            }else if("event".equals(type)&&packet.optInt("id",-1)==WS_RUN){
                JSONObject event=packet.optJSONObject("event");
                if(event!=null)handleEvent(event);
            }
        }catch(Exception e){fail("assist_protocol_"+e.getClass().getSimpleName());}
    }

    private void selectPipeline(JSONObject list)throws Exception {
        if(list==null)throw new IOException("pipeline_list_empty");
        JSONArray items=list.optJSONArray("pipelines");
        if(items==null)throw new IOException("pipeline_list_empty");
        JSONObject chosen=null;
        for(int i=0;i<items.length();i++){
            JSONObject p=items.optJSONObject(i);
            if(p==null||p.optString("id").isEmpty()||p.isNull("stt_engine")||
                    p.isNull("tts_engine")||p.optString("stt_engine").isEmpty()||
                    p.optString("tts_engine").isEmpty())continue;
            if(p.optString("name").equalsIgnoreCase("TAFA Lokal")){chosen=p;break;}
        }
        if(chosen==null)throw new IOException("tafa_lokal_pipeline_missing");
        JSONObject input=new JSONObject().put("sample_rate",SAMPLE_RATE).put("no_vad",true);
        if(!wakeWord.isEmpty())input.put("wake_word_phrase",wakeWord);
        JSONObject cmd=new JSONObject().put("id",WS_RUN).put("type","assist_pipeline/run")
            .put("pipeline",chosen.getString("id")).put("start_stage","stt")
            .put("end_stage","tts").put("timeout",120).put("input",input);
        if(!lastConversation.isEmpty())cmd.put("conversation_id",lastConversation);
        send(cmd);
        state("waiting_for_stt");
    }

    private void handleEvent(JSONObject event) throws Exception {
        String type=event.optString("type");
        JSONObject data=event.optJSONObject("data");
        if(data==null)data=new JSONObject();
        if("run-start".equals(type)){
            JSONObject runner=data.optJSONObject("runner_data");
            handler=runner==null?-1:runner.optInt("stt_binary_handler_id",-1);
            if(handler<0||handler>255)throw new IOException("stt_handler_missing");
            state("starting_microphone");
        }else if("stt-start".equals(type)){
            if(handler<0)throw new IOException("stt_handler_missing");
            startCapture();
        }else if("stt-end".equals(type)){
            stopCapture(false);
            String words=data.optJSONObject("stt_output")==null?"":data.optJSONObject("stt_output").optString("text","");
            gotSpeech=!words.trim().isEmpty();
            state(gotSpeech?"processing":"no_speech");
        }else if("intent-start".equals(type)){
            state("thinking");
        }else if("intent-end".equals(type)){
            JSONObject intent=data.optJSONObject("intent_output");
            if(intent!=null)conversationId=intent.optString("conversation_id",lastConversation);
        }else if("tts-start".equals(type)){
            state("generating_voice");
        }else if("tts-end".equals(type)){
            JSONObject output=data.optJSONObject("tts_output");
            if(output!=null){
                String url=output.optString("url","");
                if(!url.isEmpty())ttsPath=audioPath(url);
            }
        }else if("error".equals(type)){
            pipelineFailed=true;
            stopCapture(false);
            fail("assist_"+data.optString("code","error").replaceAll("[^a-zA-Z0-9_-]",""));
        }else if("run-end".equals(type)){
            didRunEnd=true;
            stopCapture(false);
            if(!pipelineFailed){
                if(!gotSpeech||ttsPath.isEmpty())finish(false);
                else work.execute(this::submitAndAwaitPlayback);
            }
        }
    }

    /** Accept only a same-instance HA TTS proxy path (no foreign URL/host). */
    private String audioPath(String raw)throws Exception {
        URL expected=new URL(haBase),actual=new URL(expected,raw);
        if(!expected.getProtocol().equals(actual.getProtocol())||
           !expected.getHost().equalsIgnoreCase(actual.getHost())||
           expected.getPort()!=actual.getPort()||
           actual.getQuery()!=null||actual.getRef()!=null||
           !actual.getPath().matches("/api/tts_proxy/[A-Za-z0-9_.~-]{1,200}"))
            throw new IOException("untrusted_tts_audio_url");
        return actual.getPath();
    }

    private void startCapture(){
        if(capture||ended.get())return;
        capture=true;
        state("listening");
        work.execute(()->{
            AudioRecord audio=null;
            boolean sentEnd=false;
            try{
                int min=AudioRecord.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT);
                if(min<=0)throw new IOException("microphone_unavailable");
                // Recheck the revocable Android runtime permission immediately
                // before opening the microphone, not just at session start.
                if(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                        !=PackageManager.PERMISSION_GRANTED)
                    throw new IOException("microphone_permission_revoked");
                audio=new AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION,
                    SAMPLE_RATE,AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,Math.max(4096,min*2));
                if(audio.getState()!=AudioRecord.STATE_INITIALIZED)
                    throw new IOException("microphone_unavailable");
                recorder=audio;
                // Vosk has already closed its own recorder before this point.
                audio.startRecording();
                NativeSpeechEndpoint endpoint=new NativeSpeechEndpoint(pauseMs,followup?6500:8000);
                int gain=context.getSharedPreferences(MainActivity.PREF,0).getInt("mic_gain",100);
                gain=Math.max(50,Math.min(200,gain));
                short[] pcm=new short[FRAME_SAMPLES];
                while(capture&&!ended.get()){
                    int n=audio.read(pcm,0,pcm.length,AudioRecord.READ_BLOCKING);
                    if(n<0)throw new IOException("microphone_read_failed");
                    if(n!=FRAME_SAMPLES)continue;
                    // Digital microphone gain, applied to STT and silence detection.
                    if(gain!=100)for(int i=0;i<n;i++){
                        int sample=pcm[i]*gain/100;
                        pcm[i]=(short)Math.max(-32768,Math.min(32767,sample));
                    }
                    byte[] data=new byte[1+n*2];
                    data[0]=(byte)(handler&0xff);
                    for(int i=0;i<n;i++){
                        data[1+i*2]=(byte)pcm[i];
                        data[2+i*2]=(byte)(pcm[i]>>>8);
                    }
                    WebSocket ws=socket;
                    if(ws==null||!ws.send(ByteString.of(data)))throw new IOException("audio_socket_closed");
                    NativeSpeechEndpoint.Decision choice=endpoint.feed(pcm,n);
                    if(choice!=NativeSpeechEndpoint.Decision.CONTINUE){
                        capture=false;
                        ws.send(ByteString.of(new byte[]{(byte)(handler&0xff)}));
                        sentEnd=true;
                        state(choice==NativeSpeechEndpoint.Decision.EMPTY?
                            "no_speech":"transcribing");
                        break;
                    }
                }
            }catch(Exception error){
                if(capture&&!ended.get())fail("audio_"+error.getClass().getSimpleName());
            }finally{
                capture=false;
                if(audio!=null){
                    try{audio.stop();}catch(Exception ignored){}
                    audio.release();
                }
                recorder=null;
            }
        });
    }

    private void stopCapture(boolean signalEnd){
        if(!capture)return;
        capture=false;
        AudioRecord audio=recorder;
        if(audio!=null)try{audio.stop();}catch(Exception ignored){}
        if(signalEnd&&handler>=0&&socket!=null)
            socket.send(ByteString.of(new byte[]{(byte)(handler&0xff)}));
    }

    private void submitAndAwaitPlayback(){
        String jobId="";
        try{
            if(ended.get())return;
            if(!AudioService.running)throw new IOException("tablet_player_stopped");
            state("sending_audio");
            JSONObject job=roomApi(new JSONObject().put("action","submit").put("path",ttsPath));
            jobId=job.optString("id","");
            if(!job.optBoolean("accepted")||!jobId.matches("[a-f0-9]{32}"))
                throw new IOException("audio_submit_rejected");
            state("waiting_for_playback");
            long deadline=SystemClock.elapsedRealtime()+90000;
            while(!ended.get()&&SystemClock.elapsedRealtime()<deadline){
                JSONObject progress=roomApi(new JSONObject().put("action","status").put("id",jobId));
                String stage=progress.optString("stage","unknown");
                if("done".equals(stage)){finish(true);return;}
                if("buffering".equals(stage)||"playing".equals(stage))state(stage);
                if("error".equals(stage)||"cancelled".equals(stage)||
                        "unknown".equals(stage)||"expired".equals(stage))
                    throw new IOException("playback_"+stage);
                Thread.sleep(650);
            }
            throw new IOException("playback_timeout");
        }catch(Exception e){
            if(!ended.get())fail(e.getMessage()==null?"playback_failed":e.getMessage());
            if(!jobId.isEmpty())try{
                roomApi(new JSONObject().put("action","cancel").put("id",jobId));
            }catch(Exception ignored){}
        }
    }

    private void fail(String reason){state("error:"+reason);finish(false);}
    private void finish(boolean answered){
        if(!finished.compareAndSet(false,true))return;
        ended.set(true);
        stopCapture(false);
        WebSocket ws=socket;
        if(ws!=null)ws.close(1000,"finished");
        work.shutdownNow();
        listener.finished(answered,answered?conversationId:"");
    }

    @Override public void onFailure(WebSocket ws,Throwable reason,Response response){
        if(!ended.get())fail("websocket_disconnected");
    }
    @Override public void onClosing(WebSocket ws,int code,String reason){
        if(!ended.get()&&!didRunEnd)fail("websocket_closed");
    }
    @Override public void onClosed(WebSocket ws,int code,String reason){
        if(!ended.get()&&!didRunEnd)fail("websocket_closed");
    }
    @Override public void close(){
        ended.set(true);
        stopCapture(false);
        WebSocket ws=socket;if(ws!=null)ws.close(1000,"stopped");
        work.shutdownNow();
    }
}
