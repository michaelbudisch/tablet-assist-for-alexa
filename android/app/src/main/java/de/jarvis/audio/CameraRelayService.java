package de.jarvis.audio;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.hardware.display.DisplayManager;
import android.os.*;
import android.util.Size;
import android.view.Display;
import java.util.UUID;
import java.util.concurrent.*;

/** Explicit-start camera foreground service; one capture/upload at a time, no disk or offline queue. */
public class CameraRelayService extends Service {
    static volatile boolean running;
    static volatile String status="camera_relay_off";
    static volatile long sent,lastSent;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private final FrameMotion motion=new FrameMotion();
    private CameraPreviewController camera;
    private CameraUploadClient upload;
    private PowerManager.WakeLock wake;
    private volatile boolean active;
    private boolean motionEnabled;
    private int retries;
    private String lens;
    private long captureStarted;
    private final Runnable capture=()->{
        if(active&&camera!=null){
            captureStarted=SystemClock.elapsedRealtime();
            Display display=getSystemService(DisplayManager.class).getDisplay(Display.DEFAULT_DISPLAY);
            camera.capture(display==null?0:display.getRotation()*90);
        }
    };
    private final Runnable renewWake=new Runnable(){public void run(){
        if(active){if(wake.isHeld())wake.release();wake.acquire(10*60*1000L);main.postDelayed(this,5*60*1000L);}
    }};
    @Override public IBinder onBind(Intent intent){return null;}
    @Override public void onCreate(){super.onCreate();notification();}
    private void notification(){
        Context localized=AppLanguage.wrap(this);
        NotificationManager notifications=getSystemService(NotificationManager.class);
        notifications.createNotificationChannel(new NotificationChannel("camera",localized.getString(R.string.camera_notification_channel),NotificationManager.IMPORTANCE_LOW));
        PendingIntent open=PendingIntent.getActivity(this,50,new Intent(this,CameraActivity.class),PendingIntent.FLAG_IMMUTABLE);
        PendingIntent stop=PendingIntent.getService(this,51,new Intent(this,CameraRelayService.class).setAction("stop"),PendingIntent.FLAG_IMMUTABLE);
        Notification notification=new Notification.Builder(this,"camera").setContentTitle(localized.getString(R.string.camera_relay_title))
                .setContentText(localized.getString(R.string.camera_notification_text)).setSmallIcon(R.drawable.ic_notification)
                .setContentIntent(open).addAction(new Notification.Action.Builder(null,localized.getString(R.string.camera_relay_stop),stop).build()).setOngoing(true).build();
        if(Build.VERSION.SDK_INT>=30)startForeground(43,notification,ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA);else startForeground(43,notification);
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        if(intent==null||"stop".equals(intent.getAction())){stopSelf();return START_NOT_STICKY;}
        if("refresh_ui".equals(intent.getAction())){notification();return START_NOT_STICKY;}
        if(active)return START_NOT_STICKY;
        try{
            var prefs=getSharedPreferences(MainActivity.PREF,0);
            String device=prefs.getString("camera_device_id","");
            if(!device.matches("[a-f0-9]{32}")){device=UUID.randomUUID().toString().replace("-","");prefs.edit().putString("camera_device_id",device).apply();}
            upload=new CameraUploadClient(prefs.getString("base",""),MainActivity.decrypt(prefs.getString("secret","")),prefs.getString(MainActivity.HTTP_CONSENT,""),device,prefs.getBoolean("room_audio_enabled",false));
            lens=prefs.getString("camera_lens_id","");
            if(lens.isEmpty())lens=CameraPreviewController.lenses(this).get(0).id;
            motionEnabled=prefs.getBoolean("camera_motion",false);
            wake=getSystemService(PowerManager.class).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"EchoRelay:Camera");
            active=true;running=true;sent=0;lastSent=0;status="camera_relay_starting";renewWake.run();
            main.postDelayed(this::open,500);
        }catch(Exception error){status="camera_setup_required";stopSelf();}
        return START_NOT_STICKY;
    }
    private void open(){
        if(!active)return;
        camera=new CameraPreviewController(this,new CameraPreviewController.Listener(){
            public void onReady(Size size,int sensor,boolean front){main.post(capture);}
            public void onSnapshot(CameraPreviewController.Snapshot snapshot){
                if(!active)return;
                io.execute(()->{
                    String outcome="camera_relay_active";
                    try{
                        CameraJpeg.Frame frame=CameraJpeg.prepare(snapshot.jpeg,motionEnabled);
                        Boolean changed=motionEnabled?motion.changed(frame.gray):null;
                        if(!active)return;
                        upload.upload(frame,snapshot.capturedAt,changed,getSharedPreferences(MainActivity.PREF,0).getInt(CameraRefresh.KEY,CameraRefresh.DEFAULT));
                        if(active){sent++;lastSent=System.currentTimeMillis();}
                    }catch(Exception error){
                        String message=error.getMessage();
                        outcome=message!=null&&message.matches("camera_[a-z_]+")?message:"camera_upload_error";
                    }
                    final String next=outcome;
                    main.post(()->{
                        if(active){
                            status=next;
                            if(next.equals("camera_auth_error")||next.equals("camera_pairing_error")){stopSelf();return;}
                            int interval=getSharedPreferences(MainActivity.PREF,0)
                                    .getInt(CameraRefresh.KEY,CameraRefresh.DEFAULT);
                            long elapsed=SystemClock.elapsedRealtime()-captureStarted;
                            main.postDelayed(capture,CameraRefresh.nextDelay(interval,elapsed,next.equals("camera_relay_active")));
                        }
                    });
                });
            }
            public void onError(){
                if(!active)return;
                if(camera!=null){camera.close();camera=null;}
                if(++retries<3)main.postDelayed(CameraRelayService.this::open,1000);
                else{status="camera_error";stopSelf();}
            }
        });
        camera.open(lens,null);
    }
    @Override public void onDestroy(){
        active=false;running=false;main.removeCallbacksAndMessages(null);
        if(camera!=null){camera.close();camera=null;}
        if(upload!=null)upload.close();io.shutdownNow();motion.clear();
        if(wake!=null&&wake.isHeld())wake.release();
        if(!status.equals("camera_error")&&!status.equals("camera_setup_required")&&!status.equals("camera_auth_error")&&!status.equals("camera_pairing_error"))status="camera_relay_off";
        stopForeground(true);super.onDestroy();
    }
}
