package de.jarvis.audio;

import java.net.InetAddress;
import java.net.URI;
import java.util.Locale;

/** Shared transport policy for setup, discovery and the foreground service. */
final class HaAddress {
    static String normalize(String raw) {
        try {
            URI uri = new URI(raw.trim());
            String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase(Locale.ROOT);
            if ((!scheme.equals("https") && !scheme.equals("http")) || uri.getHost() == null
                    || uri.getRawUserInfo() != null || uri.getRawQuery() != null || uri.getRawFragment() != null
                    || (uri.getRawPath() != null && !uri.getRawPath().isEmpty() && !uri.getRawPath().equals("/"))
                    || uri.getPort() == 0 || uri.getPort() > 65535) {
                throw new IllegalArgumentException();
            }
            return new URI(scheme, null, uri.getHost().toLowerCase(Locale.ROOT), uri.getPort(), null, null, null).toASCIIString();
        } catch (Exception e) {
            throw new IllegalArgumentException("invalid_address");
        }
    }

    static String validate(String raw, boolean allowLocalHttp) {
        String base = normalize(raw);
        if (base.startsWith("http://")) {
            if (!isLocalLiteral(URI.create(base).getHost())) {
                throw new IllegalArgumentException("http_lan_only");
            }
            if (!allowLocalHttp) {
                throw new IllegalArgumentException("http_consent_required");
            }
        }
        return base;
    }

    static String validateStored(String raw, String consentBase) {
        String base = normalize(raw);
        return validate(base, base.equals(consentBase));
    }

    static boolean isHttp(String raw) {
        return raw != null && raw.trim().toLowerCase(Locale.ROOT).startsWith("http://");
    }

    static boolean isLocalLiteral(String rawHost) {
        if (rawHost == null) return false;
        String host = rawHost.replace("[", "").replace("]", "");
        if (host.contains(":")) {
            // Parse only a numeric IPv6 literal; never resolve an untrusted DNS name.
            String address = host.split("%", 2)[0];
            if (!address.matches("[0-9a-fA-F:]+")) return false;
            try {
                byte[] bytes = InetAddress.getByName(address).getAddress();
                return bytes.length == 16 && ((bytes[0] & 0xfe) == 0xfc
                        || ((bytes[0] & 0xff) == 0xfe && (bytes[1] & 0xc0) == 0x80));
            } catch (Exception e) { return false; }
        }
        if (!host.matches("(?:0|[1-9][0-9]{0,2})(?:\\.(?:0|[1-9][0-9]{0,2})){3}")) return false;
        String[] parts = host.split("\\.");
        int[] ip = new int[4];
        for (int i = 0; i < 4; i++) {
            ip[i] = Integer.parseInt(parts[i]);
            if (ip[i] > 255) return false;
        }
        return ip[0] == 10 || (ip[0] == 172 && ip[1] >= 16 && ip[1] <= 31)
                || (ip[0] == 192 && ip[1] == 168) || (ip[0] == 169 && ip[1] == 254);
    }

    private HaAddress() {}
}
