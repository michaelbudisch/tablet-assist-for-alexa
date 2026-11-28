package de.tafa.devicebridge;

import android.content.Context;
import android.net.nsd.NsdManager;
import android.net.nsd.NsdServiceInfo;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;

/** A bounded, foreground-only DNS-SD search. No API calls or credentials are used. */
final class HaDiscovery {
    static final String SERVICE_TYPE = "_home-assistant._tcp.";
    interface Listener {
        void onFound(HaDiscoveryEntry entry);
        void onFinished(String error);
    }

    private final NsdManager nsd;
    private final WifiManager wifi;
    private final Listener listener;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ArrayDeque<NsdServiceInfo> pending = new ArrayDeque<>();
    private final Set<String> seen = new HashSet<>();
    private final Set<String> emitted = new HashSet<>();
    private WifiManager.MulticastLock multicast;
    private NsdManager.ResolveListener resolving;
    private boolean active;
    private boolean registered;
    private boolean stopRetried;
    private final Runnable timeout = () -> finish(null);

    HaDiscovery(Context context, Listener listener) {
        Context app = context.getApplicationContext();
        nsd = app.getSystemService(NsdManager.class);
        wifi = app.getSystemService(WifiManager.class);
        this.listener = listener;
    }

    void start() {
        active = true;
        try {
            if (nsd == null) throw new IllegalStateException();
            if (wifi != null) {
                multicast = wifi.createMulticastLock("tafa-ha-discovery");
                multicast.setReferenceCounted(false);
                multicast.acquire();
            }
            nsd.discoverServices(SERVICE_TYPE, NsdManager.PROTOCOL_DNS_SD, discovery);
            registered = true;
            main.postDelayed(timeout, 12000);
        } catch (RuntimeException e) {
            finish("discovery_unavailable");
        }
    }

    void cancel() { close(); }

    private void finish(String error) {
        if (!active) return;
        close();
        listener.onFinished(error);
    }

    private void close() {
        active = false;
        main.removeCallbacksAndMessages(null);
        pending.clear();
        if (registered) {
            registered = false;
            try { nsd.stopServiceDiscovery(discovery); } catch (RuntimeException ignored) {}
        }
        if (resolving != null && Build.VERSION.SDK_INT >= 34) {
            try { nsd.stopServiceResolution(resolving); } catch (RuntimeException ignored) {}
        }
        resolving = null;
        if (multicast != null && multicast.isHeld()) multicast.release();
        multicast = null;
    }

    private final NsdManager.DiscoveryListener discovery = new NsdManager.DiscoveryListener() {
        @Override public void onDiscoveryStarted(String type) {}
        @Override public void onDiscoveryStopped(String type) {}
        @Override public void onStartDiscoveryFailed(String type, int code) {
            main.post(() -> finish("discovery_failed_start"));
        }
        @Override public void onStopDiscoveryFailed(String type, int code) {
            // An OEM may reject the first stop while a start is still in flight.
            if (stopRetried) return;
            stopRetried = true;
            try { nsd.stopServiceDiscovery(this); } catch (RuntimeException ignored) {}
        }
        @Override public void onServiceFound(NsdServiceInfo info) {
            main.post(() -> {
                if (!active || seen.size() >= 20) return;
                String type = info.getServiceType();
                if (type == null || !type.startsWith("_home-assistant._tcp")) return;
                if (seen.add(info.getServiceName())) {
                    pending.add(info);
                    resolveNext();
                }
            });
        }
        @Override public void onServiceLost(NsdServiceInfo info) {
            main.post(() -> pending.removeIf(item -> item.getServiceName().equals(info.getServiceName())));
        }
    };

    private void resolveNext() {
        // Older Android versions accept only one outstanding resolve at a time.
        if (!active || resolving != null || pending.isEmpty()) return;
        NsdServiceInfo next = pending.removeFirst();
        NsdManager.ResolveListener callback = new NsdManager.ResolveListener() {
            @Override public void onResolveFailed(NsdServiceInfo info, int code) {
                main.post(() -> complete(this, null));
            }
            @Override public void onServiceResolved(NsdServiceInfo info) {
                main.post(() -> complete(this, info));
            }
        };
        resolving = callback;
        try { nsd.resolveService(next, callback); }
        catch (RuntimeException e) { complete(callback, null); }
    }

    private void complete(NsdManager.ResolveListener callback, NsdServiceInfo info) {
        if (!active || resolving != callback) return;
        resolving = null;
        if (info != null && info.getHost() != null) {
            for (HaDiscoveryEntry entry : HaDiscoveryEntry.from(info.getServiceName(), info.getAttributes(),
                    info.getHost().getHostAddress(), info.getPort())) {
                if (emitted.size() < 20 && emitted.add(entry.base)) listener.onFound(entry);
            }
        }
        resolveNext();
    }
}
