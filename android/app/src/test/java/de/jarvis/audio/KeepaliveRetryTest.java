package de.jarvis.audio;
import org.junit.Test;
import static org.junit.Assert.*;

public class KeepaliveRetryTest {
    @Test public void boundedIncreasingDelay() {
        assertEquals(3000L, KeepaliveRetry.delayMs(1));
        assertEquals(6000L, KeepaliveRetry.delayMs(2));
        assertEquals(15000L, KeepaliveRetry.delayMs(5));
        assertEquals(30000L, KeepaliveRetry.delayMs(10));
        assertEquals(30000L, KeepaliveRetry.delayMs(100));
        assertEquals(3000L, KeepaliveRetry.delayMs(0));
    }
}
