package de.jarvis.audio;

import org.junit.Test;
import static org.junit.Assert.*;

public class WakePilotMultiroomTest {
    @Test public void eachTabletHasSeparateEntities() {
        for (int slot=1;slot<=4;slot++) {
            assertEquals("input_boolean.jarvis_wake_tablet_"+slot+"_stumm",
                WakePilotSettings.entity("muted",slot));
            assertEquals("input_select.jarvis_wake_tablet_"+slot+"_rufwort",
                WakePilotSettings.entity("word",slot));
            assertEquals("input_number.jarvis_wake_tablet_"+slot+"_strenge",
                WakePilotSettings.entity("strict",slot));
            assertEquals("input_number.jarvis_wake_tablet_"+slot+"_sperrzeit",
                WakePilotSettings.entity("cooldown",slot));
            assertEquals("input_number.jarvis_wake_tablet_"+slot+"_ubergabe",
                WakePilotSettings.entity("hold",slot));
            assertEquals("input_text.jarvis_wake_tablet_"+slot+"_geratekennung",
                WakePilotSettings.entity("owner",slot));
        }
        assertNotEquals(WakePilotSettings.entity("muted",1),WakePilotSettings.entity("muted",2));
    }

    @Test public void rejectsOutOfRangeSlotsAndUnknownKeys() {
        try{WakePilotSettings.entity("muted",0);fail("slot 0 accepted");}
        catch(IllegalArgumentException expected){}
        try{WakePilotSettings.entity("muted",5);fail("slot 5 accepted");}
        catch(IllegalArgumentException expected){}
        try{WakePilotSettings.entity("bad",2);fail("unknown key accepted");}
        catch(IllegalArgumentException expected){}
    }
}
