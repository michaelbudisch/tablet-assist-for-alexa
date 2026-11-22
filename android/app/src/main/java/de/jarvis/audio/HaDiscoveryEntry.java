package de.jarvis.audio;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

final class HaDiscoveryEntry {
    final String name;
    final String base;

    HaDiscoveryEntry(String name, String base) { this.name = name; this.base = base; }

    static List<HaDiscoveryEntry> from(String serviceName, Map<String, byte[]> attributes, String host, int port) {
        String name = attribute(attributes, "location_name");
        if (name.isEmpty()) name = serviceName == null ? "Home Assistant" : serviceName;
        name = name.replaceAll("[\\p{Cntrl}\\p{Cf}]", " ").trim();
        if (name.isEmpty()) name = "Home Assistant";
        if (name.length() > 80) name = name.substring(0, 80);
        Set<String> bases = new LinkedHashSet<>();
        String internal = attribute(attributes, "internal_url");
        // Prefer advertised HTTPS hostnames so certificate verification continues to work.
        for (String key : new String[]{"internal_url", "external_url", "base_url"}) {
            String candidate = attribute(attributes, key);
            try {
                String base = HaAddress.normalize(candidate);
                if (base.startsWith("https://")) bases.add(base);
            } catch (IllegalArgumentException ignored) {}
        }
        // HTTP always uses the resolved LAN IP, not a hostname which might resolve elsewhere.
        if (HaAddress.isHttp(internal) || (internal.isEmpty() && bases.isEmpty())) {
            try {
                if (port > 0 && port <= 65535 && HaAddress.isLocalLiteral(host)) {
                    String local = new URI("http", null, host, port, null, null, null).toASCIIString();
                    bases.add(HaAddress.validate(local, true));
                }
            } catch (Exception ignored) {}
        }
        List<HaDiscoveryEntry> entries = new ArrayList<>();
        for (String base : bases) entries.add(new HaDiscoveryEntry(name, base));
        return entries;
    }

    private static String attribute(Map<String, byte[]> attributes, String key) {
        byte[] value = attributes.get(key);
        return value == null || value.length > 512 ? "" : new String(value, StandardCharsets.UTF_8).trim();
    }
}
