package de.jarvis.audio;

import android.app.Instrumentation;
import android.graphics.*;
import android.hardware.display.DisplayManager;
import android.media.ExifInterface;
import android.view.Display;
import java.io.*;
import java.nio.file.Files;

/** Host sets emulator acceleration while Android display rotation remains locked. */
final class CameraOrientationSmoke {
    private static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    static String run(Instrumentation test,int pose)throws Exception{
        var context=test.getTargetContext();
        CameraOrientation[] tracker=new CameraOrientation[1];
        test.runOnMainSync(()->tracker[0]=new CameraOrientation(context));
        try{
            Display display=context.getSystemService(DisplayManager.class).getDisplay(Display.DEFAULT_DISPLAY);
            check(display.getRotation()==0,"Test display must remain locked at natural orientation");
            int expected=CameraRotation.normalize(90-pose);
            long deadline=System.nanoTime()+10_000_000_000L;
            while(tracker[0].imageDegrees(90,true)!=expected&&System.nanoTime()<deadline)Thread.sleep(50);
            check(tracker[0].imageDegrees(90,true)==expected,"Front image follows physical pose "+pose);
            check(tracker[0].imageDegrees(90,false)==CameraRotation.normalize(90+pose),
                "Rear image uses opposite compensation");
            check(display.getRotation()==0,"Physical sensor must work without display rotation");
            jpegMatchesAnalysis(test);
            return "Orientation smoke passed: physical pose "+pose+
                " with display locked, front/rear correction and all four EXIF-normalized JPEG rotations.";
        }finally{test.runOnMainSync(tracker[0]::close);}
    }
    private static void jpegMatchesAnalysis(Instrumentation test)throws Exception{
        // Red top-left, green top-right, blue bottom-right, yellow bottom-left.
        Bitmap raw=Bitmap.createBitmap(80,60,Bitmap.Config.ARGB_8888);
        Canvas canvas=new Canvas(raw);Paint paint=new Paint();
        int[] colors={Color.RED,Color.GREEN,Color.BLUE,Color.YELLOW};
        int[][] areas={{0,0,40,30},{40,0,80,30},{40,30,80,60},{0,30,40,60}};
        for(int i=0;i<4;i++){paint.setColor(colors[i]);int[] a=areas[i];canvas.drawRect(a[0],a[1],a[2],a[3],paint);}
        File file=File.createTempFile("orientation-smoke-",".jpg",test.getTargetContext().getCacheDir());
        try{
            int[] tags={ExifInterface.ORIENTATION_NORMAL,ExifInterface.ORIENTATION_ROTATE_90,
                ExifInterface.ORIENTATION_ROTATE_180,ExifInterface.ORIENTATION_ROTATE_270};
            for(int turn=0;turn<4;turn++){
                try(OutputStream out=new FileOutputStream(file)){check(raw.compress(Bitmap.CompressFormat.JPEG,95,out),"Fixture JPEG");}
                ExifInterface exif=new ExifInterface(file.getPath());
                exif.setAttribute(ExifInterface.TAG_ORIENTATION,Integer.toString(tags[turn]));exif.saveAttributes();
                CameraJpeg.Frame frame=CameraJpeg.prepare(Files.readAllBytes(file.toPath()),true);
                Bitmap upright=BitmapFactory.decodeByteArray(frame.jpeg,0,frame.jpeg.length);
                try{
                    check(upright.getWidth()==(turn%2==0?80:60)&&upright.getHeight()==(turn%2==0?60:80),"Upright dimensions");
                    int actual=upright.getPixel(upright.getWidth()/4,upright.getHeight()/4);
                    int expected=colors[(4-turn)%4];
                    check(Math.abs(Color.red(actual)-Color.red(expected))<30&&
                        Math.abs(Color.green(actual)-Color.green(expected))<30&&
                        Math.abs(Color.blue(actual)-Color.blue(expected))<30,"Correct upright pixel quadrant for "+turn*90);
                    check(frame.gray.length==64*48,"Motion samples upright image");
                }finally{upright.recycle();}
            }
        }finally{raw.recycle();file.delete();}
    }
}
