package de.jarvis.audio;

/**
 * Lightweight endpoint detector for optional native Assist capture.
 * 20 ms PCM16 frames at 16 kHz. No recorded audio is kept in this class.
 * Designed to leave short thinking pauses intact, like the Jarvis dashboard.
 */
final class NativeSpeechEndpoint {
    enum Decision { CONTINUE, END, EMPTY, LIMIT }

    private final int pauseFrames;
    private final int emptyFrames;
    private int frames, voiced, silent, recent, recentCount;
    private boolean started;
    private double noise=0.003;

    NativeSpeechEndpoint(int pauseMs, int emptyMs) {
        pauseFrames=Math.max(45,Math.min(160,pauseMs/20));
        emptyFrames=Math.max(150,Math.min(550,emptyMs/20));
    }

    Decision feed(short[] samples, int length) {
        if(length<=0)return Decision.CONTINUE;
        double energy=0;
        for(int i=0;i<length;i++){
            double v=samples[i]/32768.0;
            energy+=v*v;
        }
        double rms=Math.sqrt(energy/length);
        frames++;
        double threshold=Math.max(0.006,Math.min(0.04,noise*2.5));
        boolean sound=rms>=threshold;
        if(!started&&!sound)noise=noise*0.97+rms*0.03;
        recent=((recent<<1)|(sound?1:0))&255;
        recentCount=Math.min(8,recentCount+1);
        if(!started){
            if(recentCount>=8 && Integer.bitCount(recent)>=5){
                started=true;voiced=5;silent=0;
            }else if(frames>=emptyFrames)return Decision.EMPTY;
        }else {
            if(sound){voiced++;silent=0;}
            else silent++;
            if(voiced>=12&&silent>=pauseFrames)return Decision.END;
        }
        if(frames>=1250)return Decision.LIMIT; // 25 s hard maximum
        return Decision.CONTINUE;
    }

    boolean hasSpeech(){return started&&voiced>=12;}
}
