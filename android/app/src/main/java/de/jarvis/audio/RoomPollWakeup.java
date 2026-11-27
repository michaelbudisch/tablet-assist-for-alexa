package de.jarvis.audio;

import java.util.concurrent.Executor;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BooleanSupplier;

/** Coalesces explicit job-ready signals onto the existing serial room executor. */
final class RoomPollWakeup {
    private final Executor executor;
    private final BooleanSupplier ready;
    private final Runnable poll;
    private final AtomicBoolean pending=new AtomicBoolean();
    RoomPollWakeup(Executor executor,BooleanSupplier ready,Runnable poll){
        this.executor=executor;this.ready=ready;this.poll=poll;
    }
    void request(){
        if(!pending.compareAndSet(false,true))return;
        try{
            executor.execute(()->{
                pending.set(false);
                if(ready.getAsBoolean())poll.run();
            });
        }catch(RejectedExecutionException stopped){pending.set(false);}
    }
}
