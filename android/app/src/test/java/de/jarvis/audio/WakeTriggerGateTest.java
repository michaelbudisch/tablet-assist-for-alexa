package de.jarvis.audio;

import org.junit.Test;
import static org.junit.Assert.*;

public class WakeTriggerGateTest {
    @Test public void sensitivityOneIsImmediate() {
        WakeTriggerGate g=new WakeTriggerGate();
        assertTrue(g.confirm("Hey Jarvis",1));
    }
    @Test public void strictnessTwoRequiresTwoConfirmations() {
        WakeTriggerGate g=new WakeTriggerGate();
        assertFalse(g.confirm("Hey Jarvis",2));
        assertTrue(g.confirm("Hey Jarvis",2));
    }
    @Test public void strictnessThreeResetsOnMismatch() {
        WakeTriggerGate g=new WakeTriggerGate();
        assertFalse(g.confirm("Jarvis",3));
        assertFalse(g.confirm("Alexa",3));
        assertFalse(g.confirm("Alexa",3));
        assertTrue(g.confirm("Alexa",3));
        g.reset();
        assertFalse(g.confirm("Alexa",3));
        assertFalse(g.confirm(null,3));
        assertFalse(g.confirm("Alexa",3));
    }
}
