package de.jarvis.audio;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.display.DisplayManager;
import android.media.ExifInterface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.util.Size;
import android.view.*;
import android.widget.*;
import java.io.ByteArrayInputStream;
import java.text.DateFormat;
import java.util.*;

/** Explicit, visible camera preparation; leaving this screen clears images and closes the camera. */
public class CameraActivity extends Activity implements TextureView.SurfaceTextureListener {
    private static final int CAMERA_PERMISSION=200;
    private TextureView preview;
    private Spinner lenses;
    private TextView status,snapshotStatus;
    private ImageView snapshotView;
    private List<CameraPreviewController.Lens> available=Collections.emptyList();
    private CameraPreviewController controller;
    private Bitmap snapshot;
    private Size bufferSize;
    private int sensorOrientation;
    private boolean visible,startRequested,permissionPending;
    private boolean relayPermissionPending;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final Runnable refreshRelay=new Runnable(){public void run(){
        ((TextView)findViewById(R.id.camera_relay_status)).setText(relayMessage(CameraActivity.this));
        boolean relay=CameraRelayService.running;
        findViewById(R.id.camera_relay_start).setEnabled(!relay&&!available.isEmpty());
        findViewById(R.id.camera_relay_stop).setEnabled(relay);
        findViewById(R.id.camera_motion).setEnabled(!relay);
        if(controller==null){lenses.setEnabled(!relay);findViewById(R.id.camera_start).setEnabled(!relay&&!available.isEmpty());}
        handler.postDelayed(this,1000);
    }};
    private DisplayManager displays;
    private final DisplayManager.DisplayListener displayListener=new DisplayManager.DisplayListener(){
        public void onDisplayAdded(int id){}
        public void onDisplayRemoved(int id){}
        public void onDisplayChanged(int id){transform();}
    };
    @Override protected void attachBaseContext(Context base){super.attachBaseContext(AppLanguage.wrap(base));}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);setContentView(R.layout.activity_camera);
        if(getResources().getConfiguration().screenWidthDp>760)
            findViewById(R.id.camera_page).setLayoutParams(new FrameLayout.LayoutParams(
                    Math.round(760*getResources().getDisplayMetrics().density),FrameLayout.LayoutParams.WRAP_CONTENT,Gravity.CENTER_HORIZONTAL));
        preview=findViewById(R.id.camera_preview);preview.setOpaque(false);preview.setSurfaceTextureListener(this);
        status=findViewById(R.id.camera_status);snapshotStatus=findViewById(R.id.camera_snapshot_status);
        snapshotView=findViewById(R.id.camera_snapshot);lenses=findViewById(R.id.camera_lens);
        findViewById(R.id.camera_back).setOnClickListener(v->finish());
        findViewById(R.id.camera_start).setOnClickListener(v->requestStart());
        findViewById(R.id.camera_stop).setOnClickListener(v->stopCamera());
        findViewById(R.id.camera_capture).setOnClickListener(v->{
            if(controller==null)return;
            findViewById(R.id.camera_capture).setEnabled(false);
            snapshotStatus.setText(R.string.camera_capturing);
            controller.capture(rotation());
        });
        findViewById(R.id.camera_clear).setOnClickListener(v->clearSnapshot());
        Spinner refreshRate=findViewById(R.id.camera_refresh_rate);
        var prefs=getSharedPreferences(MainActivity.PREF,0);
        int[] intervals=CameraRefresh.options();
        ArrayList<String> intervalLabels=new ArrayList<>();
        int savedInterval=CameraRefresh.normalize(prefs.getInt(CameraRefresh.KEY,CameraRefresh.DEFAULT));
        int selectedInterval=0;
        for(int i=0;i<intervals.length;i++){
            intervalLabels.add(getResources().getQuantityString(R.plurals.camera_refresh_interval,intervals[i],intervals[i]));
            if(intervals[i]==savedInterval)selectedInterval=i;
        }
        refreshRate.setAdapter(BridgeChoices.create(this,intervalLabels));
        refreshRate.setSelection(selectedInterval);
        refreshRate.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,View view,int position,long id){
                prefs.edit().putInt(CameraRefresh.KEY,intervals[position]).apply();
            }
        });
        CheckBox motion=findViewById(R.id.camera_motion);
        motion.setChecked(getSharedPreferences(MainActivity.PREF,0).getBoolean("camera_motion",false));
        motion.setOnCheckedChangeListener((button,checked)->getSharedPreferences(MainActivity.PREF,0).edit().putBoolean("camera_motion",checked).apply());
        findViewById(R.id.camera_relay_start).setOnClickListener(v->requestRelay());
        findViewById(R.id.camera_relay_stop).setOnClickListener(v->stopService(new Intent(this,CameraRelayService.class)));
        try {
            available=CameraPreviewController.lenses(this);
            ArrayList<String> labels=new ArrayList<>();
            String saved=getSharedPreferences(MainActivity.PREF,0).getString("camera_lens_id","");
            int selected=0;
            for(int i=0;i<available.size();i++){
                CameraPreviewController.Lens lens=available.get(i);
                int label=lens.facing==CameraCharacteristics.LENS_FACING_FRONT?R.string.camera_front:
                        lens.facing==CameraCharacteristics.LENS_FACING_BACK?R.string.camera_rear:R.string.camera_external;
                labels.add(getString(label)+" · "+(i+1));
                if(lens.id.equals(saved))selected=i;
            }
            lenses.setAdapter(BridgeChoices.create(this,labels));
            lenses.setSelection(selected);
            lenses.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
                public void onNothingSelected(AdapterView<?> parent){}
                public void onItemSelected(AdapterView<?> parent,View view,int position,long id){
                    getSharedPreferences(MainActivity.PREF,0).edit().putString("camera_lens_id",available.get(position).id).apply();
                }
            });
            if(available.isEmpty()){status.setText(R.string.camera_unavailable);findViewById(R.id.camera_start).setEnabled(false);}
        }catch(Exception error){status.setText(R.string.camera_error);findViewById(R.id.camera_start).setEnabled(false);}
        displays=getSystemService(DisplayManager.class);
    }
    private void requestStart(){
        if(available.isEmpty()||!visible||CameraRelayService.running)return;
        if(checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){
            permissionPending=true;
            requestPermissions(new String[]{Manifest.permission.CAMERA},CAMERA_PERMISSION);return;
        }
        startRequested=true;status.setText(R.string.camera_starting);
        findViewById(R.id.camera_start).setEnabled(false);findViewById(R.id.camera_stop).setEnabled(true);
        findViewById(R.id.camera_start).setAlpha(0.45f);
        lenses.setEnabled(false);
        if(preview.isAvailable())openCamera();
    }
    private void requestRelay(){
        if(!visible||available.isEmpty()||CameraRelayService.running)return;
        if(!getSharedPreferences(MainActivity.PREF,0).contains("secret")){
            CameraRelayService.status="camera_setup_required";
            ((TextView)findViewById(R.id.camera_relay_status)).setText(R.string.camera_setup_required);return;
        }
        if(checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){
            relayPermissionPending=true;requestPermissions(new String[]{Manifest.permission.CAMERA},CAMERA_PERMISSION);return;
        }
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},201);
        stopCamera();
        try{startForegroundService(new Intent(this,CameraRelayService.class).setAction("start"));}
        catch(Exception error){((TextView)findViewById(R.id.camera_relay_status)).setText(R.string.camera_error);}
    }
    static String relayMessage(Context context){
        int resource=context.getResources().getIdentifier(CameraRelayService.status,"string",context.getPackageName());
        String message=context.getString(resource==0?R.string.camera_upload_error:resource);
        if(CameraRelayService.running&&CameraRelayService.sent>0)
            message+="\n"+context.getString(R.string.camera_relay_count,CameraRelayService.sent,
                    DateFormat.getTimeInstance(DateFormat.MEDIUM).format(new Date(CameraRelayService.lastSent)));
        return message;
    }
    private void openCamera(){
        if(!visible||!startRequested||controller!=null)return;
        clearSnapshot();
        controller=new CameraPreviewController(this,new CameraPreviewController.Listener(){
            public void onReady(Size size,int sensor,boolean facingFront){
                bufferSize=size;sensorOrientation=sensor;transform();
                findViewById(R.id.camera_preview_cover).setVisibility(View.GONE);
                status.setText(R.string.camera_active);findViewById(R.id.camera_capture).setEnabled(true);
            }
            public void onSnapshot(CameraPreviewController.Snapshot image){
                try {
                    Bitmap decoded=BitmapFactory.decodeByteArray(image.jpeg,0,image.jpeg.length);
                    if(decoded==null)throw new IllegalArgumentException("JPEG decode failed");
                    ExifInterface exif=new ExifInterface(new ByteArrayInputStream(image.jpeg));
                    int orientation=exif.getAttributeInt(ExifInterface.TAG_ORIENTATION,ExifInterface.ORIENTATION_NORMAL);
                    Matrix matrix=new Matrix();
                    switch(orientation){
                        case ExifInterface.ORIENTATION_FLIP_HORIZONTAL:matrix.setScale(-1,1);break;
                        case ExifInterface.ORIENTATION_ROTATE_180:matrix.setRotate(180);break;
                        case ExifInterface.ORIENTATION_FLIP_VERTICAL:matrix.setScale(1,-1);break;
                        case ExifInterface.ORIENTATION_TRANSPOSE:matrix.setRotate(90);matrix.postScale(-1,1);break;
                        case ExifInterface.ORIENTATION_ROTATE_90:matrix.setRotate(90);break;
                        case ExifInterface.ORIENTATION_TRANSVERSE:matrix.setRotate(270);matrix.postScale(-1,1);break;
                        case ExifInterface.ORIENTATION_ROTATE_270:matrix.setRotate(270);break;
                        default:break;
                    }
                    Bitmap upright=Bitmap.createBitmap(decoded,0,0,decoded.getWidth(),decoded.getHeight(),matrix,true);
                    if(upright!=decoded)decoded.recycle();
                    clearSnapshot();snapshot=upright;snapshotView.setImageBitmap(snapshot);snapshotView.setVisibility(View.VISIBLE);
                    snapshotStatus.setText(getString(R.string.camera_snapshot_ready,
                            DateFormat.getTimeInstance(DateFormat.MEDIUM).format(new Date(image.capturedAt)),snapshot.getWidth(),snapshot.getHeight()));
                    findViewById(R.id.camera_clear).setEnabled(true);
                    findViewById(R.id.camera_capture).setEnabled(true);
                }catch(Exception error){stopCamera();status.setText(R.string.camera_error);}
            }
            public void onError(){stopCamera();status.setText(R.string.camera_error);}
        });
        controller.open(available.get(lenses.getSelectedItemPosition()).id,preview.getSurfaceTexture());
    }
    private int rotation(){return getWindowManager().getDefaultDisplay().getRotation()*90;}
    private void transform(){
        if(bufferSize==null||preview.getWidth()==0||preview.getHeight()==0)return;
        // TextureView already applies sensor orientation and front-camera mirroring.
        // Undo its default stretch, then account only for display rotation and fit the view.
        int angle=-rotation();
        float width=preview.getWidth(),height=preview.getHeight();
        float orientedWidth=sensorOrientation%180==0?bufferSize.getWidth():bufferSize.getHeight();
        float orientedHeight=sensorOrientation%180==0?bufferSize.getHeight():bufferSize.getWidth();
        float rotatedWidth=angle%180==0?orientedWidth:orientedHeight;
        float rotatedHeight=angle%180==0?orientedHeight:orientedWidth;
        float scale=Math.min(width/rotatedWidth,height/rotatedHeight);
        Matrix matrix=new Matrix();matrix.setScale(orientedWidth/width,orientedHeight/height);
        matrix.postTranslate(-orientedWidth/2f,-orientedHeight/2f);matrix.postRotate(angle);
        matrix.postScale(scale,scale);matrix.postTranslate(width/2,height/2);preview.setTransform(matrix);
    }
    private void clearSnapshot(){
        snapshotView.setImageDrawable(null);snapshotView.setVisibility(View.GONE);
        if(snapshot!=null){snapshot.recycle();snapshot=null;}
        snapshotStatus.setText(R.string.camera_no_snapshot);findViewById(R.id.camera_clear).setEnabled(false);
    }
    private void stopCamera(){
        startRequested=false;permissionPending=false;
        if(controller!=null){controller.close();controller=null;}
        bufferSize=null;clearSnapshot();
        findViewById(R.id.camera_preview_cover).setVisibility(View.VISIBLE);
        findViewById(R.id.camera_start).setEnabled(!available.isEmpty());findViewById(R.id.camera_stop).setEnabled(false);
        findViewById(R.id.camera_start).setAlpha(1f);
        findViewById(R.id.camera_capture).setEnabled(false);lenses.setEnabled(true);status.setText(R.string.camera_off);
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){
        super.onRequestPermissionsResult(request,permissions,results);
        if(request!=CAMERA_PERMISSION)return;
        if(relayPermissionPending){relayPermissionPending=false;if(visible&&results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED)requestRelay();
            else {CameraRelayService.status="camera_denied";((TextView)findViewById(R.id.camera_relay_status)).setText(R.string.camera_denied);}return;}
        boolean pending=permissionPending;permissionPending=false;
        if(!visible||!pending)return;
        if(results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED)requestStart();
        else {
            status.setText(R.string.camera_denied);
            if(!shouldShowRequestPermissionRationale(Manifest.permission.CAMERA))
                new android.app.AlertDialog.Builder(this).setMessage(R.string.camera_denied)
                        .setNegativeButton(R.string.cancel,null).setPositiveButton(R.string.camera_settings,(dialog,which)->
                                startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,Uri.parse("package:"+getPackageName())))).show();
        }
    }
    @Override protected void onStart(){super.onStart();visible=true;displays.registerDisplayListener(displayListener,null);handler.post(refreshRelay);}
    @Override protected void onStop(){visible=false;handler.removeCallbacksAndMessages(null);stopCamera();displays.unregisterDisplayListener(displayListener);super.onStop();}
    @Override protected void onDestroy(){if(controller!=null)controller.close();super.onDestroy();}
    @Override public void onSurfaceTextureAvailable(SurfaceTexture texture,int width,int height){openCamera();}
    @Override public void onSurfaceTextureSizeChanged(SurfaceTexture texture,int width,int height){transform();}
    @Override public boolean onSurfaceTextureDestroyed(SurfaceTexture texture){stopCamera();return true;}
    @Override public void onSurfaceTextureUpdated(SurfaceTexture texture){}
}
