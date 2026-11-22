package de.jarvis.audio;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.Test;
import static org.junit.Assert.*;

public class HaDiscoveryEntryTest {
    private Map<String, byte[]> attributes(String... pairs) {
        Map<String, byte[]> values = new HashMap<>();
        for (int i = 0; i < pairs.length; i += 2) values.put(pairs[i], pairs[i + 1].getBytes(StandardCharsets.UTF_8));
        return values;
    }

    @Test public void preservesHttpsCertificateHostnameAndOffersLocalHttpSeparately() {
        List<HaDiscoveryEntry> entries = HaDiscoveryEntry.from("Home", attributes("location_name", "Zuhause",
                "internal_url", "http://homeassistant.local:8123", "external_url", "https://ha.example.org/",
                "base_url", "https://ha.example.org"), "192.168.1.20", 8123);
        assertEquals(2, entries.size());
        assertEquals("Zuhause", entries.get(0).name);
        assertEquals("https://ha.example.org", entries.get(0).base);
        assertEquals("http://192.168.1.20:8123", entries.get(1).base);
    }

    @Test public void httpsBackendIsNotDowngradedToHttp() {
        List<HaDiscoveryEntry> entries = HaDiscoveryEntry.from("Home", attributes(
                "internal_url", "https://ha.local:8123"), "192.168.1.20", 8123);
        assertEquals(1, entries.size());
        assertEquals("https://ha.local:8123", entries.get(0).base);
    }

    @Test public void fallsBackToResolvedLocalIpWhenUrlsAreMissing() {
        assertEquals("http://10.0.0.5:8123",
                HaDiscoveryEntry.from("Home", attributes(), "10.0.0.5", 8123).get(0).base);
        assertEquals("http://[fd12::5]:8123",
                HaDiscoveryEntry.from("Home", attributes(), "fd12::5", 8123).get(0).base);
        assertTrue(HaDiscoveryEntry.from("Home", attributes(), "8.8.8.8", 8123).isEmpty());
        assertTrue(HaDiscoveryEntry.from("Home", attributes(), "192.168.1.2", 0).isEmpty());
    }

    @Test public void ignoresMalformedAdvertisedUrlsAndSanitizesNames() {
        List<HaDiscoveryEntry> entries = HaDiscoveryEntry.from("Home", attributes("location_name", "My\nHome\u202e",
                "internal_url", "https://ha.example.org/api?token=secret",
                "external_url", "https://user:secret@ha.example.org"), "192.168.1.20", 8123);
        assertTrue(entries.isEmpty());
        List<HaDiscoveryEntry> clean = HaDiscoveryEntry.from("Home", attributes("location_name", "My\nHome\u202e"), "10.0.0.5", 8123);
        assertEquals("My Home", clean.get(0).name);
    }
}
