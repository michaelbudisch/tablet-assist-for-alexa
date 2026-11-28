package de.tafa.devicebridge;

final class PcmFormat {
    final int sampleRate, channels, frameBytes;
    PcmFormat(int sampleRate, int channels) {
        if (sampleRate < 8000 || sampleRate > 96000 || channels < 1 || channels > 2)
            throw new IllegalArgumentException("unsupported_pcm_format");
        this.sampleRate = sampleRate; this.channels = channels; frameBytes = channels * 2;
    }
    int bytesForMs(int millis) { return (int) ((long) sampleRate * millis / 1000) * frameBytes; }
    boolean same(PcmFormat other) { return sampleRate == other.sampleRate && channels == other.channels; }
}
