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
    private final int maxFrames;
    private final boolean followup;
    private int frames, voiced, silent, recent, recentCount;
    private boolean started,lastSound;
    private double noise=0.003;

    NativeSpeechEndpoint(int pauseMs, int emptyMs) {
        this(pauseMs,emptyMs,false);
    }
    NativeSpeechEndpoint(int pauseMs,int emptyMs,boolean followup) {
        this.followup=followup;
        pauseFrames=Math.max(45,Math.min(160,pauseMs/20));
        emptyFrames=Math.max(75,Math.min(550,emptyMs/20));
        maxFrames=followup?500:1250; // 10 seconds vs. 25 seconds.
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
        // An unlocked follow-up uses a stricter noise gate than a wakeword request.
        double threshold=Math.max(followup?0.011:0.006,
                                  Math.min(0.04,noise*(followup?3.0:2.5)));
        boolean sound=rms>=threshold;
        lastSound=sound;
        if(!started&&!sound)noise=noise*0.97+rms*0.03;
        recent=((recent<<1)|(sound?1:0))&255;
        recentCount=Math.min(8,recentCount+1);
        if(!started){
            if(recentCount>=8 && Integer.bitCount(recent)>=(followup?6:5)){
                started=true;voiced=5;silent=0;
            }else if(frames>=emptyFrames)return Decision.EMPTY;
        }else {
            if(sound){voiced++;silent=0;}
            else silent++;
            if(voiced>=12&&silent>=pauseFrames)return Decision.END;
        }
        if(frames>=maxFrames)return Decision.LIMIT;
        return Decision.CONTINUE;
    }

    boolean started(){return started;}
    boolean voicedFrame(){return started&&lastSound;}
    boolean hasSpeech(){return started&&voiced>=12;}
}
