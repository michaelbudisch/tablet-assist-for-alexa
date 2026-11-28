package de.tafa.devicebridge;

import java.util.concurrent.Executor;

/**
 * Latest-value, non-blocking voice phase publisher.
 *
 * Android never waits for Home Assistant on the microphone or UI thread.
 * A slow network request may coalesce intermediate phases, but the latest
 * state is always delivered after the in-flight request completes.
 */
final class WakePhaseReporter {
    interface Sender {
        void send(String phase);
    }

    private final Executor executor;
    private final Sender sender;
    private String pending;
    private String pendingWake;
    private boolean active;
    private boolean closed;

    WakePhaseReporter(Executor executor, Sender sender) {
        if (executor == null || sender == null) throw new IllegalArgumentException("executor/sender");
        this.executor = executor;
        this.sender = sender;
    }

    synchronized void submit(String phase) {
        if (closed || phase == null || phase.isEmpty()) return;
        // Never lose the edge that marks actual wakeword detection.
        // Native connecting/listening stages can change before the worker
        // starts, but the wake marker must still reach HA first.
        if (phase.startsWith("detected:")) pendingWake = phase;
        else pending = phase;
        if (active) return;
        active = true;
        try {
            executor.execute(this::drain);
        } catch (RuntimeException rejected) {
            active = false;
            pending = null;
            pendingWake = null;
        }
    }

    private void drain() {
        while (true) {
            final String phase;
            synchronized (this) {
                if (closed || (pending == null && pendingWake == null)) {
                    active = false;
                    return;
                }
                if (pendingWake != null) {
                    phase = pendingWake;
                    pendingWake = null;
                } else {
                    phase = pending;
                    pending = null;
                }
            }
            try {
                sender.send(phase);
            } catch (RuntimeException ignored) {
                // Telemetry is best effort; the regular status sync retries.
            }
        }
    }

    synchronized void close() {
        closed = true;
        pending = null;
        pendingWake = null;
    }
}
