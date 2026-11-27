package de.jarvis.audio;

import android.app.*;
import android.content.*;
import android.graphics.Bitmap;
import android.os.SystemClock;
import android.view.View;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;

/** Synthetic metadata only: never opens microphone, camera, HA or an audio output. */
final class NativeFlowSmoke {
    private static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static void main(Instrumentation i,Runnable action){
        AtomicReference<Throwable> error=new AtomicReference<>();
        i.runOnMainSync(()->{try{action.run();}catch(Throwable e){error.set(e);}});
        if(error.get()!=null)throw new AssertionError(error.get());
        i.waitForIdleSync();
    }
    private static void support(Instrumentation i,Activity activity){
        main(i,()->{
            activity.findViewById(R.id.nav_settings).performClick();
            View header=activity.findViewById(R.id.section_settings).findViewWithTag("settings_group_5");
            header.performClick();
            CheckBox enabled=activity.findViewById(R.id.flow_recording);
            enabled.setChecked(false);enabled.setChecked(true);
        });
    }
    private static void screenshot(Instrumentation i,Activity a,String name)throws Exception{
        main(i,()->{
            View view=a.findViewById(R.id.flow_summary);
            view.requestRectangleOnScreen(new android.graphics.Rect(0,0,view.getWidth(),Math.min(view.getHeight(),400)),true);
        });
        CountDownLatch frame=new CountDownLatch(1);
        i.runOnMainSync(()->{
            View root=a.getWindow().getDecorView();
            root.getViewTreeObserver().registerFrameCommitCallback(frame::countDown);root.invalidate();
        });
        check(frame.await(5,TimeUnit.SECONDS),"Diagnostic frame rendered");
        i.getUiAutomation().waitForIdle(100,5000);
        Bitmap bitmap=i.getUiAutomation().takeScreenshot();
        try(FileOutputStream out=new FileOutputStream(new File(a.getCacheDir(),name+".png"))){
            check(bitmap!=null,"Screenshot available");bitmap.compress(Bitmap.CompressFormat.PNG,100,out);
        }
    }
    static String run(Instrumentation i,String layout)throws Exception{
        Context ctx=i.getTargetContext();
        JSONObject timing=new JSONObject().put("TRIGGER",0).put("ASSIST_START",10).put("MIC_READY",100)
            .put("SPEECH_START",200).put("SPEECH_END",1200).put("CAPTURE_END",2900)
            .put("STT_END",3500).put("INTENT_START",3510).put("INTENT_END",4500)
            .put("TTS_START",4510).put("TTS_END",4700).put("FIRST_BYTE",5000)
            .put("FIRST_PCM",5100).put("OUTPUT_SUBMITTED",5500).put("OUTPUT_PROGRESS",6000)
            .put("PLAYBACK_END",8500).put("SESSION_END",8700);
        JSONObject facts=new JSONObject().put("OUTPUT","bluetooth").put("ENGINE","pcm").put("PAUSE_MS","1700");
        JSONObject success=new JSONObject().put("id","00000000-0000-0000-0000-000000000001")
            .put("kind","WAKEWORD").put("status","SUCCESS").put("started_wall_ms",System.currentTimeMillis())
            .put("events_ms",timing).put("facts",facts);
        JSONObject failure=new JSONObject().put("id","00000000-0000-0000-0000-000000000002")
            .put("kind","MANUAL").put("status","ERROR").put("started_wall_ms",System.currentTimeMillis())
            .put("events_ms",new JSONObject().put("TRIGGER",0)).put("facts",new JSONObject())
            .put("error","assist_stt_failed");
        String fixture=new JSONObject().put("runs",new JSONArray().put(success).put(failure)).toString();
        ctx.getSharedPreferences(MainActivity.PREF,0).edit().clear().putString("ui_language","de")
            .putString(VoiceDiagnostics.HISTORY,fixture).commit();
        Activity screen=i.startActivitySync(new Intent(ctx,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        try{
            support(i,screen);
            Activity de=screen;
            main(i,()->{
                TextView summary=de.findViewById(R.id.flow_summary);
                check(summary.isShown(),"Native diagnosis available in support group");
                check(summary.getText().toString().contains("4800,0 ms"),"DE speech-end latency is 4800 ms");
                check(summary.getText().toString().contains("n=1"),"Failed run excluded from success percentile");
                ((Spinner)de.findViewById(R.id.flow_runs)).setSelection(1);
            });
            main(i,()->check(((TextView)de.findViewById(R.id.flow_details)).getText().toString()
                .contains("Sprachende"),"Detailed latency breakdown"));
            screenshot(i,de,"native-flow-de-"+layout);
            main(i,()->de.findViewById(R.id.flow_copy).performClick());
            android.content.ClipboardManager clipboard=ctx.getSystemService(android.content.ClipboardManager.class);
            String exported=clipboard.getPrimaryClip().getItemAt(0).getText().toString();
            JSONObject json=new JSONObject(exported);
            check(json.getString("schema").equals("tafa-native-flow-v1"),"Structured diagnostic export");
            check(json.getJSONArray("runs").length()==2,"Success and error retained");
            check(!exported.contains("access_token")&&!exported.contains("https://")&&!exported.contains("stt_output"),
                "No token, URL or transcript in diagnostic export");
            Instrumentation.ActivityMonitor change=i.addMonitor(MainActivity.class.getName(),null,false);
            main(i,()->de.findViewById(R.id.language_en).performClick());
            screen=i.waitForMonitorWithTimeout(change,10000);i.removeMonitor(change);
            check(screen!=null,"English diagnostic activity recreated");
            support(i,screen);
            Activity en=screen;
            main(i,()->check(((TextView)en.findViewById(R.id.flow_summary)).getText().toString()
                .contains("4800.0 ms"),"EN metadata survives recreation"));
            screenshot(i,en,"native-flow-en-"+layout);
            VoiceTrace active=VoiceDiagnostics.begin(ctx,VoiceTrace.Kind.MANUAL);
            main(i,()->en.findViewById(R.id.flow_clear).performClick());
            active.mark(VoiceTrace.Point.OUTPUT_PROGRESS);
            VoiceDiagnostics.finish(active,VoiceTrace.Status.SUCCESS,"");
            check(new JSONObject(VoiceDiagnostics.export()).getJSONArray("runs").length()==0,
                "Clear retires active callbacks and cannot resurrect history");
            check(!AudioService.running&&!WakeWordService.running&&!CameraRelayService.running,
                "Diagnostics never starts a real capture or playback service");
            return "Native flow smoke passed: DE/EN, known phase durations, success/error history, cohorts, JSON copy, recreation and clear during an active measurement; synthetic metadata only.\n";
        }finally{Activity last=screen;if(last!=null)main(i,last::finish);}
    }
}
