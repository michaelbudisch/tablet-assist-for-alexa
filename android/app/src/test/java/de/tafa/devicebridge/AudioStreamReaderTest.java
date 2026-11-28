package de.tafa.devicebridge;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import org.junit.Test;
import static org.junit.Assert.*;

public class AudioStreamReaderTest {
    static byte[] wav(byte[] pcm,int rate,int channels,long length) throws IOException {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        bytes.write("RIFF".getBytes("US-ASCII"));
        bytes.write(ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(0).array());
        bytes.write("WAVEfmt ".getBytes("US-ASCII"));
        bytes.write(ByteBuffer.allocate(24).order(ByteOrder.LITTLE_ENDIAN).putInt(16).putShort((short)1)
                .putShort((short)channels).putInt(rate).putInt(rate*channels*2).putShort((short)(channels*2)).putShort((short)16)
                .putInt(0x61746164).array());
        bytes.write(ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt((int)length).array());
        bytes.write(pcm);return bytes.toByteArray();
    }
    static byte[] header(int version,int bitrate,int rate,int padding,int channels) {
        int word=0xffe00000|(version<<19)|(1<<17)|(1<<16)|(bitrate<<12)|(rate<<10)|(padding<<9)|((channels==1?3:0)<<6);
        return ByteBuffer.allocate(4).putInt(word).array();
    }
    @Test public void wavHandlesArbitraryNetworkSplitsAndUnknownLengths()throws Exception {
        byte[] pcm=new byte[8012];for(int i=0;i<pcm.length;i++)pcm[i]=(byte)i;
        for(long length:new long[]{0,0xffffffffL,pcm.length}){
            ByteArrayOutputStream actual=new ByteArrayOutputStream();
            InputStream fragmented=new FilterInputStream(new ByteArrayInputStream(wav(pcm,24000,2,length))){
                public int read(byte[] b,int off,int len)throws IOException{return super.read(b,off,Math.min(len,3));}
            };
            AudioStreamReader.wav(fragmented,(format,b,off,len)->{
                assertEquals(24000,format.sampleRate);assertEquals(2,format.channels);actual.write(b,off,len);
            });
            assertArrayEquals(pcm,actual.toByteArray());
        }
    }
    @Test public void wavRejectsIncompleteFramesAndDeclaredTruncation()throws Exception {
        assertThrows(EOFException.class,()->AudioStreamReader.wav(new ByteArrayInputStream(wav(new byte[3],24000,1,0)),(f,b,o,n)->{}));
        assertThrows(EOFException.class,()->AudioStreamReader.wav(new ByteArrayInputStream(wav(new byte[2],24000,1,100)),(f,b,o,n)->{}));
    }
    @Test public void parsesMpeg1Mpeg2AndMpeg25IncludingPadding()throws Exception {
        AudioStreamReader.Mp3Frame first=AudioStreamReader.Mp3Frame.header(header(3,9,0,0,2));
        assertEquals(44100,first.sampleRate);assertEquals(417,first.bytes.length);assertEquals(1152,first.samples);
        assertEquals(418,AudioStreamReader.Mp3Frame.header(header(3,9,0,1,2)).bytes.length);
        AudioStreamReader.Mp3Frame ha=AudioStreamReader.Mp3Frame.header(header(2,8,1,0,1));
        assertEquals(24000,ha.sampleRate);assertEquals(192,ha.bytes.length);assertEquals(576,ha.samples);assertEquals(1,ha.channels);
        AudioStreamReader.Mp3Frame low=AudioStreamReader.Mp3Frame.header(header(0,4,0,0,1));
        assertEquals(11025,low.sampleRate);assertEquals(208,low.bytes.length);
    }
    @Test public void skipsId3AndPreservesEveryCompressedFrame()throws Exception {
        byte[] frame=AudioStreamReader.Mp3Frame.header(header(2,8,1,0,1)).bytes;
        Arrays.fill(frame,4,frame.length,(byte)23);
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        bytes.write(new byte[]{'I','D','3',4,0,0,0,0,0,3,11,22,33});bytes.write(frame);bytes.write(frame);
        AudioStreamReader.Mp3Reader reader=new AudioStreamReader.Mp3Reader(new BufferedInputStream(new ByteArrayInputStream(bytes.toByteArray())));
        assertArrayEquals(frame,reader.next().bytes);assertArrayEquals(frame,reader.next().bytes);assertNull(reader.next());
    }
    @Test public void rejectsReservedMpegHeadersAndTruncatedPayloads()throws Exception {
        for(byte[] invalid:new byte[][]{header(1,8,1,0,1),header(2,0,1,0,1),header(2,15,1,0,1),header(2,8,3,0,1)})
            assertThrows(AudioStreamReader.Unsupported.class,()->AudioStreamReader.Mp3Frame.header(invalid));
        byte[] partial=Arrays.copyOf(AudioStreamReader.Mp3Frame.header(header(2,8,1,0,1)).bytes,20);
        assertThrows(EOFException.class,()->new AudioStreamReader.Mp3Reader(new BufferedInputStream(new ByteArrayInputStream(partial))).next());
    }
}
