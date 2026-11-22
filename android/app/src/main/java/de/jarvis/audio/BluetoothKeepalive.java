package de.jarvis.audio;

import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.media.AudioAttributes;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import java.util.function.Consumer;

/** Opt-in zero-PCM playback. Does not request audio focus, reconnect devices or change system volume. */
final class BluetoothKeepalive {
    private final Context context;
    private final AudioManager audio;
    private final Consumer<String> status;
    private final Handler main = new Handler(Looper.getMainLooper());
    private MediaPlayer player;
    private boolean enabled, failed, prepared;
    private long routeDeadline;
    private int confirmedDevice = -1;
    private final Runnable monitor = this::tick;

    BluetoothKeepalive(Context context, Consumer<String> status) {
        this.context = context;
        this.audio = context.getSystemService(AudioManager.class);
        this.status = status;
    }

    void setEnabled(boolean enabled) {
        this.enabled = enabled;
        failed = false;
        main.removeCallbacksAndMessages(null);
        if (!enabled) { release(); status.accept("off"); return; }
        tick();
    }

    void pauseForFocus() {
        enabled = false;
        main.removeCallbacksAndMessages(null);
        release();
        status.accept("error");
    }

    void close() { setEnabled(false); }

    private AudioDeviceInfo bluetooth() {
        if (audio != null) for (AudioDeviceInfo device : audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS))
            if (device.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP) return device;
        return null;
    }

    private void tick() {
        if (!enabled || failed) return;
        AudioDeviceInfo device = bluetooth();
        if (device == null) { release(); status.accept("waiting"); }
        else if (player == null) start(device);
        else {
            try {
                if (!prepared) {
                    if (SystemClock.elapsedRealtime() >= routeDeadline) fail();
                } else if (player.isPlaying()) {
                    AudioDeviceInfo routed = player.getRoutedDevice();
                    if (routed != null && routed.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP
                            && (confirmedDevice == -1 || confirmedDevice == routed.getId())) {
                        confirmedDevice = routed.getId();
                        status.accept("active");
                    } else if (confirmedDevice != -1 || SystemClock.elapsedRealtime() >= routeDeadline) fail();
                } else if (SystemClock.elapsedRealtime() >= routeDeadline) fail();
            } catch (RuntimeException e) { fail(); }
        }
        if (enabled && !failed) main.postDelayed(monitor, 1000);
    }

    private void start(AudioDeviceInfo device) {
        try {
            MediaPlayer current = new MediaPlayer();
            player = current;
            routeDeadline = SystemClock.elapsedRealtime() + 15000;
            current.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
            try (AssetFileDescriptor source = context.getResources().openRawResourceFd(R.raw.keepalive_silence)) {
                current.setDataSource(source.getFileDescriptor(), source.getStartOffset(), source.getLength());
            }
            current.setLooping(true);
            // The bundled WAV contains only zeros. A nonzero volume keeps a real playback session.
            current.setVolume(1, 1);
            try { current.setPreferredDevice(device); } catch (RuntimeException ignored) {}
            current.setOnErrorListener((media, what, extra) -> { if (media == player) fail(); return true; });
            current.setOnPreparedListener(media -> {
                if (!enabled || media != player) return;
                try {
                    AudioDeviceInfo output = bluetooth();
                    if (output == null) { release(); status.accept("waiting"); return; }
                    try { media.setPreferredDevice(output); } catch (RuntimeException ignored) {}
                    media.start();
                    prepared = true;
                    routeDeadline = SystemClock.elapsedRealtime() + 4000;
                } catch (RuntimeException e) { fail(); }
            });
            current.prepareAsync();
            status.accept("starting");
        } catch (Exception e) { fail(); }
    }

    private void fail() {
        failed = true;
        main.removeCallbacksAndMessages(null);
        release();
        status.accept("error");
    }

    private void release() {
        if (player != null) {
            try { player.setVolume(0, 0); player.release(); } catch (RuntimeException ignored) {}
            player = null;
        }
        confirmedDevice = -1;
        prepared = false;
    }
}
