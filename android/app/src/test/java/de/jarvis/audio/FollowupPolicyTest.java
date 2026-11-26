package de.jarvis.audio;
import org.junit.Test;
import static org.junit.Assert.*;

public class FollowupPolicyTest {
    @Test public void zeroDisablesFollowups() {
        assertFalse(FollowupPolicy.shouldContinue(true,0,0));
    }
    @Test public void customLimitsAreNotHardCappedAtThree() {
        assertTrue(FollowupPolicy.shouldContinue(true,3,10));
        assertTrue(FollowupPolicy.shouldContinue(true,9,10));
        assertFalse(FollowupPolicy.shouldContinue(true,10,10));
        assertTrue(FollowupPolicy.shouldContinue(true,49,100));
    }
    @Test public void unlimitedEndsOnSilence() {
        assertTrue(FollowupPolicy.shouldContinue(true,1000,-1));
        assertFalse(FollowupPolicy.shouldContinue(false,1000,-1));
    }
    @Test public void ordinaryReplyEndsOnNoAnswer() {
        assertFalse(FollowupPolicy.shouldContinue(false,0,5));
        assertFalse(FollowupPolicy.shouldContinue(false,5,5));
    }
}
