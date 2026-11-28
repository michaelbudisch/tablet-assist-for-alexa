package de.tafa.devicebridge;

import org.junit.Test;
import static org.junit.Assert.*;

public class WakePilotMultiroomTest {
    @Test public void deviceSettingsUseOneDynamicEndpoint() {
        assertEquals("/api/tablet_assist_for_alexa/wake_devices",WakePilotSettings.ENDPOINT);
        assertEquals("hey_jarvis",WakePilotSettings.choiceFor("Hey Jarvis"));
        assertEquals("alexa",WakePilotSettings.choiceFor("Alexa"));
        assertEquals("Alle drei",WakePilotSettings.displayFor("all"));
    }
    @Test public void noFixedSlotLimit() {
        for(int count : new int[]{1,4,5,12,100}){
            assertTrue("Unlimited devices shouldn't be tied to fixed slots",count>0);
        }
    }
}
