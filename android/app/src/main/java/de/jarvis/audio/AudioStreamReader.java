package de.jarvis.audio;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Incremental RIFF/PCM and MPEG Layer III framing. No seek, content-length or EOF is needed to start. */
final class AudioStreamReader {
    static final class Unsupported extends IOException {
        Unsupported() { super("unsupported_stream_format"); }
        Unsupported(Throwable cause) { super("unsupported_stream_format", cause); }
    }
    interface PcmConsumer { void accept(PcmFormat format, byte[] bytes, int offset, int length) throws Exception; }
    interface Mp3Decoder extends AutoCloseable {
        void frame(Mp3Frame frame, PcmConsumer output) throws Exception;
        void end(PcmConsumer output) throws Exception;
        void close();
    }
    interface DecoderFactory { Mp3Decoder create(Mp3Frame first) throws Exception; }

    static String decode(BufferedInputStream input, PcmConsumer output, DecoderFactory decoders) throws Exception {
        input.mark(12);
        byte[] prefix = new byte[4];
        int count = readSome(input, prefix, 0, 4);
        input.reset();
        if (count == 4 && ascii(prefix, 0, "RIFF")) { wav(input, output); return "wav_pcm"; }
        if(count==0)throw new EOFException("empty_audio");
        if(count<4)throw new Unsupported();
        // Other containers must go to the file reserve, not be searched for accidental MPEG sync words.
        if(!ascii(prefix,0,"ID3"))Mp3Frame.header(prefix);
        Mp3Reader reader = new Mp3Reader(input);
        Mp3Frame first = reader.next();
        if (first == null) throw new EOFException("empty_audio");
        try (Mp3Decoder decoder = decoders.create(first)) {
            decoder.frame(first, output);
            Mp3Frame frame;
            while ((frame = reader.next()) != null) {
                if (frame.sampleRate != first.sampleRate || frame.channels != first.channels) throw new IOException("stream_format_changed");
                decoder.frame(frame, output);
            }
            decoder.end(output);
        }
        return "mp3";
    }

    static void wav(InputStream input, PcmConsumer output) throws Exception {
        byte[] riff = exact(input, 12);
        if (!ascii(riff, 0, "RIFF") || !ascii(riff, 8, "WAVE")) throw new Unsupported();
        PcmFormat format = null;
        long metadata = 12;
        while (true) {
            byte[] chunk = exact(input, 8);
            long size = u32(chunk, 4);
            metadata += 8;
            if (ascii(chunk, 0, "data")) {
                if (format == null) throw new IOException("wav_missing_format");
                // HA/Wyoming streaming WAVs use zero or a sentinel for an as-yet unknown length.
                boolean unknown = size == 0 || size == 0xffffffffL || size == 0x7fffffffL;
                if (!unknown && (size > 24L * 1024 * 1024 || size % format.frameBytes != 0)) throw new IOException("invalid_wav_length");
                byte[] bytes = new byte[16384 + format.frameBytes];
                long remaining = unknown ? Long.MAX_VALUE : size;
                int carry = 0;
                while (remaining > 0) {
                    int read = input.read(bytes, carry, (int) Math.min(16384, remaining));
                    if (read < 0) {
                        if (!unknown) throw new EOFException("truncated_wav");
                        break;
                    }
                    if (read == 0) continue;
                    remaining -= read;
                    int available = carry + read;
                    int aligned = available - available % format.frameBytes;
                    if (aligned > 0) output.accept(format, bytes, 0, aligned);
                    carry = available - aligned;
                    if (carry > 0) System.arraycopy(bytes, aligned, bytes, 0, carry);
                }
                if (carry != 0) throw new EOFException("unaligned_wav");
                return;
            }
            if (size > 256 * 1024 || metadata + size > 256 * 1024) throw new Unsupported();
            if (ascii(chunk, 0, "fmt ")) {
                if (size < 16 || size > 4096) throw new Unsupported();
                byte[] fmt = exact(input, (int) size);
                int encoding = u16(fmt, 0), channels = u16(fmt, 2), bits = u16(fmt, 14);
                long rate = u32(fmt, 4);
                if (encoding != 1 || bits != 16 || rate > 96000) throw new Unsupported();
                try { format = new PcmFormat((int) rate, channels); } catch (IllegalArgumentException e) { throw new Unsupported(e); }
                if (u16(fmt, 12) != format.frameBytes || u32(fmt, 8) != rate * format.frameBytes) throw new IOException("invalid_wav_format");
            } else discard(input, size);
            if ((size & 1) != 0) exact(input, 1);
            metadata += size + (size & 1);
        }
    }

    static final class Mp3Frame {
        final byte[] bytes;
        final int sampleRate, channels, samples;
        Mp3Frame(byte[] bytes, int rate, int channels, int samples) {
            this.bytes = bytes; sampleRate = rate; this.channels = channels; this.samples = samples;
        }
        static Mp3Frame header(byte[] header) throws Unsupported {
            int word = (header[0] & 255) << 24 | (header[1] & 255) << 16 | (header[2] & 255) << 8 | (header[3] & 255);
            int version = (word >>> 19) & 3, layer = (word >>> 17) & 3;
            int bitrateIndex = (word >>> 12) & 15, rateIndex = (word >>> 10) & 3;
            if ((word & 0xffe00000) != 0xffe00000 || version == 1 || layer != 1 || bitrateIndex == 0 || bitrateIndex == 15 || rateIndex == 3)
                throw new Unsupported();
            int[] rates = {44100, 48000, 32000};
            int[] mpeg1 = {0,32,40,48,56,64,80,96,112,128,160,192,224,256,320};
            int[] mpeg2 = {0,8,16,24,32,40,48,56,64,80,96,112,128,144,160};
            int rate = rates[rateIndex] / (version == 3 ? 1 : version == 2 ? 2 : 4);
            int bitrate = (version == 3 ? mpeg1 : mpeg2)[bitrateIndex] * 1000;
            int size = (version == 3 ? 144 : 72) * bitrate / rate + ((word >>> 9) & 1);
            if (size < 4 || size > 4096) throw new Unsupported();
            byte[] bytes = Arrays.copyOf(header, size);
            return new Mp3Frame(bytes, rate, ((word >>> 6) & 3) == 3 ? 1 : 2, version == 3 ? 1152 : 576);
        }
    }

    static final class Mp3Reader {
        private final BufferedInputStream input;
        private boolean started;
        Mp3Reader(BufferedInputStream input) { this.input = input; }
        Mp3Frame next() throws IOException {
            input.mark(12);
            byte[] header = new byte[4];
            int count = readSome(input, header, 0, 4);
            input.reset();
            if (count == 0) return null;
            if (count < 4) throw new EOFException("truncated_mp3");
            if (ascii(header, 0, "ID3")) {
                byte[] tag = exact(input, 10);
                if ((tag[6] & 128) != 0 || (tag[7] & 128) != 0 || (tag[8] & 128) != 0 || (tag[9] & 128) != 0) throw new Unsupported();
                int size = (tag[6] & 127) << 21 | (tag[7] & 127) << 14 | (tag[8] & 127) << 7 | (tag[9] & 127);
                if (size > 512 * 1024) throw new Unsupported();
                discard(input, size + (tag[3] == 4 && (tag[5] & 16) != 0 ? 10 : 0));
                // Limit tag chains as well as each individual tag.
                return nextWithoutTag();
            }
            if (started && (ascii(header, 0, "TAG") || ascii(header, 0, "APET"))) return null;
            return readFrame();
        }
        private Mp3Frame nextWithoutTag() throws IOException {
            input.mark(4); byte[] h = exact(input, 4); input.reset();
            if (ascii(h, 0, "ID3")) throw new Unsupported();
            return readFrame();
        }
        private Mp3Frame readFrame() throws IOException {
            byte[] header = exact(input, 4);
            int skipped = 0;
            while (true) {
                try {
                    Mp3Frame frame = Mp3Frame.header(header);
                    byte[] body = exact(input, frame.bytes.length - 4);
                    System.arraycopy(body, 0, frame.bytes, 4, body.length);
                    started = true;
                    return frame;
                } catch (Unsupported e) {
                    if (started || skipped++ >= 16 * 1024) throw e;
                    int next = input.read();
                    if (next < 0) throw new Unsupported();
                    header[0]=header[1]; header[1]=header[2]; header[2]=header[3]; header[3]=(byte)next;
                }
            }
        }
    }

    static int readSome(InputStream input, byte[] bytes, int offset, int length) throws IOException {
        int total=0;
        while(total<length){int read=input.read(bytes,offset+total,length-total);if(read<0)break;if(read>0)total+=read;}
        return total;
    }
    static byte[] exact(InputStream input,int length)throws IOException {
        byte[] bytes=new byte[length];if(readSome(input,bytes,0,length)!=length)throw new EOFException("truncated_audio");return bytes;
    }
    static void discard(InputStream input,long length)throws IOException {
        byte[] bytes=new byte[4096];while(length>0){int n=input.read(bytes,0,(int)Math.min(length,bytes.length));if(n<0)throw new EOFException("truncated_metadata");length-=n;}
    }
    static boolean ascii(byte[] bytes,int offset,String text){return new String(bytes,offset,text.length(),StandardCharsets.US_ASCII).equals(text);}
    static int u16(byte[] bytes,int offset){return(bytes[offset]&255)|((bytes[offset+1]&255)<<8);}
    static long u32(byte[] bytes,int offset){return(u16(bytes,offset)&0xffffL)|((long)u16(bytes,offset+2)<<16);}
    private AudioStreamReader(){}
}
