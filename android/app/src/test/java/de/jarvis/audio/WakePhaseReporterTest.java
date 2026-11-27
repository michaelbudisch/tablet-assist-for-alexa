package de.jarvis.audio;

import org.junit.Test;
import static org.junit.Assert.*;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executor;

public class WakePhaseReporterTest {
    @Test public void burstPublishesLatestPhaseWithoutQueueingManyRequests() {
        List<Runnable> tasks = new ArrayList<>();
        List<String> sent = new ArrayList<>();
        WakePhaseReporter reporter = new WakePhaseReporter(tasks::add, sent::add);
        reporter.submit("detected: hey jarvis");
        reporter.submit("native_connecting");
        reporter.submit("native_listening");
        assertEquals(1, tasks.size());
        tasks.remove(0).run();
        assertEquals(2, sent.size());
        assertEquals("detected: hey jarvis", sent.get(0));
        assertEquals("native_listening", sent.get(1));
    }

    @Test public void phaseChangeDuringSendIsDeliveredRightAfterward() {
        List<Runnable> tasks = new ArrayList<>();
        List<String> sent = new ArrayList<>();
        final WakePhaseReporter[] ref = new WakePhaseReporter[1];
        ref[0] = new WakePhaseReporter(tasks::add, value -> {
            sent.add(value);
            if ("native_listening".equals(value)) ref[0].submit("native_thinking");
        });
        ref[0].submit("native_listening");
        tasks.remove(0).run();
        assertEquals(2, sent.size());
        assertEquals("native_listening", sent.get(0));
        assertEquals("native_thinking", sent.get(1));
        assertTrue(tasks.isEmpty());
    }

    @Test public void closeDropsPendingWork() {
        List<Runnable> tasks = new ArrayList<>();
        List<String> sent = new ArrayList<>();
        WakePhaseReporter reporter = new WakePhaseReporter(tasks::add, sent::add);
        reporter.submit("native_playing");
        reporter.close();
        tasks.remove(0).run();
        reporter.submit("listening: hey_jarvis");
        assertTrue(sent.isEmpty());
        assertTrue(tasks.isEmpty());
    }

    @Test public void failedPublishDoesNotBlockNewStatus() {
        List<Runnable> tasks = new ArrayList<>();
        List<String> sent = new ArrayList<>();
        WakePhaseReporter reporter = new WakePhaseReporter(tasks::add, value -> {
            if ("native_connecting".equals(value)) throw new IllegalStateException("offline");
            sent.add(value);
        });
        reporter.submit("native_connecting");
        tasks.remove(0).run();
        reporter.submit("native_thinking");
        tasks.remove(0).run();
        assertEquals(1, sent.size());
        assertEquals("native_thinking", sent.get(0));
    }
}
