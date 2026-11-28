package de.jarvis.audio;

import java.io.*;
import java.net.HttpURLConnection;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BooleanSupplier;

/** One cancellable response: network/decoder producer and bounded PCM playback consumer. */
final class StreamingSession {
    static final int START_BUFFER_MS = 600;
    static final long MAX_BYTES = 24L * 1024 * 1024;
    interface ConnectionFactory { HttpURLConnection open() throws Exception; }
    interface Output extends AutoCloseable {
        /** Must verify the real route using only silence before returning. */
        void open(PcmFormat format) throws Exception;
        void write(byte[] bytes,int offset,int length) throws Exception;
        void silence(int millis) throws Exception;
        long queuedMillis();
        void drain() throws Exception;
        /** Thread-safe: mute immediately, even if a network read or decoder is blocked. */
        void abort();
        void close();
    }
    interface OutputFactory { Output create(BooleanSupplier stopped); }
    interface Listener {
        default void timing(VoiceTrace.Point point){}
        default void metric(VoiceTrace.Fact fact,long value){}
        void onPlaying(String diagnostics);
        void onBuffering(String diagnostics);
        void onDone(String diagnostics);
        void onFallback(File file,String diagnostics);
        void onError(String error,String diagnostics);
    }
    private final ConnectionFactory connections;
    private final AudioStreamReader.DecoderFactory decoders;
    private final OutputFactory outputs;
    private final Listener listener;
    private final File cacheDir;
    private final PcmBuffer queue = new PcmBuffer();
    private final Object soundLock = new Object();
    private final CountDownLatch outputClosed = new CountDownLatch(1);
    private final AtomicBoolean terminal = new AtomicBoolean();
    private final long started = System.nanoTime();
    private volatile boolean cancelled, fallback, stopSound;
    private boolean heard;
    private volatile HttpURLConnection connection;
    private volatile InputStream body;
    private volatile Output output;
    private Thread producer, consumer;
    private volatile long firstByteMs=-1, firstPcmMs=-1, firstPlayMs=-1, received;
    private volatile int rebuffers;
    private volatile String mode="preparing";

    StreamingSession(File cacheDir,ConnectionFactory connections,AudioStreamReader.DecoderFactory decoders,
                     OutputFactory outputs,Listener listener) {
        this.cacheDir=cacheDir;this.connections=connections;this.decoders=decoders;this.outputs=outputs;this.listener=listener;
    }
    void start() {
        consumer=new Thread(this::consume,"relay-pcm-output");
        producer=new Thread(this::produce,"relay-stream-decode");
        consumer.start();producer.start();
    }
    boolean soundStopped(){return cancelled||stopSound;}
    void cancel() {
        cancelled=true;stopSound=true;terminal.set(true);queue.cancel();
        Output current=output;if(current!=null)current.abort();
        if(producer!=null)producer.interrupt();if(consumer!=null)consumer.interrupt();
        // HttpURLConnection.close/disconnect may block on an OEM client; never do that on Android's UI thread.
        Thread closer=new Thread(this::closeConnection,"relay-stream-cancel");closer.setDaemon(true);closer.start();
    }
    boolean awaitStopped(long millis)throws InterruptedException {
        long deadline=System.nanoTime()+TimeUnit.MILLISECONDS.toNanos(millis);
        if(producer!=null)producer.join(millis);
        long remaining=Math.max(0,TimeUnit.NANOSECONDS.toMillis(deadline-System.nanoTime()));
        if(consumer!=null&&remaining>0)consumer.join(remaining);
        return (producer==null||!producer.isAlive())&&(consumer==null||!consumer.isAlive());
    }
    String diagnostics(){return "mode="+mode+"; first_byte_ms="+firstByteMs+"; first_pcm_ms="+firstPcmMs
            +"; first_submit_ms="+firstPlayMs+"; received_bytes="+received+"; rebuffer_count="+rebuffers;}
    private long elapsed(){return TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-started);}
    private void check()throws IOException {
        if(cancelled||Thread.currentThread().isInterrupted())throw new InterruptedIOException("cancelled");
        if(elapsed()>120000)throw new IOException("error_stream_timeout");
    }

    private void produce() {
        File spool=null;
        FileOutputStream disk=null;
        BufferedInputStream input=null;
        boolean transfer=false, complete=false;
        Exception failure=null;
        try {
            listener.timing(VoiceTrace.Point.FETCH_START);
            check();connection=connections.open();check();
            int status=connection.getResponseCode();
            listener.timing(VoiceTrace.Point.HTTP_READY);
            if(status!=200)throw new IOException(status==401||status==403?"error_stream_auth":"error_stream_http");
            if(connection.getContentLengthLong()>MAX_BYTES)throw new IOException("error_stream_size");
            spool=File.createTempFile("tafa-",".audio",cacheDir);
            disk=new FileOutputStream(spool);
            body=connection.getInputStream();
            final FileOutputStream destination=disk;
            InputStream tee=new FilterInputStream(body) {
                private int saved(byte[] bytes,int offset,int count)throws IOException {
                    check();if(count>0){
                        if(received+count>MAX_BYTES)throw new IOException("error_stream_size");
                        if(firstByteMs<0){firstByteMs=elapsed();listener.timing(VoiceTrace.Point.FIRST_BYTE);}received+=count;destination.write(bytes,offset,count);
                    }return count;
                }
                @Override public int read(byte[] bytes,int offset,int length)throws IOException {check();return saved(bytes,offset,in.read(bytes,offset,length));}
                @Override public int read()throws IOException {byte[] one=new byte[1];int n=read(one,0,1);return n<0?-1:one[0]&255;}
            };
            input=new BufferedInputStream(tee,16384);
            final long[] decoded={0};
            AudioStreamReader.PcmConsumer pcm=(format,bytes,offset,length)->{
                check();if(stopSound)throw new InterruptedIOException("cancelled");
                if(firstPcmMs<0){firstPcmMs=elapsed();listener.timing(VoiceTrace.Point.FIRST_PCM);}
                if(mode.equals("preparing"))mode="wav_pcm";
                decoded[0]+=length;
                if(decoded[0]>(long)format.bytesForMs(1000)*120)throw new IOException("error_stream_duration");
                queue.configure(format);queue.put(bytes,offset,length);
            };
            try {
                AudioStreamReader.decode(input,pcm,first->{mode="mp3";return decoders.create(first);});
                if(decoded[0]==0)throw new IOException("error_stream_empty");
                complete=true;
            } catch(AudioStreamReader.Unsupported unsupported) {
                synchronized(soundLock){
                    if(heard)throw new IOException("error_stream_format_changed",unsupported);
                    fallback=true;stopSound=true;
                }
                queue.cancel();Output current=output;if(current!=null)current.abort();
                outputClosed.await(2,TimeUnit.SECONDS);
                mode="file_fallback";
                byte[] rest=new byte[16384];while(input.read(rest)!=-1)check();
                if(received==0)throw new IOException("error_stream_empty");
                transfer=true;
            }
        }catch(Exception error){failure=error;}
        finally{
            if(input!=null)try{input.close();}catch(IOException ignored){}
            if(disk!=null)try{disk.close();}catch(IOException ignored){}
            closeConnection();
            if(transfer&&!cancelled&&failure==null&&terminal.compareAndSet(false,true))listener.onFallback(spool,diagnostics());
            else if(spool!=null)spool.delete();
            if(complete&&!cancelled)queue.finish();
            else if(failure!=null&&!cancelled){
                fail(failure);
            }
        }
    }

    private void consume() {
        Output sink=null;
        try{
            PcmFormat format=queue.awaitFormat();
            int threshold=format.bytesForMs(START_BUFFER_MS);
            queue.awaitInitial(threshold);check();
            if(queue.size()==0)throw new IOException("error_stream_empty");
            if(soundStopped())return;
            listener.timing(VoiceTrace.Point.BUFFER_READY);
            sink=outputs.create(this::soundStopped);output=sink;
            sink.open(format);
            listener.timing(VoiceTrace.Point.ROUTE_READY);
            byte[] block=new byte[Math.max(format.frameBytes,format.bytesForMs(20))];
            boolean announce=true;
            while(!soundStopped()){
                check();int count=queue.poll(block);
                if(count<0){sink.drain();listener.timing(VoiceTrace.Point.PLAYBACK_END);if(!cancelled&&terminal.compareAndSet(false,true))listener.onDone(diagnostics());return;}
                if(count>0){
                    synchronized(soundLock){
                        if(soundStopped())return;
                        sink.write(block,0,count);heard=true;if(firstPlayMs<0){firstPlayMs=elapsed();listener.timing(VoiceTrace.Point.OUTPUT_SUBMITTED);}
                    }
                    if(announce){listener.onPlaying(diagnostics());announce=false;}
                }else if(sink.queuedMillis()>40){queue.awaitChange(15);}
                else{
                    rebuffers++;listener.metric(VoiceTrace.Fact.REBUFFERS,rebuffers);announce=true;listener.onBuffering(diagnostics());
                    while(!soundStopped()&&!queue.ended()&&queue.size()<threshold){
                        check();sink.silence(20);queue.awaitChange(10);
                    }
                }
            }
        }catch(Exception error){if(!cancelled&&!fallback)fail(error);}
        finally{if(sink!=null)sink.close();output=null;outputClosed.countDown();}
    }

    private void fail(Exception error){
        String code=error.getMessage();
        if(code==null||!code.matches("error_[a-z0-9_]{1,90}"))code="error_stream_decode";
        boolean firstFailure=terminal.compareAndSet(false,true);
        stopSound=true;
        Output current=output;if(current!=null)current.abort();
        // Preserve the cause while waking the peer; secondary shutdown errors cannot replace it.
        queue.fail(new IOException(code,error));
        if(firstFailure){
            listener.onError(code,diagnostics());
            if(producer!=null&&producer!=Thread.currentThread())producer.interrupt();
            Thread closer=new Thread(this::closeConnection,"relay-stream-failure");closer.setDaemon(true);closer.start();
        }
    }
    private void closeConnection(){
        HttpURLConnection current=connection;
        if(current!=null){try{current.disconnect();}catch(RuntimeException ignored){}}
        InputStream stream=body;if(stream!=null)try{stream.close();}catch(IOException ignored){}
    }
}
