package de.jarvis.audio;

import java.io.IOException;
import java.io.InterruptedIOException;

/** At most two seconds of decoded audio, with producer backpressure and cancellation wakeups. */
final class PcmBuffer {
    private byte[] bytes;
    private int head, size;
    private boolean ended, cancelled;
    private IOException error;
    private PcmFormat format;
    int peak;
    synchronized void configure(PcmFormat value) throws IOException {
        check();
        if(format!=null){if(!format.same(value))throw new IOException("stream_format_changed");return;}
        format=value; bytes=new byte[value.bytesForMs(2000)]; notifyAll();
    }
    synchronized PcmFormat awaitFormat() throws IOException,InterruptedException {
        while(format==null&&!ended){check();wait(100);}
        check(); if(format==null)throw new IOException("empty_audio");return format;
    }
    synchronized void put(byte[] source,int offset,int length)throws IOException,InterruptedException {
        if(format==null||length%format.frameBytes!=0)throw new IOException("invalid_pcm_alignment");
        while(length>0){
            check();while(size==bytes.length){wait(100);check();}
            int amount=Math.min(length,Math.min(bytes.length-size,bytes.length-(head+size)%bytes.length));
            System.arraycopy(source,offset,bytes,(head+size)%bytes.length,amount);
            offset+=amount;length-=amount;size+=amount;peak=Math.max(peak,size);notifyAll();
        }
    }
    synchronized int poll(byte[] target)throws IOException {
        check();if(size==0)return ended?-1:0;
        int amount=Math.min(size,target.length);amount-=amount%format.frameBytes;
        int first=Math.min(amount,bytes.length-head);
        System.arraycopy(bytes,head,target,0,first);
        if(first<amount)System.arraycopy(bytes,0,target,first,amount-first);
        head=(head+amount)%bytes.length;size-=amount;notifyAll();return amount;
    }
    synchronized void awaitInitial(int minimum)throws IOException,InterruptedException {
        while(size<minimum&&!ended){check();wait(100);}check();
    }
    synchronized int size()throws IOException{check();return size;}
    synchronized boolean ended()throws IOException{check();return ended;}
    synchronized void awaitChange(long millis)throws IOException,InterruptedException{check();wait(millis);check();}
    synchronized void finish(){ended=true;notifyAll();}
    synchronized void fail(IOException value){error=value;notifyAll();}
    synchronized void cancel(){cancelled=true;notifyAll();}
    private void check()throws IOException{if(cancelled)throw new InterruptedIOException("cancelled");if(error!=null)throw error;}
}
