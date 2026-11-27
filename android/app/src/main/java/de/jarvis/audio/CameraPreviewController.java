package de.jarvis.audio;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.*;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.util.Size;
import android.view.Surface;
import java.nio.ByteBuffer;
import java.util.*;

/** Local Camera2 preview and on-demand JPEG source. No storage, network, audio or background service. */
final class CameraPreviewController implements AutoCloseable {
    static final class Lens {
        final String id;
        final int facing;
        Lens(String id, int facing) { this.id=id; this.facing=facing; }
    }
    /** JPEG includes its camera-provided EXIF orientation; timestamp records arrival at the app. */
    static final class Snapshot {
        final byte[] jpeg;
        final long capturedAt;
        Snapshot(byte[] jpeg) { this.jpeg=jpeg; capturedAt=System.currentTimeMillis(); }
    }
    interface Listener {
        void onReady(Size preview, int sensorOrientation, boolean front);
        void onSnapshot(Snapshot snapshot);
        void onError();
        /** Optional background YUV analysis; true means the listener closes the image. */
        default boolean onAnalysis(Image image,int sensorOrientation,boolean front){return false;}
    }
    private final Context context;
    private final Listener listener;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final HandlerThread thread=new HandlerThread("relay-camera");
    private final Handler worker;
    private volatile boolean closed;
    private CameraDevice camera;
    private CameraCaptureSession session;
    private ImageReader reader;
    private ImageReader backgroundPreview;
    private Surface previewSurface;
    private boolean capturing,ready;
    private int sensor;
    private boolean front;
    private final Runnable captureTimeout=()->fail();

    CameraPreviewController(Context context, Listener listener) {
        this.context=context.getApplicationContext(); this.listener=listener;
        thread.start(); worker=new Handler(thread.getLooper());
    }
    static List<Lens> lenses(Context context) throws CameraAccessException {
        CameraManager manager=context.getSystemService(CameraManager.class);
        List<Lens> result=new ArrayList<>();
        for(String id:manager.getCameraIdList()) {
            Integer facing=manager.getCameraCharacteristics(id).get(CameraCharacteristics.LENS_FACING);
            result.add(new Lens(id, facing==null ? CameraCharacteristics.LENS_FACING_EXTERNAL : facing));
        }
        result.sort(Comparator.comparingInt(lens -> lens.facing==CameraCharacteristics.LENS_FACING_FRONT?0:
                lens.facing==CameraCharacteristics.LENS_FACING_BACK?1:2));
        return result;
    }
    // Bound both outputs to avoid full-resolution photos on a tablet used mainly for audio.
    private static Size choose(Size[] sizes, double aspect) {
        if(sizes==null||sizes.length==0)throw new IllegalArgumentException("No output sizes");
        return Arrays.stream(sizes).filter(size -> (long)size.getWidth()*size.getHeight()<=1280L*960)
                .min(Comparator.comparingDouble(size -> {
            long area=(long)size.getWidth()*size.getHeight();
            double ratio=(double)size.getWidth()/size.getHeight();
            return -area + Math.abs(ratio-aspect)*1e9;
        })).orElseThrow();
    }
    void open(String id, SurfaceTexture texture) {
        worker.post(()->{
            if(closed)return;
            try {
                if(context.checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){fail();return;}
                CameraManager manager=context.getSystemService(CameraManager.class);
                CameraCharacteristics characteristics=manager.getCameraCharacteristics(id);
                Integer orientation=characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
                sensor=orientation==null?0:orientation;
                front=Objects.equals(characteristics.get(CameraCharacteristics.LENS_FACING),CameraCharacteristics.LENS_FACING_FRONT);
                StreamConfigurationMap config=characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
                if(config==null){fail();return;}
                Size jpeg=choose(config.getOutputSizes(ImageFormat.JPEG),4.0/3);
                Size preview=choose(config.getOutputSizes(SurfaceTexture.class),(double)jpeg.getWidth()/jpeg.getHeight());
                if(texture!=null){
                    texture.setDefaultBufferSize(preview.getWidth(),preview.getHeight());
                    previewSurface=new Surface(texture);
                }else{
                    Size[] analysisSizes=Arrays.stream(config.getOutputSizes(ImageFormat.YUV_420_888))
                        .filter(s->s.getWidth()<=640&&s.getHeight()<=480).toArray(Size[]::new);
                    Size drainSize=choose(analysisSizes.length>0?analysisSizes:config.getOutputSizes(ImageFormat.YUV_420_888),4.0/3);
                    backgroundPreview=ImageReader.newInstance(drainSize.getWidth(),drainSize.getHeight(),ImageFormat.YUV_420_888,2);
                    backgroundPreview.setOnImageAvailableListener(source->{
                        Image image=null;boolean owned=false;
                        try{
                            image=source.acquireLatestImage();
                            if(image!=null&&!closed)owned=listener.onAnalysis(image,sensor,front);
                        }catch(RuntimeException ignored){}
                        finally{if(image!=null&&!owned)try{image.close();}catch(RuntimeException ignored){}}
                    },worker);
                    previewSurface=backgroundPreview.getSurface();
                }
                reader=ImageReader.newInstance(jpeg.getWidth(),jpeg.getHeight(),ImageFormat.JPEG,2);
                reader.setOnImageAvailableListener(source->{
                    try(Image image=source.acquireLatestImage()) {
                        if(image==null||closed||!capturing)return;
                        ByteBuffer data=image.getPlanes()[0].getBuffer();
                        if(data.remaining()==0||data.remaining()>8*1024*1024){fail();return;}
                        byte[] bytes=new byte[data.remaining()]; data.get(bytes);
                        capturing=false;worker.removeCallbacks(captureTimeout);
                        Snapshot snapshot=new Snapshot(bytes);
                        main.post(()->{if(!closed)listener.onSnapshot(snapshot);});
                    }catch(Exception error){fail();}
                },worker);
                manager.openCamera(id,new CameraDevice.StateCallback(){
                    @Override public void onOpened(CameraDevice device) {
                        if(closed){device.close();return;}
                        // The open callback survives worker shutdown, so a late open can always be closed.
                        if(!worker.post(()->{
                        if(closed){device.close();return;}
                        camera=device;
                        try {
                            camera.createCaptureSession(Arrays.asList(previewSurface,reader.getSurface()),new CameraCaptureSession.StateCallback(){
                                @Override public void onConfigured(CameraCaptureSession configured) {
                                    if(closed){configured.close();return;}
                                    session=configured;
                                    try {
                                        CaptureRequest.Builder request=camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
                                        request.addTarget(previewSurface);
                                        session.setRepeatingRequest(request.build(),new CameraCaptureSession.CaptureCallback(){
                                            @Override public void onCaptureCompleted(CameraCaptureSession active,CaptureRequest request,TotalCaptureResult result){
                                                if(!closed&&!ready){ready=true;main.post(()->{if(!closed)listener.onReady(preview,sensor,front);});}
                                            }
                                        },worker);
                                    }catch(Exception error){fail();}
                                }
                                @Override public void onConfigureFailed(CameraCaptureSession configured){fail();}
                            },worker);
                        }catch(Exception error){fail();}
                        }))device.close();
                    }
                    @Override public void onDisconnected(CameraDevice device){device.close();if(!closed)worker.post(()->fail());}
                    @Override public void onError(CameraDevice device,int error){device.close();if(!closed)worker.post(()->fail());}
                },main);
                worker.postDelayed(()->{if(!closed&&!ready)fail();},10000);
            }catch(Exception error){fail();}
        });
    }
    void capture(int displayRotationDegrees) {
        worker.post(()->{
            if(closed||!ready||capturing||camera==null||session==null)return;
            try {
                capturing=true;
                CaptureRequest.Builder request=camera.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
                request.addTarget(reader.getSurface());
                request.set(CaptureRequest.JPEG_ORIENTATION,(sensor-displayRotationDegrees*(front?-1:1)+360)%360);
                request.set(CaptureRequest.JPEG_QUALITY,(byte)85);
                session.capture(request.build(),new CameraCaptureSession.CaptureCallback(){
                    @Override public void onCaptureFailed(CameraCaptureSession active,CaptureRequest request,CaptureFailure failure){fail();}
                },worker);
                worker.postDelayed(captureTimeout,8000);
            }catch(Exception error){fail();}
        });
    }
    private void fail() {
        if(closed)return;
        main.post(()->{if(!closed)listener.onError();});
        release();
    }
    private void release() {
        worker.removeCallbacksAndMessages(null);
        ready=false;capturing=false;
        if(session!=null){session.close();session=null;}
        if(camera!=null){camera.close();camera=null;}
        if(reader!=null){reader.close();reader=null;}
        if(backgroundPreview!=null){backgroundPreview.close();backgroundPreview=null;}
        if(previewSurface!=null){previewSurface.release();previewSurface=null;}
    }
    @Override public void close() {
        if(closed)return;
        closed=true;
        worker.post(()->{try{release();}finally{thread.quitSafely();}});
    }
}
