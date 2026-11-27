package de.jarvis.audio;

import org.junit.Test;
import static org.junit.Assert.*;

public class NativeSpeechEndpointTest {
    private static short[] frame(int value){
        short[] a=new short[320];
        java.util.Arrays.fill(a,(short)value);
        return a;
    }
    @Test public void emptyMicStopsWithoutInventingWords(){
        NativeSpeechEndpoint vad=new NativeSpeechEndpoint(1700,8000);
        for(int i=0;i<399;i++)assertEquals(NativeSpeechEndpoint.Decision.CONTINUE,vad.feed(frame(0),320));
        assertEquals(NativeSpeechEndpoint.Decision.EMPTY,vad.feed(frame(0),320));
        assertFalse(vad.hasSpeech());
    }
    @Test public void speechWithThinkingPauseIsNotCutOff(){
        NativeSpeechEndpoint vad=new NativeSpeechEndpoint(1700,8000);
        for(int i=0;i<20;i++)assertEquals(NativeSpeechEndpoint.Decision.CONTINUE,vad.feed(frame(1500),320));
        for(int i=0;i<50;i++)assertEquals(NativeSpeechEndpoint.Decision.CONTINUE,vad.feed(frame(0),320));
        for(int i=0;i<20;i++)assertEquals(NativeSpeechEndpoint.Decision.CONTINUE,vad.feed(frame(1500),320));
        for(int i=0;i<84;i++)assertEquals(NativeSpeechEndpoint.Decision.CONTINUE,vad.feed(frame(0),320));
        assertEquals(NativeSpeechEndpoint.Decision.END,vad.feed(frame(0),320));
        assertTrue(vad.hasSpeech());
    }
    @Test public void followupStopsAfterThreeSecondsOfSilence(){
        NativeSpeechEndpoint vad=new NativeSpeechEndpoint(1700,3000,true);
        for(int i=0;i<149;i++)assertEquals(NativeSpeechEndpoint.Decision.CONTINUE,vad.feed(frame(0),320));
        assertEquals(NativeSpeechEndpoint.Decision.EMPTY,vad.feed(frame(0),320));
        assertFalse(vad.hasSpeech());
    }
    @Test public void quietBackgroundNoiseDoesNotBecomeSpeechInFollowup(){
        NativeSpeechEndpoint vad=new NativeSpeechEndpoint(1700,3000,true);
        for(int i=0;i<149;i++)assertEquals(NativeSpeechEndpoint.Decision.CONTINUE,vad.feed(frame(250),320));
        assertEquals(NativeSpeechEndpoint.Decision.EMPTY,vad.feed(frame(250),320));
    }
    @Test public void veryLongFollowupIsCappedAtTenSeconds(){
        NativeSpeechEndpoint vad=new NativeSpeechEndpoint(1700,3000,true);
        for(int i=0;i<499;i++)vad.feed(frame(1800),320);
        assertEquals(NativeSpeechEndpoint.Decision.LIMIT,vad.feed(frame(1800),320));
    }
    @Test public void maxDurationTerminatesContinuousInput(){
        NativeSpeechEndpoint vad=new NativeSpeechEndpoint(1700,8000);
        for(int i=0;i<1249;i++)vad.feed(frame(2000),320);
        assertEquals(NativeSpeechEndpoint.Decision.LIMIT,vad.feed(frame(2000),320));
    }
}