package de.jarvis.audio;
import org.junit.Test;
import static org.junit.Assert.*;

public class FollowupPolicyTest {
    @Test public void defaultAndLegacyFiniteLimits(){
        assertEquals(0,FollowupPolicy.effectiveLimit(0,-1));
        assertFalse(FollowupPolicy.shouldContinue(true,0,0));
        for(int n=1;n<=10;n++){
            assertTrue(FollowupPolicy.shouldContinue(true,n-1,n));
            assertFalse(FollowupPolicy.shouldContinue(true,n,n));
        }
    }
    @Test public void optInUnlimitedUntilSilenceOrError(){
        assertEquals(-1,FollowupPolicy.localLimit(-1));
        assertEquals(-1,FollowupPolicy.effectiveLimit(-1,-1));
        assertTrue(FollowupPolicy.shouldContinue(true,1000,-1));
        assertFalse(FollowupPolicy.shouldContinue(false,0,-1));
        assertFalse(FollowupPolicy.shouldContinue(true,-1,-1));
    }
    @Test public void homeAssistantCanOnlyLimit(){
        assertEquals(2,FollowupPolicy.effectiveLimit(20,2));
        assertEquals(20,FollowupPolicy.effectiveLimit(20,-1));
        assertEquals(100,FollowupPolicy.effectiveLimit(-1,100));
        assertEquals(0,FollowupPolicy.effectiveLimit(-1,0));
        assertFalse(FollowupPolicy.shouldContinue(true,2,
            FollowupPolicy.effectiveLimit(-1,2)));
    }
    @Test public void invalidValuesCannotEnableUnlimited(){
        assertEquals(0,FollowupPolicy.localLimit(-20));
        assertEquals(100,FollowupPolicy.localLimit(Integer.MAX_VALUE));
        assertFalse(FollowupPolicy.shouldContinue(true,100,100));
    }
}
