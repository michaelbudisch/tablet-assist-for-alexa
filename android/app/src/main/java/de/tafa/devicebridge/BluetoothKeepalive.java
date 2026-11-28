package de.tafa.devicebridge;

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

/** Opt-in zero-PCM playback, only while TAFA's audio player runs.
 * No audio focus request, Bluetooth pairing, system volume change or auto-start.
 */
final class BluetoothKeepalive {
    private final Context context;
    private final AudioManager audio;
    private final Consumer<String> status;
    private final Handler main = new Handler(Looper.getMainLooper());
    private MediaPlayer player;
    private boolean enabled, prepared;
    private long routeDeadline, retryAt;
    private int failures, confirmedDevice = -1;
    private final Runnable monitor = this::tick;

    BluetoothKeepalive(Context context, Consumer<String> status) {
        this.context = context;
        this.audio = context.getSystemService(AudioManager.class);
        this.status = status;
    }

    void setEnabled(boolean newValue) {
        // Repeated service updates must not interrupt an already stable stream.
        if (enabled == newValue) return;
        enabled = newValue;
        main.removeCallbacks(monitor);
        if (!enabled) {
            release();
            failures = 0;
            retryAt = 0;
            status.accept("off");
            return;
        }
        failures = 0;
        retryAt = 0;
        tick();
    }

    /** Briefly release the silent stream after actual media loses audio focus.
     * The saved user preference remains enabled and playback resumes later.
     */
    void pauseForFocus() {
        if (!enabled) return;
        release();
        retryAt = SystemClock.elapsedRealtime() + 10000;
        status.accept("retrying");
        main.removeCallbacks(monitor);
        main.postDelayed(monitor, 1000);
    }

    void close() { setEnabled(false); }

    private AudioDeviceInfo bluetooth() {
        if (audio != null) {
            for (AudioDeviceInfo device : audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS)) {
                if (device.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP) return device;
            }
        }
        return null;
    }

    private void tick() {
        if (!enabled) return;
        long now = SystemClock.elapsedRealtime();
        AudioDeviceInfo device = bluetooth();
        if (device == null) {
            release();
            failures = 0;
            retryAt = 0;
            status.accept("waiting");
        } else if (now < retryAt) {
            status.accept("retrying");
        } else if (player == null) {
            start(device);
        } else {
            try {
                if (!prepared) {
                    if (now >= routeDeadline) fail();
                } else if (player.isPlaying()) {
                    AudioDeviceInfo routed = player.getRoutedDevice();
                    if (routed != null && routed.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP
                            && (confirmedDevice == -1 || confirmedDevice == routed.getId())) {
                        confirmedDevice = routed.getId();
                        failures = 0;
                        status.accept("active");
                    } else if (confirmedDevice != -1 || now >= routeDeadline) {
                        fail();
                    }
                } else if (now >= routeDeadline) {
                    fail();
                }
            } catch (RuntimeException e) {
                fail();
            }
        }
        if (enabled) main.postDelayed(monitor, 1000);
    }

    private void start(AudioDeviceInfo device) {
        try {
            MediaPlayer current = new MediaPlayer();
            player = current;
            routeDeadline = SystemClock.elapsedRealtime() + 15000;
            current.setAudioAttributes(new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
            try (AssetFileDescriptor source =
                         context.getResources().openRawResourceFd(R.raw.keepalive_silence)) {
                current.setDataSource(source.getFileDescriptor(),
                        source.getStartOffset(), source.getLength());
            }
            current.setLooping(true);
            // The WAV is all-zero PCM; nonzero player volume maintains a media
            // session without audible output. Never change system volume.
            current.setVolume(1, 1);
            try { current.setPreferredDevice(device); } catch (RuntimeException ignored) {}
            current.setOnErrorListener((media, what, extra) -> {
                if (media == player) fail();
                return true;
            });
            current.setOnPreparedListener(media -> {
                if (!enabled || media != player) return;
                try {
                    AudioDeviceInfo output = bluetooth();
                    if (output == null) {
                        release();
                        status.accept("waiting");
                        return;
                    }
                    try { media.setPreferredDevice(output); } catch (RuntimeException ignored) {}
                    media.start();
                    prepared = true;
                    routeDeadline = SystemClock.elapsedRealtime() + 4000;
                } catch (RuntimeException e) {
                    fail();
                }
            });
            current.prepareAsync();
            status.accept("starting");
        } catch (Exception e) {
            fail();
        }
    }

    private void fail() {
        release();
        failures = Math.min(10, failures + 1);
        retryAt = SystemClock.elapsedRealtime() + KeepaliveRetry.delayMs(failures);
        status.accept("retrying");
    }

    private void release() {
        if (player != null) {
            try {
                player.setVolume(0, 0);
                player.release();
            } catch (RuntimeException ignored) {}
            player = null;
        }
        confirmedDevice = -1;
        prepared = false;
    }
}
