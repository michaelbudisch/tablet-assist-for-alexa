package de.tafa.devicebridge;

/** Physical pose relative to the device's natural orientation, independent of screen lock. */
final class CameraRotation {
    private int physical=-1;
    synchronized void update(int degrees){
        if(degrees<0||degrees>=360)return; // Flat/unknown: retain the last reliable mounting pose.
        int rounded=((degrees+45)/90*90)%360;
        if(physical<0){physical=rounded;return;}
        int distance=Math.abs(degrees-physical);
        distance=Math.min(distance,360-distance);
        if(distance>=60)physical=rounded; // 15-degree hysteresis beyond the quadrant boundary.
    }
    synchronized int imageDegrees(int sensor,int display,boolean front){
        int pose=physical<0?normalize(-display):physical;
        return normalize(sensor+(front?-pose:pose));
    }
    static int normalize(int value){return (value%360+360)%360;}
}
