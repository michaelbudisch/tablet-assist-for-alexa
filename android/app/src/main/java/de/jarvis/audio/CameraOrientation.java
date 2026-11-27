package de.jarvis.audio;

import android.content.Context;
import android.hardware.SensorManager;
import android.hardware.display.DisplayManager;
import android.os.Handler;
import android.os.Looper;
import android.view.Display;
import android.view.OrientationEventListener;

/** One low-rate physical orientation listener per explicitly opened camera. */
final class CameraOrientation implements AutoCloseable {
    private final CameraRotation rotation=new CameraRotation();
    private final DisplayManager displays;
    private final OrientationEventListener listener;
    private volatile int displayDegrees;
    private final DisplayManager.DisplayListener displayListener=new DisplayManager.DisplayListener(){
        @Override public void onDisplayAdded(int id){refreshDisplay();}
        @Override public void onDisplayRemoved(int id){refreshDisplay();}
        @Override public void onDisplayChanged(int id){if(id==Display.DEFAULT_DISPLAY)refreshDisplay();}
    };
    CameraOrientation(Context context){
        displays=context.getSystemService(DisplayManager.class);
        refreshDisplay();
        if(displays!=null)displays.registerDisplayListener(displayListener,new Handler(Looper.getMainLooper()));
        listener=new OrientationEventListener(context,SensorManager.SENSOR_DELAY_NORMAL){
            @Override public void onOrientationChanged(int degrees){rotation.update(degrees);}
        };
        if(listener.canDetectOrientation())listener.enable();
    }
    private void refreshDisplay(){
        Display display=displays==null?null:displays.getDisplay(Display.DEFAULT_DISPLAY);
        displayDegrees=display==null?0:display.getRotation()*90;
    }
    int imageDegrees(int sensor,boolean front){
        // No display-service calls on the high-rate Camera2 analysis path.
        return rotation.imageDegrees(sensor,displayDegrees,front);
    }
    @Override public void close(){
        listener.disable();
        if(displays!=null)displays.unregisterDisplayListener(displayListener);
    }
}
