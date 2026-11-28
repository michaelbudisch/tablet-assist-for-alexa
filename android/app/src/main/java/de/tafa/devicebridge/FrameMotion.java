package de.tafa.devicebridge;

/** Coarse image change, not person/object recognition. Suppress uniform brightness changes. */
final class FrameMotion {
    private int[] previous;
    boolean changed(int[] gray) {
        if(previous==null||previous.length!=gray.length){previous=gray.clone();return false;}
        long sum=0;
        for(int i=0;i<gray.length;i++)sum+=gray[i]-previous[i];
        double shift=(double)sum/gray.length;
        int changed=0;
        for(int i=0;i<gray.length;i++)if(Math.abs(gray[i]-previous[i]-shift)>22)changed++;
        previous=gray.clone();
        return changed>gray.length*0.08;
    }
    void clear(){previous=null;}
}
