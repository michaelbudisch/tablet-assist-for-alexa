package de.tafa.devicebridge;

import java.io.*;
import java.net.*;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class StreamingSessionTest {
    static class SplitBody extends InputStream {
        final byte[] data; final int split;
        final CountDownLatch release=new CountDownLatch(1);
        volatile boolean eof,closed;int position;
        SplitBody(byte[] data,int split){this.data=data;this.split=split;}
        public int read()throws IOException{byte[] b=new byte[1];return read(b,0,1)<0?-1:b[0]&255;}
        public int read(byte[] b,int off,int len)throws IOException{
            if(position>=split&&!eof&&!closed&&release.getCount()>0)try{
                if(!release.await(3,TimeUnit.SECONDS))throw new IOException("test_body_gate_timeout");
            }catch(InterruptedException e){throw new InterruptedIOException();}
            if(closed)throw new IOException("closed");
            if(position==data.length){eof=true;return -1;}
            int amount=Math.min(len,(position<split?split:data.length)-position);
            System.arraycopy(data,position,b,off,amount);position+=amount;return amount;
        }
        public void close(){closed=true;release.countDown();}
    }
    static class Connection extends HttpURLConnection {
        final InputStream body;final int code;volatile boolean disconnected;
        Connection(InputStream body,int code)throws Exception{super(new URL("https://test.invalid/"));this.body=body;this.code=code;}
        public int getResponseCode(){return code;}
        public InputStream getInputStream(){return body;}
        public void connect(){}
        public boolean usingProxy(){return false;}
        public void disconnect(){disconnected=true;try{body.close();}catch(IOException ignored){}}
    }
    static class Sink implements StreamingSession.Output {
        final ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        volatile boolean aborted,closed;boolean refuse;
        public void open(PcmFormat format)throws IOException{if(refuse)throw new IOException("error_route_unconfirmed");}
        public void write(byte[] b,int offset,int length)throws IOException{if(aborted)throw new IOException("cancelled");bytes.write(b,offset,length);}
        public void silence(int millis)throws InterruptedException{Thread.sleep(1);}
        public long queuedMillis(){return 100;}
        public void drain(){}
        public void abort(){aborted=true;}
        public void close(){abort();closed=true;}
    }
    static class Events implements StreamingSession.Listener {
        final CountDownLatch playing=new CountDownLatch(1),terminal=new CountDownLatch(1);
        volatile String error,diagnostics;volatile File fallback;
        public void onPlaying(String value){diagnostics=value;playing.countDown();}
        public void onBuffering(String value){diagnostics=value;}
        public void onDone(String value){diagnostics=value;terminal.countDown();}
        public void onFallback(File file,String value){fallback=file;diagnostics=value;terminal.countDown();}
        public void onError(String code,String value){error=code;diagnostics=value;terminal.countDown();}
    }
    private StreamingSession session(File dir,Connection c,Sink sink,Events events){
        return new StreamingSession(dir,()->c,first->{throw new AudioStreamReader.Unsupported();},stopped->sink,events);
    }
    private void clean(File dir){File[] files=dir.listFiles();if(files!=null)for(File file:files)file.delete();dir.delete();}

    @Test public void startsBeforeResponseEofWithoutDroppingOrRepeatingPcm()throws Exception {
        File dir=Files.createTempDirectory("relay-stream-test").toFile();
        byte[] pcm=new byte[24000*2*3];for(int i=0;i<pcm.length;i++)pcm[i]=(byte)(i*7);
        SplitBody body=new SplitBody(AudioStreamReaderTest.wav(pcm,24000,1,0),44+24000*2);
        Sink sink=new Sink();Events events=new Events();StreamingSession stream=session(dir,new Connection(body,200),sink,events);
        try{
            stream.start();assertTrue("Playback must begin while the server is still holding back the rest",events.playing.await(2,TimeUnit.SECONDS));
            assertFalse(body.eof);body.release.countDown();assertTrue(events.terminal.await(3,TimeUnit.SECONDS));
            assertNull(events.error);assertNull(events.fallback);assertTrue(stream.awaitStopped(2000));
            assertArrayEquals("Every speech byte must reach the sink exactly once",pcm,sink.bytes.toByteArray());
            assertEquals(0,dir.list().length);
        }finally{stream.cancel();stream.awaitStopped(2000);clean(dir);}
    }
    @Test public void unconfirmedRouteEmitsNoSpeech()throws Exception {
        File dir=Files.createTempDirectory("relay-route-test").toFile();
        byte[] pcm=new byte[48000];SplitBody body=new SplitBody(AudioStreamReaderTest.wav(pcm,24000,1,0),44+48000);
        Sink sink=new Sink();sink.refuse=true;Events events=new Events();Connection c=new Connection(body,200);
        StreamingSession stream=session(dir,c,sink,events);
        try{
            stream.start();assertTrue(events.terminal.await(2,TimeUnit.SECONDS));assertEquals("error_route_unconfirmed",events.error);
            assertEquals(0,sink.bytes.size());
        }finally{stream.cancel();assertTrue(stream.awaitStopped(2000));clean(dir);}
    }
    @Test public void cancelInterruptsAnIncompleteNetworkResponseAndRemovesCache()throws Exception {
        File dir=Files.createTempDirectory("relay-cancel-test").toFile();
        SplitBody body=new SplitBody(AudioStreamReaderTest.wav(new byte[144000],24000,1,0),44+48000);
        Sink sink=new Sink();Events events=new Events();Connection c=new Connection(body,200);
        StreamingSession stream=session(dir,c,sink,events);
        try{
            stream.start();assertTrue(events.playing.await(2,TimeUnit.SECONDS));stream.cancel();
            assertTrue("Streaming threads stop promptly",stream.awaitStopped(1500));assertTrue("Output is muted or released",sink.aborted);
            assertTrue("Network connection closes",c.disconnected);assertEquals(0,dir.list().length);
        }finally{stream.cancel();clean(dir);}
    }
    @Test public void unsupportedFormatFallsBackToSameResponseOnlyBeforeSpeech()throws Exception {
        File dir=Files.createTempDirectory("relay-fallback-test").toFile();
        byte[] opaque="OggS valid-other-format-placeholder".getBytes("US-ASCII");
        Sink sink=new Sink();Events events=new Events();Connection c=new Connection(new ByteArrayInputStream(opaque),200);
        StreamingSession stream=session(dir,c,sink,events);
        try{
            stream.start();assertTrue(events.terminal.await(2,TimeUnit.SECONDS));assertNotNull(events.fallback);assertNull(events.error);
            assertArrayEquals(opaque,Files.readAllBytes(events.fallback.toPath()));assertEquals(0,sink.bytes.size());
        }finally{stream.cancel();stream.awaitStopped(2000);clean(dir);}
    }
    @Test public void rejectsRedirectResponsesInsteadOfSendingCredentialsElsewhere()throws Exception {
        File dir=Files.createTempDirectory("relay-http-test").toFile();Sink sink=new Sink();Events events=new Events();
        StreamingSession stream=session(dir,new Connection(new ByteArrayInputStream(new byte[0]),302),sink,events);
        try{stream.start();assertTrue(events.terminal.await(2,TimeUnit.SECONDS));assertEquals("error_stream_http",events.error);assertEquals(0,sink.bytes.size());}
        finally{stream.cancel();stream.awaitStopped(2000);clean(dir);}
    }
    @Test public void decoderFailureAfterSpeechNeverReplaysThroughFallback()throws Exception {
        File dir=Files.createTempDirectory("relay-no-replay-test").toFile();
        byte[] frame=AudioStreamReader.Mp3Frame.header(AudioStreamReaderTest.header(2,8,1,0,1)).bytes;
        ByteArrayOutputStream encoded=new ByteArrayOutputStream();encoded.write(frame);encoded.write(frame);
        SplitBody body=new SplitBody(encoded.toByteArray(),frame.length);
        Connection c=new Connection(body,200);Sink sink=new Sink();Events events=new Events();
        StreamingSession stream=new StreamingSession(dir,()->c,first->new AudioStreamReader.Mp3Decoder(){
            int frames;
            public void frame(AudioStreamReader.Mp3Frame frame,AudioStreamReader.PcmConsumer output)throws Exception {
                if(frames++>0)throw new AudioStreamReader.Unsupported();
                byte[] pcm=new byte[48000];Arrays.fill(pcm,(byte)9);output.accept(new PcmFormat(24000,1),pcm,0,pcm.length);
            }
            public void end(AudioStreamReader.PcmConsumer output){}
            public void close(){}
        },stopped->sink,events);
        try{
            stream.start();assertTrue(events.playing.await(2,TimeUnit.SECONDS));body.release.countDown();
            assertTrue(events.terminal.await(2,TimeUnit.SECONDS));assertNull("No fallback after any speech",events.fallback);
            assertEquals("error_stream_format_changed",events.error);
            assertTrue(sink.bytes.size()>0&&sink.bytes.size()<=48000);
        }finally{stream.cancel();stream.awaitStopped(2000);clean(dir);}
    }
    @Test public void boundedPcmQueueWakesBlockedProducerOnCancel()throws Exception {
        PcmFormat format=new PcmFormat(8000,1);PcmBuffer queue=new PcmBuffer();queue.configure(format);
        queue.put(new byte[format.bytesForMs(2000)],0,format.bytesForMs(2000));
        ExecutorService worker=Executors.newSingleThreadExecutor();
        try{
            Future<?> blocked=worker.submit(()->{try{queue.put(new byte[2],0,2);throw new AssertionError("must not exceed buffer capacity");}catch(IOException|InterruptedException expected){}});
            queue.cancel();blocked.get(1,TimeUnit.SECONDS);
        }finally{worker.shutdownNow();}
    }
}
