package de.jarvis.audio;

import android.content.Context;
import org.json.JSONObject;
import java.util.concurrent.*;

/** Bounded latest-value metadata only, isolated from microphone and image uploads. */
final class ApproachReporter implements AutoCloseable {
    private final Context app;
    private final ExecutorService io=Executors.newSingleThreadExecutor(r->{
        Thread t=new Thread(r,"TAFA-Approach-Status");t.setDaemon(true);return t;
    });
    private final WakePhaseReporter queue;
    private boolean enrolled;
    ApproachReporter(Context ctx){
        app=ctx.getApplicationContext();
        queue=new WakePhaseReporter(io,json->{
            try{
                if(!enrolled){WakePilotSettings.register(app);enrolled=true;}
                WakePilotSettings.reportApproach(app,new JSONObject(json));
                CameraApproach.delivery="ok";
            }catch(Exception error){
                CameraApproach.delivery="error";
                // Registration retries are idempotent and never rename an existing tablet.
                enrolled=false;
            }
        });
    }
    void submit(Boolean near,Integer percent,int threshold){
        try{queue.submit(new JSONObject().put("near",near==null?JSONObject.NULL:near)
            .put("face_percent",percent==null?JSONObject.NULL:percent)
            .put("threshold_percent",threshold).toString());}
        catch(Exception ignored){}
    }
    @Override public void close(){
        submit(null,null,25);
        // Drain the final unavailable marker, without blocking the UI thread.
        io.shutdown();
    }
}
