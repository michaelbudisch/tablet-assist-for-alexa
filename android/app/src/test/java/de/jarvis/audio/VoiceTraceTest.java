package de.jarvis.audio;

import org.junit.Test;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import static org.junit.Assert.*;
import static de.jarvis.audio.VoiceTrace.Point.*;

public class VoiceTraceTest {
    final AtomicLong clock=new AtomicLong(1_000_000_000L);
    void time(long millis){clock.set(1_000_000_000L+millis*1_000_000L);}
    VoiceTrace trace(){return new VoiceTrace("sample",VoiceTrace.Kind.WAKEWORD,clock::get,123);}
    @Test public void missingMeasurementsAreNotZeroOrEstimated(){
        VoiceTrace t=trace();time(100);t.mark(OUTPUT_SUBMITTED);
        assertNull(t.snapshot().between(SPEECH_END,OUTPUT_PROGRESS));
        assertNull(t.snapshot().between(TRIGGER,OUTPUT_PROGRESS));
        assertEquals(100.0,t.snapshot().between(TRIGGER,OUTPUT_SUBMITTED),0.001);
    }
    @Test public void lastVoicedFrameSeparatesSpeechFromEndpointPause(){
        VoiceTrace t=trace();time(20);t.mark(SPEECH_START);
        time(400);t.mark(SPEECH_END);time(500);t.mark(SPEECH_END);
        time(2200);t.mark(CAPTURE_END);time(3000);t.mark(OUTPUT_PROGRESS);
        assertEquals(1700.0,t.snapshot().between(SPEECH_END,CAPTURE_END),0.001);
        assertEquals(2500.0,t.snapshot().between(SPEECH_END,OUTPUT_PROGRESS),0.001);
    }
    @Test public void duplicateEventsDoNotMoveTheFirstOutput(){
        VoiceTrace t=trace();time(100);t.mark(OUTPUT_PROGRESS);
        time(300);t.mark(OUTPUT_PROGRESS);
        assertEquals(100.0,t.snapshot().between(TRIGGER,OUTPUT_PROGRESS),0.001);
    }
    @Test public void playbackBeforeSubmitResponseKeepsOriginalDeviceTimestamp(){
        VoiceTrace.Store store=new VoiceTrace.Store(clock::get);
        VoiceTrace t=store.begin(VoiceTrace.Kind.MANUAL,123);
        VoiceTrace.Playback p=store.playback("a".repeat(32));
        time(50);p.mark(JOB_RECEIVED);time(150);p.mark(OUTPUT_PROGRESS);
        time(300);assertTrue(store.bind(t,"a".repeat(32)));
        assertEquals(150.0,t.snapshot().between(TRIGGER,OUTPUT_PROGRESS),0.001);
        assertEquals(50.0,t.snapshot().between(TRIGGER,JOB_RECEIVED),0.001);
    }
    @Test public void unrelatedJobAndAnotherRequestCannotContaminateTrace(){
        VoiceTrace.Store store=new VoiceTrace.Store(clock::get);
        VoiceTrace a=store.begin(VoiceTrace.Kind.WAKEWORD,1);
        VoiceTrace b=store.begin(VoiceTrace.Kind.FOLLOWUP,1);
        store.playback("b".repeat(32)).mark(OUTPUT_PROGRESS);
        assertTrue(store.bind(a,"a".repeat(32)));
        assertFalse(store.bind(b,"a".repeat(32)));
        time(80);store.playback("a".repeat(32)).mark(OUTPUT_PROGRESS);
        assertNull(b.snapshot().between(TRIGGER,OUTPUT_PROGRESS));
        assertEquals(80.0,a.snapshot().between(TRIGGER,OUTPUT_PROGRESS),0.001);
    }
    @Test public void clearRetiresActiveAndUnboundCallbacks(){
        VoiceTrace.Store store=new VoiceTrace.Store(clock::get);
        VoiceTrace t=store.begin(VoiceTrace.Kind.WAKEWORD,1);
        VoiceTrace.Playback p=store.playback("a".repeat(32));
        store.clear();time(80);p.mark(OUTPUT_PROGRESS);t.mark(STT_END);
        assertFalse(store.bind(t,"a".repeat(32)));
        t.finish(VoiceTrace.Status.SUCCESS,"");
        assertTrue(store.snapshots().isEmpty());
    }
    @Test public void disablingInterruptsMeasurementWithoutRestartingIt(){
        VoiceTrace.Store store=new VoiceTrace.Store(clock::get);
        VoiceTrace t=store.begin(VoiceTrace.Kind.WAKEWORD,1);
        store.enabled(false);t.finish(VoiceTrace.Status.SUCCESS,"");
        store.begin(VoiceTrace.Kind.MANUAL,1);
        assertEquals(1,store.snapshots().size());
        assertEquals(VoiceTrace.Status.INTERRUPTED,store.snapshots().get(0).status);
        store.enabled(true);store.begin(VoiceTrace.Kind.MANUAL,2);
        assertEquals(2,store.snapshots().size());
    }
    @Test public void historiesAndUnboundJobBuffersAreBounded(){
        VoiceTrace.Store store=new VoiceTrace.Store(clock::get);
        VoiceTrace first=store.begin(VoiceTrace.Kind.WAKEWORD,0);
        for(int i=0;i<100;i++){
            store.begin(VoiceTrace.Kind.MANUAL,i);
            store.playback(String.format("%032x",i)).mark(FIRST_BYTE);
        }
        assertEquals(20,store.snapshots().size());
        first.finish(VoiceTrace.Status.SUCCESS,"");
        assertEquals(20,store.snapshots().size());
    }
    @Test public void terminalOutcomeIsStableAndLateProgressIsIgnored(){
        VoiceTrace t=trace();time(10);t.finish(VoiceTrace.Status.ERROR,"audio_ioexception");
        time(20);t.mark(OUTPUT_PROGRESS);t.finish(VoiceTrace.Status.SUCCESS,"");
        assertEquals(VoiceTrace.Status.ERROR,t.snapshot().status);
        assertEquals("audio_ioexception",t.snapshot().error);
        assertNull(t.snapshot().between(TRIGGER,OUTPUT_PROGRESS));
    }
    @Test public void arbitraryContentCannotEnterExportableFactsOrErrors(){
        VoiceTrace t=trace();
        t.fact(VoiceTrace.Fact.OUTPUT,"https://server/api?token=secret");
        t.finish(VoiceTrace.Status.ERROR,"https://server/secret");
        assertTrue(t.snapshot().facts.isEmpty());
        assertEquals("error",t.snapshot().error);
    }
    @Test public void clockRegressionIsNotDisplayedAsNegativeLatency(){
        VoiceTrace t=trace();clock.set(0);t.mark(STT_END);
        assertFalse(t.snapshot().points.containsKey(STT_END));
    }
    @Test public void recoveryNeverPresentsAnInterruptedRunAsSuccessful(){
        VoiceTrace t=trace();time(20);t.mark(STT_START);
        VoiceTrace restored=VoiceTrace.restore(t.snapshot(),clock::get);
        restored.finish(VoiceTrace.Status.SUCCESS,"");
        assertEquals(VoiceTrace.Status.INTERRUPTED,restored.snapshot().status);
    }
    @Test public void silentRouteWarmupCannotCountAsResponsePresentation(){
        VoiceTrace.PresentationGate gate=new VoiceTrace.PresentationGate();
        assertFalse(gate.observe(500));
        gate.routeVerified();
        assertFalse(gate.waiting());
        assertFalse(gate.observe(1000));
        assertTrue(gate.submitted(1000));
        assertTrue(gate.waiting());
        assertFalse(gate.observe(999));
        assertFalse(gate.observe(1000));
        assertTrue(gate.observe(1001));
        assertFalse(gate.observe(2000));
        assertFalse(gate.submitted(3000));
    }
    @Test public void submittedFramesStillRequireVerifiedOutput(){
        VoiceTrace.PresentationGate gate=new VoiceTrace.PresentationGate();
        gate.submitted(0);
        assertFalse(gate.observe(200));
        gate.routeVerified();
        assertTrue(gate.observe(200));
    }
    @Test public void percentileInterpolationKeepsSmallSampleCountHonest(){
        List<Double> values=Arrays.asList(100.0,200.0,300.0,400.0);
        assertEquals(250.0,VoiceTrace.percentile(values,.5),0.001);
        assertEquals(385.0,VoiceTrace.percentile(values,.95),0.001);
        assertEquals(100.0,values.get(0),0.001);
    }
}
