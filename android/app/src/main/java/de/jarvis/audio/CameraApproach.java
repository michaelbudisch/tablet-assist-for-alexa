package de.jarvis.audio;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Rect;
import android.media.Image;
import android.os.SystemClock;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.face.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Optional on-device face boxes; never identifies people or sends analysis images. */
final class CameraApproach implements AutoCloseable {
    static final String ENABLED="camera_approach",THRESHOLD="approach_threshold",HOLD="approach_hold";
    static volatile String status="off",delivery="off";
    static volatile int facePercent;
    private final Context app;
    private final SharedPreferences prefs;
    private final AtomicBoolean busy=new AtomicBoolean();
    private final ApproachState state=new ApproachState();
    private FaceDetector detector;
    private byte[] pixels;
    private ApproachReporter reporter;
    private volatile boolean closed;
    private long nextAt;
    private Boolean previous;
    private long lastReported=-1;
    private int lastReportedThreshold=-1;
    private int previousThreshold=-1;
    CameraApproach(Context ctx){
        app=ctx.getApplicationContext();prefs=app.getSharedPreferences(MainActivity.PREF,0);
        status="off";facePercent=0;delivery="off";
    }
    /** Called by the existing Camera2 drain thread. Image bytes are copied only at the bounded analysis rate. */
    synchronized boolean accept(Image image,int sensor,boolean front){
        if(closed)return false;
        if(!prefs.getBoolean(ENABLED,false)){
            if(!"off".equals(status)){state.clear();emit(null,null,25);status="off";facePercent=0;}
            return false;
        }
        long now=SystemClock.elapsedRealtime();
        if(now<nextAt||busy.get())return false;
        nextAt=now+750;
        int threshold=Math.max(15,Math.min(60,prefs.getInt(THRESHOLD,25)));
        int hold=Math.max(2,Math.min(10,prefs.getInt(HOLD,4)));
        if(!front){state.clear();status="front_required";emit(null,null,threshold);return false;}
        try{
            if(detector==null)detector=FaceDetection.getClient(new FaceDetectorOptions.Builder()
                .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_FAST)
                .setLandmarkMode(FaceDetectorOptions.LANDMARK_MODE_NONE)
                .setClassificationMode(FaceDetectorOptions.CLASSIFICATION_MODE_NONE)
                .setMinFaceSize(.12f).build());
            if(previousThreshold!=threshold){state.clear();previousThreshold=threshold;}
            android.view.Display display=app.getSystemService(android.hardware.display.DisplayManager.class)
                .getDisplay(android.view.Display.DEFAULT_DISPLAY);
            int rotation=ApproachState.rotation(sensor,display==null?0:display.getRotation()*90,front);
            boolean swap=rotation%180!=0;
            int width=swap?image.getHeight():image.getWidth(),height=swap?image.getWidth():image.getHeight();
            busy.set(true);status="checking";
            pixels=ApproachYuv.copy(image,pixels);
            detector.process(InputImage.fromByteArray(pixels,image.getWidth(),image.getHeight(),rotation,InputImage.IMAGE_FORMAT_NV21))
                .addOnSuccessListener(Runnable::run,faces->{
                    synchronized(CameraApproach.this){
                        if(closed||!prefs.getBoolean(ENABLED,false))return;
                        double largest=0;
                        for(Face face:faces){Rect b=face.getBoundingBox();
                            largest=Math.max(largest,ApproachState.facePercent(width,height,b.left,b.top,b.right,b.bottom));}
                        facePercent=(int)Math.round(largest);
                        boolean near=state.update(SystemClock.elapsedRealtime(),largest,threshold,hold);
                        status=near?"near":"far";emit(near,facePercent,threshold);
                    }
                }).addOnFailureListener(Runnable::run,error->{
                    synchronized(CameraApproach.this){
                        if(!closed){state.clear();status="error";facePercent=0;emit(null,null,threshold);}
                    }
                }).addOnCompleteListener(Runnable::run,task->{
                    busy.set(false);
                });
            // All bytes are now private; Camera2 keeps no acquired analysis image.
            return false;
        }catch(RuntimeException error){
            busy.set(false);state.clear();status="error";emit(null,null,threshold);return false;
        }
    }
    private void emit(Boolean near,Integer percent,int threshold){
        long now=SystemClock.elapsedRealtime();
        if(lastReported>=0&&java.util.Objects.equals(previous,near)&&lastReportedThreshold==threshold&&now-lastReported<3000)return;
        lastReported=now;lastReportedThreshold=threshold;
        if(reporter==null)reporter=new ApproachReporter(app);
        reporter.submit(near,percent,threshold);previous=near;
    }
    @Override public synchronized void close(){
        closed=true;state.clear();status="off";facePercent=0;
        if(detector!=null)detector.close();
        if(reporter!=null)reporter.close();
    }
}
