package de.jarvis.audio;
import android.app.Instrumentation;
import android.graphics.ImageFormat;
import android.media.*;
import android.os.*;
import com.google.android.gms.tasks.Tasks;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.face.*;
import com.google.mlkit.vision.face.FaceDetector;
import java.util.concurrent.*;

/** Synthetic blank YUV, offline bundled model; no real camera, person, HA or microphone. */
final class ApproachSmoke {
    static String run(Instrumentation instrumentation)throws Exception{
        HandlerThread thread=new HandlerThread("approach-smoke");thread.start();
        ImageReader reader=ImageReader.newInstance(640,480,ImageFormat.YUV_420_888,3);
        ImageWriter writer=null;Image image=null;FaceDetector detector=null;
        try{
            CountDownLatch arrived=new CountDownLatch(1);
            reader.setOnImageAvailableListener(r->arrived.countDown(),new Handler(thread.getLooper()));
            writer=ImageWriter.newInstance(reader.getSurface(),2);
            Image input=writer.dequeueInputImage();
            for(int i=0;i<input.getPlanes().length;i++){
                java.nio.ByteBuffer b=input.getPlanes()[i].getBuffer();
                byte value=(byte)(i==0?16:128);
                while(b.hasRemaining())b.put(value);
            }
            writer.queueInputImage(input);
            if(!arrived.await(5,TimeUnit.SECONDS))throw new AssertionError("YUV frame unavailable");
            image=reader.acquireLatestImage();
            if(image==null)throw new AssertionError("Missing YUV frame");
            detector=FaceDetection.getClient(new FaceDetectorOptions.Builder()
                .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_FAST).build());
            byte[] snapshot=ApproachYuv.copy(image,null);
            if(ApproachYuv.copy(image,snapshot)!=snapshot)throw new AssertionError("Analysis buffer must be reused");
            for(int i=0;i<snapshot.length;i++)if(snapshot[i]!=(byte)(i<640*480?16:128))
                throw new AssertionError("YUV plane strides were not normalized");
            image.close();image=null;
            for(int pose:new int[]{0,90,180,270}){
                CameraRotation orientation=new CameraRotation();orientation.update(pose);
                int rotation=orientation.imageDegrees(270,0,true);
                if(!Tasks.await(detector.process(InputImage.fromByteArray(snapshot,640,480,rotation,InputImage.IMAGE_FORMAT_NV21)),30,TimeUnit.SECONDS).isEmpty())
                    throw new AssertionError("Blank frame must not create presence at physical pose "+pose);
            }
            return "Approach smoke passed: bundled detector processed synthetic Camera2 YUV with plane strides, rotation and a reusable private buffer; no false face, no real camera or HA used.";
        }finally{
            if(detector!=null)detector.close();if(image!=null)image.close();
            if(writer!=null)writer.close();reader.close();thread.quitSafely();
        }
    }
}
