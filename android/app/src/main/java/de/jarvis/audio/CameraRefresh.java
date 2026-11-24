package de.jarvis.audio;

/** Bounded refresh preference for explicitly started JPEG delivery. */
final class CameraRefresh {
    static final String KEY = "camera_refresh_seconds";
    static final int DEFAULT = 2;
    static final int MIN_UPLOAD_GAP_MS = 500;
    static final int ERROR_RETRY_MS = 5000;
    private static final int[] OPTIONS = {1, 2, 3, 5, 10};

    static int[] options() { return OPTIONS.clone(); }

    static int normalize(int seconds) {
        for (int option : OPTIONS) if (seconds == option) return seconds;
        return DEFAULT;
    }

    static long nextDelay(int seconds, long elapsedMs, boolean success) {
        if (!success) return ERROR_RETRY_MS;
        return Math.max(MIN_UPLOAD_GAP_MS, normalize(seconds) * 1000L - Math.max(0L, elapsedMs));
    }

    private CameraRefresh() {}
}
