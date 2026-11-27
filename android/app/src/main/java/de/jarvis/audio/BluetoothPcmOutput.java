package de.jarvis.audio;

import android.media.*;
import android.os.Handler;
import android.os.Looper;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.function.BooleanSupplier;

/** Warm up with zeros, then stream real PCM only over a verified and continuously monitored output route. */
final class BluetoothPcmOutput implements StreamingSession.Output {
    private final AudioManager manager;
    private final BooleanSupplier stopped;
    private final String mode;
    private volatile int outputType;
    String routeLabel(){return AudioOutputMode.label(outputType);}
    private final Object trackLock=new Object();
    private volatile AudioTrack track;
    private volatile boolean aborted,routeLost;
    private volatile int confirmed=-1;
    private PcmFormat format;
    private long writtenFrames;
    private final VoiceTrace.PresentationGate presentation=new VoiceTrace.PresentationGate();
    private final VoiceTrace.Playback probe;
    private ByteBuffer transfer;
    BluetoothPcmOutput(AudioManager manager,BooleanSupplier stopped){this(manager,stopped,AudioOutputMode.BLUETOOTH);}
    BluetoothPcmOutput(AudioManager manager,BooleanSupplier stopped,String mode){this(manager,stopped,mode,null);}
    BluetoothPcmOutput(AudioManager manager,BooleanSupplier stopped,String mode,VoiceTrace.Playback probe){
        this.manager=manager;this.stopped=stopped;this.mode=mode;this.probe=probe;
        outputType=AudioOutputMode.select(manager,mode);
    }

    private AudioDeviceInfo outputDevice(){return AudioOutputMode.find(manager,outputType);}
    private boolean routed(){
        AudioTrack current=track;if(current==null)return false;
        try{
            AudioDeviceInfo device=current.getRoutedDevice();
            return device!=null&&device.getType()==outputType&&(confirmed<0||confirmed==device.getId());
        }catch(RuntimeException closing){return false;}
    }
    private void check()throws IOException {
        if(routeLost)throw new IOException("error_route_lost");
        if(aborted||stopped.getAsBoolean()||Thread.currentThread().isInterrupted())throw new IOException("cancelled");
    }
    private void verify()throws IOException {
        check();if(!routed()){routeLost=true;abort();throw new IOException("error_route_lost");}
    }
    private void prefer(){
        AudioDeviceInfo device=outputDevice();AudioTrack current=track;
        if(device!=null&&current!=null)try{current.setPreferredDevice(device);}catch(RuntimeException ignored){}
    }

    @Override public void open(PcmFormat format)throws Exception {
        this.format=format;check();
        if(outputDevice()==null&&AudioOutputMode.AUTO.equals(mode))outputType=AudioOutputMode.select(manager,mode);
        if(outputDevice()==null)throw new IOException("error_route_unavailable");
        int mask=format.channels==1?AudioFormat.CHANNEL_OUT_MONO:AudioFormat.CHANNEL_OUT_STEREO;
        int minimum=AudioTrack.getMinBufferSize(format.sampleRate,mask,AudioFormat.ENCODING_PCM_16BIT);
        if(minimum<0)throw new IOException("error_stream_output_format");
        int capacity=Math.max(minimum,format.bytesForMs(100));
        track=new AudioTrack.Builder().setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
                .setAudioFormat(new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(format.sampleRate).setChannelMask(mask).build())
                .setTransferMode(AudioTrack.MODE_STREAM).setBufferSizeInBytes(capacity).build();
        if(track.getState()!=AudioTrack.STATE_INITIALIZED)throw new IOException("error_stream_output_init");
        transfer=ByteBuffer.allocateDirect(Math.max(capacity,format.bytesForMs(20)));
        track.setVolume(0);prefer();
        track.addOnRoutingChangedListener(router->{
            if(confirmed>=0&&track!=null&&!routed()){routeLost=true;abort();}
        },new Handler(Looper.getMainLooper()));
        // Only zero samples can reach any output while the real route is still unknown.
        byte[] zeros=new byte[capacity];
        transfer.clear();transfer.put(zeros);transfer.flip();
        int initial=track.write(transfer,transfer.remaining(),AudioTrack.WRITE_NON_BLOCKING);
        if(initial<0)throw new IOException("error_stream_output_write");
        writtenFrames+=initial/format.frameBytes;
        check();track.play();
        long start=System.nanoTime(),retry=start+500_000_000L;
        int attempts=1;
        while(!routed()){
            check();long now=System.nanoTime();
            if(AudioOutputMode.AUTO.equals(mode)&&outputType==AudioDeviceInfo.TYPE_BLUETOOTH_A2DP&&
                    (AudioOutputMode.find(manager,outputType)==null||now-start>1_500_000_000L)){
                outputType=AudioDeviceInfo.TYPE_BUILTIN_SPEAKER;prefer();start=now;retry=now+500_000_000L;attempts=1;
            }
            if(now-start>4_000_000_000L)throw new IOException("error_route_unconfirmed");
            if(now>=retry&&attempts<3){prefer();attempts++;retry=now+500_000_000L;}
            // Retain the playback session without consuming the beginning of the answer.
            transfer.clear();transfer.put(zeros,0,Math.min(zeros.length,format.bytesForMs(20)));transfer.flip();
            int count=track.write(transfer,transfer.remaining(),AudioTrack.WRITE_NON_BLOCKING);
            if(count<0)throw new IOException("error_stream_output_write");
            writtenFrames+=count/format.frameBytes;
            Thread.sleep(20);
        }
        AudioDeviceInfo verified=track.getRoutedDevice();
        if(verified==null)throw new IOException("error_route_unconfirmed");
        confirmed=verified.getId();verify();track.setVolume(1);
        presentation.routeVerified();
        if(probe!=null){probe.fact(VoiceTrace.Fact.OUTPUT,routeLabel());probe.mark(VoiceTrace.Point.ROUTE_READY);}
    }

    @Override public void write(byte[] bytes,int offset,int length)throws Exception {
        verify();transfer.clear();transfer.put(bytes,offset,length);transfer.flip();
        long deadline=System.nanoTime()+2_000_000_000L;
        while(transfer.hasRemaining()){
            verify();int count;
            synchronized(trackLock){check();count=track.write(transfer,transfer.remaining(),AudioTrack.WRITE_NON_BLOCKING);}
            if(count<0)throw new IOException("error_stream_output_write");
            if(count>0&&presentation.submitted(writtenFrames)&&probe!=null)
                probe.mark(VoiceTrace.Point.OUTPUT_SUBMITTED);
            writtenFrames+=count/format.frameBytes;
            observeProgress();
            if(count==0){if(System.nanoTime()>deadline)throw new IOException("error_stream_output_stalled");Thread.sleep(5);}
        }
    }
    @Override public void silence(int millis)throws Exception {
        byte[] zeros=new byte[format.bytesForMs(Math.min(20,millis))];
        for(int left=millis;left>0;left-=20)write(zeros,0,Math.min(zeros.length,format.bytesForMs(left)));
    }
    /** Observe played frames, never equate a write() return with presentation. */
    private void observeProgress(){
        AudioTrack current=track;
        if(probe==null||!presentation.waiting()||current==null||aborted||routeLost)return;
        try{
            if(current.getPlayState()==AudioTrack.PLAYSTATE_PLAYING&&
                    presentation.observe(current.getPlaybackHeadPosition()&0xffffffffL)){
                probe.fact(VoiceTrace.Fact.OUTPUT_QUALITY,"audiotrack_head");
                probe.mark(VoiceTrace.Point.OUTPUT_PROGRESS);
            }
        }catch(RuntimeException ignored){/* Diagnostics must not alter playback. */}
    }
    @Override public long queuedMillis(){
        observeProgress();
        AudioTrack current=track;if(current==null||format==null)return 0;
        try{return Math.max(0,writtenFrames-(current.getPlaybackHeadPosition()&0xffffffffL))*1000/format.sampleRate;}
        catch(RuntimeException error){return 0;}
    }
    @Override public void drain()throws Exception {
        silence(100);
        long deadline=System.nanoTime()+5_000_000_000L;
        while((track.getPlaybackHeadPosition()&0xffffffffL)<writtenFrames){
            verify();observeProgress();if(System.nanoTime()>deadline)throw new IOException("error_stream_output_stalled");Thread.sleep(10);
        }
        observeProgress();
        if(probe!=null)probe.fact(VoiceTrace.Fact.UNDERRUNS,track.getUnderrunCount());
    }
    @Override public void abort(){
        aborted=true;
        synchronized(trackLock){AudioTrack current=track;if(current!=null)try{current.setVolume(0);current.pause();}catch(RuntimeException ignored){}}
    }
    @Override public void close(){
        abort();
        synchronized(trackLock){AudioTrack current=track;track=null;confirmed=-1;if(current!=null)current.release();}
    }
}
