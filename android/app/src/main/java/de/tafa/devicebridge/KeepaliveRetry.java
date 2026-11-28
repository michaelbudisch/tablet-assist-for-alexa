package de.tafa.devicebridge;

/** Bounded, deterministic backoff for a silent Bluetooth keepalive stream. */
final class KeepaliveRetry {
    private KeepaliveRetry() {}
    static long delayMs(int failedAttempts) {
        return Math.min(30000L, Math.max(1, failedAttempts) * 3000L);
    }
}
