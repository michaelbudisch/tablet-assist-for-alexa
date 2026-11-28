package de.tafa.devicebridge;

import android.app.Instrumentation;
import android.media.AudioManager;
import android.os.SystemClock;
import static de.tafa.devicebridge.VoiceTrace.Point.*;

/** Silent PCM only. Run on the isolated emulator, not as a live Echo latency measurement. */
final class NativePlaybackSmoke {
    static String run(Instrumentation i)throws Exception{
        VoiceTrace.Store store=new VoiceTrace.Store(SystemClock::elapsedRealtimeNanos);
        VoiceTrace trace=store.begin(VoiceTrace.Kind.MANUAL,System.currentTimeMillis());
        VoiceTrace.Playback probe=store.playback("e".repeat(32));
        store.bind(trace,"e".repeat(32));
        AudioManager manager=i.getTargetContext().getSystemService(AudioManager.class);
        BluetoothPcmOutput output=new BluetoothPcmOutput(manager,()->false,AudioOutputMode.TABLET,probe);
        try{
            PcmFormat format=new PcmFormat(16000,1);
            output.open(format);
            if(trace.has(OUTPUT_SUBMITTED)||trace.has(OUTPUT_PROGRESS))
                throw new AssertionError("Silent route warmup was counted as a response");
            if(!trace.has(ROUTE_READY))throw new AssertionError("Route not measured");
            byte[] silence=new byte[format.bytesForMs(20)];
            for(int n=0;n<15;n++)output.write(silence,0,silence.length);
            output.drain();
            VoiceTrace.Snapshot result=trace.snapshot();
            if(result.between(ROUTE_READY,OUTPUT_SUBMITTED)==null||
               result.between(OUTPUT_SUBMITTED,OUTPUT_PROGRESS)==null)
                throw new AssertionError("Expected verified submission and playback-head progress");
            if(!"audiotrack_head".equals(result.facts.get(VoiceTrace.Fact.OUTPUT_QUALITY)))
                throw new AssertionError("Playback boundary must be explicitly identified");
            return "Native silent-output smoke passed: route warmup excluded, response submission and real Android playback-head progress observed; no acoustic Echo measurement.\n";
        }finally{output.close();}
    }
}
