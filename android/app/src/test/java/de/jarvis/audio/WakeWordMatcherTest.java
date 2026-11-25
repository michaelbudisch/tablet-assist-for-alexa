package de.jarvis.audio;

import org.junit.Test;
import static org.junit.Assert.*;

public class WakeWordMatcherTest {
    @Test public void separatesWakeWords() {
        assertEquals("Hey Jarvis", WakeWordMatcher.matched("Hey Jarvis", "hey_jarvis"));
        assertNull(WakeWordMatcher.matched("Jarvis", "hey_jarvis"));
        assertEquals("Jarvis", WakeWordMatcher.matched("Jarvis", "jarvis"));
        assertEquals("Alexa", WakeWordMatcher.matched("Alexa", "alexa"));
        assertNull(WakeWordMatcher.matched("Alexa", "jarvis"));
    }
    @Test public void allModeAndBoundaries() {
        assertEquals("Hey Jarvis", WakeWordMatcher.matched("hey jarvis", "all"));
        assertEquals("Alexa", WakeWordMatcher.matched("Alexa, bitte", "all"));
        assertNull(WakeWordMatcher.matched("Alexandra", "all"));
        assertNull(WakeWordMatcher.matched("ein Jarvisianer", "all"));
        assertEquals("Jarvis", WakeWordMatcher.matched("jaRWiS", "jarvis"));
    }
}
