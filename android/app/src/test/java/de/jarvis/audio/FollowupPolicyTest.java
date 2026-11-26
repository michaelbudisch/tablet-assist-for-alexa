package de.jarvis.audio;
import org.junit.Test;
import static org.junit.Assert.*;

public class FollowupPolicyTest {
    @Test public void freshAndMigratedDevicesRequireWakeword() {
        assertEquals(0, FollowupPolicy.effectiveLimit(0, -1));
        assertFalse(FollowupPolicy.shouldContinue(true, 0, 0));
        assertFalse(FollowupPolicy.shouldContinue(true, 0, -1));
    }
    @Test public void eachLimitAllowsExactlyThatManyAdditionalQuestions() {
        for (int configured = 0; configured <= 10; configured++) {
            int used = 0;
            int limit = FollowupPolicy.effectiveLimit(configured, -1);
            while (FollowupPolicy.shouldContinue(true, used, limit)) {
                used++;
                assertTrue("Never exceed local maximum", used <= 10);
            }
            assertEquals(configured, used);
        }
    }
    @Test public void homeAssistantCanOnlyReduceTheLocalCeiling() {
        assertEquals(2, FollowupPolicy.effectiveLimit(2, 100));
        assertEquals(2, FollowupPolicy.effectiveLimit(2, -1));
        assertEquals(1, FollowupPolicy.effectiveLimit(10, 1));
        assertEquals(0, FollowupPolicy.effectiveLimit(10, 0));
        assertEquals(0, FollowupPolicy.effectiveLimit(10, -2));
    }
    @Test public void pendingFollowupMustRecheckChangedSettings() {
        assertTrue(FollowupPolicy.shouldContinue(true, 0, FollowupPolicy.effectiveLimit(5, -1)));
        assertFalse(FollowupPolicy.shouldContinue(true, 0, FollowupPolicy.effectiveLimit(0, -1)));
        assertFalse(FollowupPolicy.shouldContinue(true, 2, FollowupPolicy.effectiveLimit(2, -1)));
    }
    @Test public void silenceAndFailedRepliesEndConversation() {
        for (int limit = 0; limit <= 10; limit++)
            assertFalse(FollowupPolicy.shouldContinue(false, 0, limit));
        assertFalse(FollowupPolicy.shouldContinue(true, -1, 10));
    }
    @Test public void corruptPreferencesCannotEnableUnlimitedListening() {
        assertEquals(0, FollowupPolicy.localLimit(-1));
        assertEquals(10, FollowupPolicy.localLimit(Integer.MAX_VALUE));
        assertFalse(FollowupPolicy.shouldContinue(true, 10, 100));
    }
}
