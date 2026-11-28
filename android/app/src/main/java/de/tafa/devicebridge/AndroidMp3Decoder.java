package de.tafa.devicebridge;

import android.media.AudioFormat;
import android.media.MediaCodec;
import android.media.MediaFormat;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.function.BooleanSupplier;

/** Feed complete MP3 frames into Android's platform decoder; emit PCM incrementally. */
final class AndroidMp3Decoder implements AudioStreamReader.Mp3Decoder {
    private final MediaCodec codec;
    private final BooleanSupplier stopped;
    private PcmFormat format;
    private long samples;
    private boolean eos;
    AndroidMp3Decoder(AudioStreamReader.Mp3Frame first,BooleanSupplier stopped)throws AudioStreamReader.Unsupported {
        this.stopped=stopped;
        MediaCodec created=null;
        try{
            format=new PcmFormat(first.sampleRate,first.channels);
            MediaFormat input=MediaFormat.createAudioFormat("audio/mpeg",first.sampleRate,first.channels);
            input.setInteger(MediaFormat.KEY_MAX_INPUT_SIZE,4096);
            input.setInteger(MediaFormat.KEY_PCM_ENCODING,AudioFormat.ENCODING_PCM_16BIT);
            created=MediaCodec.createDecoderByType("audio/mpeg");
            created.configure(input,null,null,0);created.start();codec=created;
        }catch(Exception error){if(created!=null)try{created.release();}catch(RuntimeException ignored){}throw new AudioStreamReader.Unsupported(error);}
    }
    private void check()throws IOException{if(stopped.getAsBoolean()||Thread.currentThread().isInterrupted())throw new IOException("cancelled");}
    @Override public void frame(AudioStreamReader.Mp3Frame frame,AudioStreamReader.PcmConsumer output)throws Exception {
        int index;
        while((index=codec.dequeueInputBuffer(10000))<0){check();drain(output,false);}
        check();ByteBuffer buffer=codec.getInputBuffer(index);
        if(buffer==null||buffer.capacity()<frame.bytes.length)throw new IOException("error_stream_decoder_buffer");
        buffer.clear();buffer.put(frame.bytes);
        codec.queueInputBuffer(index,0,frame.bytes.length,samples*1000000L/frame.sampleRate,0);
        samples+=frame.samples;drain(output,false);
    }
    @Override public void end(AudioStreamReader.PcmConsumer output)throws Exception {
        int index;
        while((index=codec.dequeueInputBuffer(10000))<0){check();drain(output,false);}
        codec.queueInputBuffer(index,0,0,samples*1000000L/format.sampleRate,MediaCodec.BUFFER_FLAG_END_OF_STREAM);
        long deadline=System.nanoTime()+5_000_000_000L;
        while(!eos){check();drain(output,true);if(System.nanoTime()>deadline)throw new IOException("error_stream_decoder_timeout");}
    }
    private void drain(AudioStreamReader.PcmConsumer output,boolean ending)throws Exception {
        MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();
        while(true){
            check();int index=codec.dequeueOutputBuffer(info,ending?10000:0);
            if(index==MediaCodec.INFO_TRY_AGAIN_LATER)return;
            if(index==MediaCodec.INFO_OUTPUT_FORMAT_CHANGED){
                MediaFormat value=codec.getOutputFormat();
                if(value.containsKey(MediaFormat.KEY_PCM_ENCODING)&&value.getInteger(MediaFormat.KEY_PCM_ENCODING)!=AudioFormat.ENCODING_PCM_16BIT)
                    throw new AudioStreamReader.Unsupported();
                format=new PcmFormat(value.getInteger(MediaFormat.KEY_SAMPLE_RATE),value.getInteger(MediaFormat.KEY_CHANNEL_COUNT));
            }else if(index>=0){
                try{
                    if(info.size>0&&(info.flags&MediaCodec.BUFFER_FLAG_CODEC_CONFIG)==0){
                        if(info.size>1024*1024)throw new IOException("error_stream_decoder_buffer");
                        ByteBuffer buffer=codec.getOutputBuffer(index);
                        if(buffer==null)throw new IOException("error_stream_decoder_buffer");
                        buffer.position(info.offset);buffer.limit(info.offset+info.size);
                        byte[] pcm=new byte[info.size];buffer.get(pcm);output.accept(format,pcm,0,pcm.length);
                    }
                    if((info.flags&MediaCodec.BUFFER_FLAG_END_OF_STREAM)!=0)eos=true;
                }finally{codec.releaseOutputBuffer(index,false);}
            }
        }
    }
    @Override public void close(){try{codec.stop();}catch(RuntimeException ignored){}codec.release();}
}
