package de.tafa.devicebridge;

import android.app.Instrumentation;
import android.media.AudioManager;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Real Android MP3 decoder + real chunked HTTP, with a recording sink instead of a physical speaker. */
final class StreamingSmoke {
    private static void check(boolean condition,String message){if(!condition)throw new AssertionError(message);}
    static String run(Instrumentation instrumentation)throws Exception {
        StringBuilder report=new StringBuilder();
        for(String name:new String[]{"stream-24000-1.mp3","stream-44100-2.mp3","stream-24000-1.wav"}){
            byte[] source;
            try(InputStream input=instrumentation.getContext().getAssets().open(name)){
                ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] b=new byte[4096];int n;
                while((n=input.read(b))!=-1)bytes.write(b,0,n);source=bytes.toByteArray();
            }
            ByteArrayOutputStream reference=new ByteArrayOutputStream();
            AudioStreamReader.decode(new BufferedInputStream(new ByteArrayInputStream(source)),
                    (format,b,off,len)->reference.write(b,off,len),first->new AndroidMp3Decoder(first,()->false));
            check(reference.size()>48000,"Fixture decoded into real PCM: "+name);
            boolean nonzero=false;for(byte value:reference.toByteArray())if(value!=0){nonzero=true;break;}
            check(nonzero,"Fixture must contain a non-silent synthetic signal");
            int prefix=name.endsWith(".wav")?48044:name.contains("44100")?24000:12000;
            RecordingOutput sink=new RecordingOutput();Events events=new Events();
            try(SlowServer server=new SlowServer(source,prefix)){
                StreamingSession session=new StreamingSession(instrumentation.getTargetContext().getCacheDir(),
                        ()->open(server.port()),first->new AndroidMp3Decoder(first,()->false),stopped->sink,events);
                long start=System.nanoTime();
                try{
                    session.start();
                    check(events.playing.await(6,TimeUnit.SECONDS),"Streaming must start before the server releases the tail: "+name+"; "+events.error);
                    long first=(System.nanoTime()-start)/1_000_000;
                    check(!server.finished,"Playback occurred before complete HTTP response");
                    server.tail.countDown();
                    check(events.done.await(8,TimeUnit.SECONDS),"Stream finished: "+name);
                    check(events.error==null,"No decoder/network error: "+events.error);
                    check(events.fallback==null,"Supported MP3/WAV used streaming, not file fallback");
                    check(session.awaitStopped(2000),"Stream workers released");
                    check(Arrays.equals(reference.toByteArray(),sink.bytes.toByteArray()),"All decoded PCM reached output exactly once: "+name);
                    check(server.failure==null,"HTTP server error: "+server.failure);
                    report.append(name).append(": early_playback=true; first_submit_ms=").append(first)
                            .append("; decoded_bytes=").append(reference.size()).append("; ").append(events.diagnostic).append('\n');
                }finally{session.cancel();session.awaitStopped(2000);}
            }
        }
        // A stalled response must be abortable while the real Android HTTP stack is blocked in a read.
        byte[] stalled=new byte[48000];
        stalled[0]=(byte)0xff;stalled[1]=(byte)0xf3;stalled[2]=(byte)0x84;stalled[3]=(byte)0xc0;
        try(SlowServer server=new SlowServer(stalled,4)){
            Events events=new Events();RecordingOutput sink=new RecordingOutput();
            StreamingSession session=new StreamingSession(instrumentation.getTargetContext().getCacheDir(),
                    ()->open(server.port()),first->new AndroidMp3Decoder(first,()->false),stopped->sink,events);
            try{
                session.start();check(server.prefixSent.await(4,TimeUnit.SECONDS),"Stalled response opened");
                session.cancel();check(session.awaitStopped(2000),"Cancellation aborts a blocked native HTTP read");
                check(sink.bytes.size()==0,"Cancellation during header buffering emits no PCM");
            }finally{session.cancel();}
        }
        BluetoothPcmOutput bluetooth=new BluetoothPcmOutput(instrumentation.getTargetContext().getSystemService(AudioManager.class),()->false);
        try{
            boolean rejected=false;
            try{bluetooth.open(new PcmFormat(24000,1));}catch(IOException expected){rejected=true;}
            check(rejected,"Emulator without A2DP rejects real output before speech");
        }finally{bluetooth.close();}
        report.append("Native cancellation and no-Bluetooth guard passed.\n");
        return report.toString();
    }
    private static HttpURLConnection open(int port)throws Exception {
        HttpURLConnection connection=(HttpURLConnection)new URL("http://127.0.0.1:"+port+"/test.mp3").openConnection();
        connection.setConnectTimeout(2000);connection.setReadTimeout(10000);connection.setInstanceFollowRedirects(false);
        connection.setRequestProperty("Authorization","Bearer test-only-fixture");return connection;
    }
    static final class RecordingOutput implements StreamingSession.Output {
        final ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        public void open(PcmFormat format){}
        public void write(byte[] b,int offset,int length){bytes.write(b,offset,length);}
        public void silence(int millis)throws Exception{Thread.sleep(1);}
        public long queuedMillis(){return 100;}
        public void drain(){}
        public void abort(){}
        public void close(){}
    }
    static final class Events implements StreamingSession.Listener {
        final CountDownLatch playing=new CountDownLatch(1),done=new CountDownLatch(1);
        volatile String error,diagnostic;volatile File fallback;
        public void onPlaying(String value){diagnostic=value;playing.countDown();}
        public void onBuffering(String value){diagnostic=value;}
        public void onDone(String value){diagnostic=value;done.countDown();}
        public void onFallback(File file,String value){fallback=file;diagnostic=value;file.delete();done.countDown();}
        public void onError(String code,String value){error=code;diagnostic=value;done.countDown();}
    }
    static final class SlowServer implements AutoCloseable {
        final ServerSocket listener;
        final CountDownLatch tail=new CountDownLatch(1),prefixSent=new CountDownLatch(1);
        final Thread worker;
        volatile boolean finished,closing;
        volatile Exception failure;
        volatile Socket client;
        SlowServer(byte[] bytes,int first)throws Exception {
            listener=new ServerSocket(0,1,InetAddress.getByName("127.0.0.1"));
            worker=new Thread(()->{
                try(Socket socket=listener.accept()){
                    client=socket;socket.setSoTimeout(5000);
                    BufferedReader request=new BufferedReader(new InputStreamReader(socket.getInputStream(),StandardCharsets.US_ASCII));
                    boolean authorized=false;String line;
                    while((line=request.readLine())!=null&&!line.isEmpty())if(line.equalsIgnoreCase("Authorization: Bearer test-only-fixture"))authorized=true;
                    if(!authorized)throw new IOException("test_authorization_header_missing");
                    OutputStream output=socket.getOutputStream();
                    output.write("HTTP/1.1 200 OK\r\nContent-Type: audio/mpeg\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n".getBytes(StandardCharsets.US_ASCII));
                    int prefix=Math.min(first,bytes.length);chunk(output,bytes,0,prefix);prefixSent.countDown();
                    if(!tail.await(8,TimeUnit.SECONDS))throw new IOException("test_tail_gate_timeout");
                    for(int offset=prefix;offset<bytes.length;offset+=4096){
                        chunk(output,bytes,offset,Math.min(4096,bytes.length-offset));Thread.sleep(25);
                    }
                    finished=true;output.write("0\r\n\r\n".getBytes(StandardCharsets.US_ASCII));output.flush();
                }catch(Exception error){if(!closing)failure=error;}
            },"relay-test-http");worker.start();
        }
        int port(){return listener.getLocalPort();}
        private void chunk(OutputStream output,byte[] bytes,int offset,int length)throws IOException {
            output.write((Integer.toHexString(length)+"\r\n").getBytes(StandardCharsets.US_ASCII));output.write(bytes,offset,length);
            output.write("\r\n".getBytes(StandardCharsets.US_ASCII));output.flush();
        }
        public void close()throws Exception{closing=true;tail.countDown();if(client!=null)client.close();listener.close();worker.join(1000);}
    }
    private StreamingSmoke(){}
}
