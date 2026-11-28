package de.tafa.devicebridge;

/** Device-monotonic presence with entry confirmation, exit delay and hysteresis. */
final class ApproachState {
    private boolean near;
    private long candidate=-1,absent=-1,last=-1;
    synchronized boolean update(long now,double percent,int threshold,int holdSeconds){
        threshold=Math.max(15,Math.min(60,threshold));holdSeconds=Math.max(2,Math.min(10,holdSeconds));
        if(last>=0&&now<last){candidate=-1;absent=-1;near=false;}
        else if(last>=0&&now-last>2500){
            candidate=-1;
            if(now-last>=8000){absent=-1;near=false;}
        }
        last=now;
        if(!near){
            absent=-1;
            if(percent>=threshold){
                if(candidate<0)candidate=now;
                if(now-candidate>=800){near=true;candidate=-1;}
            }else candidate=-1;
        }else if(percent>=threshold*.8){absent=-1;}
        else{
            if(absent<0)absent=now;
            if(now-absent>=holdSeconds*1000L){near=false;candidate=-1;absent=-1;}
        }
        return near;
    }
    synchronized void clear(){near=false;candidate=absent=last=-1;}
    static double facePercent(int width,int height,int left,int top,int right,int bottom){
        if(width<=0||height<=0||right<=left||bottom<=top)return 0;
        double cx=(left+right)*.5/width,cy=(top+bottom)*.5/height;
        if(cx<.2||cx>.8||cy<.12||cy>.88)return 0;
        return Math.min(100,100.0*(right-left)/Math.min(width,height));
    }
}
