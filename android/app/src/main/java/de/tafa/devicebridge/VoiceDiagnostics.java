package de.tafa.devicebridge;

import android.content.Context;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.SystemClock;
import org.json.*;
import java.util.*;

/** Local, bounded trace store. Only begin/end/background checkpoints touch disk, off the audio thread. */
final class VoiceDiagnostics {
    static final String ENABLED="voice_diagnostics_enabled",HISTORY="voice_diagnostics_history";
    private static final VoiceTrace.Store STORE=new VoiceTrace.Store(SystemClock::elapsedRealtimeNanos);
    private static Context app;
    private static Handler writer;
    private static final Runnable SAVE=()->{
        Context ctx=app;if(ctx==null)return;
        ctx.getSharedPreferences(MainActivity.PREF,0).edit().putString(HISTORY,export()).apply();
    };
    static synchronized void init(Context context){
        if(app!=null)return;
        app=context.getApplicationContext();
        HandlerThread thread=new HandlerThread("TAFA-Diagnostic-Metadata");thread.start();
        writer=new Handler(thread.getLooper());
        var prefs=app.getSharedPreferences(MainActivity.PREF,0);
        String saved=prefs.getString(HISTORY,"");
        if(saved.length()<=262144)try{
            JSONArray runs=new JSONObject(saved).getJSONArray("runs");
            List<VoiceTrace.Snapshot> restored=new ArrayList<>();
            for(int i=Math.max(0,runs.length()-20);i<runs.length();i++){
                JSONObject r=runs.getJSONObject(i);
                String id=r.getString("id");if(!id.matches("[a-f0-9-]{36}"))continue;
                EnumMap<VoiceTrace.Point,Long> points=new EnumMap<>(VoiceTrace.Point.class);
                JSONObject timing=r.getJSONObject("events_ms");
                for(VoiceTrace.Point p:VoiceTrace.Point.values()){
                    double ms=timing.optDouble(p.name(),-1);
                    if(Double.isFinite(ms)&&ms>=0&&ms<=600000)points.put(p,(long)(ms*1_000_000));
                }
                EnumMap<VoiceTrace.Fact,String> facts=new EnumMap<>(VoiceTrace.Fact.class);
                JSONObject values=r.getJSONObject("facts");
                for(VoiceTrace.Fact f:VoiceTrace.Fact.values()){
                    String v=values.optString(f.name(),"");
                    if(v.matches("[a-z0-9_-]{1,40}"))facts.put(f,v);
                }
                String error=r.optString("error","");
                if(!error.matches("[a-z0-9_]{0,90}"))error="error";
                restored.add(new VoiceTrace.Snapshot(id,VoiceTrace.Kind.valueOf(r.getString("kind")),
                    VoiceTrace.Status.valueOf(r.getString("status")),r.getLong("started_wall_ms"),error,points,facts));
            }
            STORE.restore(restored);
        }catch(Exception ignored){/* Corrupt/older history must never affect capture. */}
        STORE.enabled(prefs.getBoolean(ENABLED,true));
    }
    static VoiceTrace begin(Context ctx,VoiceTrace.Kind kind){
        init(ctx);VoiceTrace t=STORE.begin(kind,System.currentTimeMillis());
        t.fact(VoiceTrace.Fact.BUILD_CODE,BuildConfig.VERSION_CODE);
        if(STORE.enabled())checkpoint();return t;
    }
    static VoiceTrace.Playback playback(Context ctx,String job){init(ctx);return STORE.playback(job);}
    static void bind(VoiceTrace trace,String job){STORE.bind(trace,job);}
    static void finish(VoiceTrace trace,VoiceTrace.Status status,String error){
        trace.finish(status,error);if(STORE.enabled())checkpoint();
    }
    static void checkpoint(){
        Handler h=writer;if(h!=null){h.removeCallbacks(SAVE);h.postDelayed(SAVE,300);}
    }
    static void clear(){STORE.clear();checkpoint();}
    static boolean enabled(){return STORE.enabled();}
    static void enabled(Context ctx,boolean value){
        init(ctx);STORE.enabled(value);
        app.getSharedPreferences(MainActivity.PREF,0).edit().putBoolean(ENABLED,value).apply();checkpoint();
    }
    static List<VoiceTrace.Snapshot> snapshots(){return STORE.snapshots();}
    static String export(){
        try{
            JSONObject root=new JSONObject().put("schema","tafa-native-flow-v1").put("app_version",BuildConfig.VERSION_NAME)
                .put("clock","tablet_elapsed_realtime").put("max_runs",20)
                .put("timing_boundary","Android playback progress; acoustic Bluetooth latency is not measured")
                .put("server_phases","Assist event arrival on tablet, includes transport and server scheduling");
            JSONArray runs=new JSONArray();
            for(VoiceTrace.Snapshot s:STORE.snapshots()){
                JSONObject points=new JSONObject(),facts=new JSONObject();
                for(var e:s.points.entrySet())points.put(e.getKey().name(),e.getValue()/1_000_000.0);
                for(var e:s.facts.entrySet())facts.put(e.getKey().name(),e.getValue());
                runs.put(new JSONObject().put("id",s.id).put("kind",s.kind.name()).put("status",s.status.name())
                    .put("started_wall_ms",s.wallMs).put("error",s.error).put("events_ms",points).put("facts",facts));
            }
            return root.put("runs",runs).toString(2);
        }catch(JSONException impossible){return "{\"schema\":\"tafa-native-flow-v1\",\"runs\":[]}";}
    }
    private VoiceDiagnostics(){}
}
