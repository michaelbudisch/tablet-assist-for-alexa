package de.tafa.devicebridge;

/** Opt-in local voice activity gate. Never stores audio or a transcript. */
final class ContinuousSpeechTrigger {
    private double noise=0.003;
    private int consecutive=0;
    boolean feed(short[] pcm,int length){
        if(pcm==null||length<=0)return false;
        double energy=0;
        for(int i=0;i<length;i++){
            double value=pcm[i]/32768.0;
            energy+=value*value;
        }
        double rms=Math.sqrt(energy/length);
        boolean voiced=rms>Math.max(0.014,Math.min(0.08,noise*3.5));
        if(voiced)consecutive++;
        else{
            consecutive=0;
            noise=noise*0.985+rms*0.015;
        }
        return consecutive>=15; // 300 ms of sustained sound, not a single click
    }
}