package de.tafa.devicebridge;

import org.junit.Test;
import static org.junit.Assert.*;
import java.util.Arrays;

public class ContinuousSpeechTriggerTest {
    static short[] frame(int level){
        short[] pcm=new short[320];Arrays.fill(pcm,(short)level);return pcm;
    }
    @Test public void silenceAndShortClicksDoNotStartAssist(){
        var trigger=new ContinuousSpeechTrigger();
        for(int i=0;i<200;i++)assertFalse(trigger.feed(frame(0),320));
        for(int i=0;i<8;i++)assertFalse(trigger.feed(frame(2000),320));
        for(int i=0;i<50;i++)assertFalse(trigger.feed(frame(0),320));
    }
    @Test public void sustainedSpeechTriggersLocally(){
        var trigger=new ContinuousSpeechTrigger();
        for(int i=0;i<14;i++)assertFalse(trigger.feed(frame(2200),320));
        assertTrue(trigger.feed(frame(2200),320));
    }
    @Test public void recoveryAfterSilence(){
        var trigger=new ContinuousSpeechTrigger();
        for(int i=0;i<10;i++)assertFalse(trigger.feed(frame(2100),320));
        assertFalse(trigger.feed(frame(0),320));
        for(int i=0;i<14;i++)assertFalse(trigger.feed(frame(2100),320));
        assertTrue(trigger.feed(frame(2100),320));
    }
}