package de.tafa.devicebridge;

import android.graphics.*;
import android.media.ExifInterface;
import java.io.*;

/** Normalize our own Camera2 JPEG: upright, unmirrored, bounded, no EXIF/GPS in the upload. */
final class CameraJpeg {
    static final class Frame {
        final byte[] jpeg;
        final int[] gray;
        Frame(byte[] jpeg,int[] gray){this.jpeg=jpeg;this.gray=gray;}
    }
    static Frame prepare(byte[] input,boolean motion)throws IOException {
        BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;
        BitmapFactory.decodeByteArray(input,0,input.length,bounds);
        if(bounds.outWidth<=0||bounds.outHeight<=0||(long)bounds.outWidth*bounds.outHeight>1280L*960)
            throw new IOException("camera_image_error");
        Bitmap decoded=BitmapFactory.decodeByteArray(input,0,input.length),upright=null;
        if(decoded==null)throw new IOException("camera_image_error");
        try{
            ExifInterface exif=new ExifInterface(new ByteArrayInputStream(input));
            int orientation=exif.getAttributeInt(ExifInterface.TAG_ORIENTATION,ExifInterface.ORIENTATION_NORMAL);
            Matrix matrix=new Matrix();
            switch(orientation){
                case 2:matrix.setScale(-1,1);break;
                case 3:matrix.setRotate(180);break;
                case 4:matrix.setScale(1,-1);break;
                case 5:matrix.setRotate(90);matrix.postScale(-1,1);break;
                case 6:matrix.setRotate(90);break;
                case 7:matrix.setRotate(270);matrix.postScale(-1,1);break;
                case 8:matrix.setRotate(270);break;
                default:break;
            }
            upright=Bitmap.createBitmap(decoded,0,0,decoded.getWidth(),decoded.getHeight(),matrix,true);
            int[] gray=null;
            if(motion){
                Bitmap small=Bitmap.createScaledBitmap(upright,64,48,true);
                try{
                    int[] pixels=new int[64*48];small.getPixels(pixels,0,64,0,0,64,48);gray=new int[pixels.length];
                    for(int i=0;i<pixels.length;i++)gray[i]=(Color.red(pixels[i])*77+Color.green(pixels[i])*150+Color.blue(pixels[i])*29)>>8;
                }finally{if(small!=upright)small.recycle();}
            }
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            if(!upright.compress(Bitmap.CompressFormat.JPEG,85,bytes)||bytes.size()>2*1024*1024)throw new IOException("camera_image_error");
            return new Frame(bytes.toByteArray(),gray);
        }finally{if(upright!=null&&upright!=decoded)upright.recycle();decoded.recycle();}
    }
}
