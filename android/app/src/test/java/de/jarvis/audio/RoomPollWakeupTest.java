package de.jarvis.audio;

import org.junit.Test;
import java.util.ArrayDeque;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.Assert.*;

public class RoomPollWakeupTest {
    @Test public void acceptedJobSchedulesImmediateWorkAndCoalescesDuplicates(){
        ArrayDeque<Runnable> queue=new ArrayDeque<>();
        AtomicInteger polls=new AtomicInteger();
        RoomPollWakeup wake=new RoomPollWakeup(queue::add,()->true,polls::incrementAndGet);
        wake.request();wake.request();wake.request();
        assertEquals(1,queue.size());assertEquals(0,polls.get());
        queue.remove().run();assertEquals(1,polls.get());
        wake.request();assertEquals(1,queue.size());
        queue.remove().run();assertEquals(2,polls.get());
    }
    @Test public void stoppingBeforeQueuedSignalExecutesNeverPollsOrReconnects(){
        ArrayDeque<Runnable> queue=new ArrayDeque<>();
        AtomicBoolean active=new AtomicBoolean(true);
        AtomicInteger polls=new AtomicInteger();
        RoomPollWakeup wake=new RoomPollWakeup(queue::add,active::get,polls::incrementAndGet);
        wake.request();active.set(false);queue.remove().run();
        assertEquals(0,polls.get());
    }
    @Test public void busyPlayerSkipsSignalAndCompletionCanRequestNextJob(){
        ArrayDeque<Runnable> queue=new ArrayDeque<>();
        AtomicBoolean busy=new AtomicBoolean(true);
        AtomicInteger polls=new AtomicInteger();
        RoomPollWakeup wake=new RoomPollWakeup(queue::add,()->!busy.get(),polls::incrementAndGet);
        wake.request();queue.remove().run();assertEquals(0,polls.get());
        busy.set(false);wake.request();queue.remove().run();assertEquals(1,polls.get());
    }
    @Test public void executorShutdownDoesNotCrashOrLeavePendingFlagStuck(){
        AtomicInteger attempts=new AtomicInteger();
        RoomPollWakeup wake=new RoomPollWakeup(r->{
            attempts.incrementAndGet();throw new RejectedExecutionException();
        },()->true,()->fail("Stopped player must not poll"));
        wake.request();wake.request();assertEquals(2,attempts.get());
    }
    @Test public void signalDuringPollQueuesAtMostOneNextPoll(){
        ArrayDeque<Runnable> queue=new ArrayDeque<>();
        RoomPollWakeup[] wake=new RoomPollWakeup[1];
        AtomicInteger polls=new AtomicInteger();
        wake[0]=new RoomPollWakeup(queue::add,()->true,()->{
            if(polls.incrementAndGet()==1){wake[0].request();wake[0].request();}
        });
        wake[0].request();queue.remove().run();
        assertEquals(1,queue.size());queue.remove().run();
        assertEquals(2,polls.get());assertTrue(queue.isEmpty());
    }
}
