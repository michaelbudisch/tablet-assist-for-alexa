package de.tafa.devicebridge;

import org.junit.Test;
import static org.junit.Assert.*;

public class HaAddressTest {
    @Test public void httpsKeepsHostnameAndDoesNotNeedHttpConsent() {
        assertEquals("https://ha.example.org:8123", HaAddress.validate(" HTTPS://HA.EXAMPLE.ORG:8123/ ", false));
        assertEquals("https://ha.example.org", HaAddress.validateStored("https://ha.example.org/", ""));
    }

    @Test public void httpRequiresConsentForExactOrigin() {
        String base = "http://192.168.1.20:8123";
        assertThrows(IllegalArgumentException.class, () -> HaAddress.validate(base, false));
        assertEquals(base, HaAddress.validateStored(base + "/", base));
        assertThrows(IllegalArgumentException.class,
                () -> HaAddress.validateStored(base, "http://192.168.1.21:8123"));
        assertThrows(IllegalArgumentException.class,
                () -> HaAddress.validateStored(base, "http://192.168.1.20:80"));
        assertThrows(IllegalArgumentException.class, () -> HaAddress.validateStored(base, ""));
    }

    @Test public void acceptsOnlyPrivateOrLinkLocalLiteralHttpDestinations() {
        for (String host : new String[]{"10.0.0.1", "172.16.0.1", "172.31.255.254", "192.168.1.2", "169.254.1.2", "[fd12::1234]", "[fe80::1234%25wlan0]"}) {
            assertTrue(host, HaAddress.isLocalLiteral(host));
            assertTrue(HaAddress.validate("http://" + host + ":8123", true).startsWith("http://"));
        }
        for (String host : new String[]{"8.8.8.8", "172.15.1.2", "172.32.1.2", "127.0.0.1", "0.0.0.0", "224.0.0.1", "homeassistant.local", "ha.example.org", "192.168.1.2.example.org", "0300.168.1.2", "192.168.256.1", "3232235777", "[::1]", "[::]", "[2001:db8::1]", "[::ffff:192.168.1.2]"}) {
            assertFalse(host, HaAddress.isLocalLiteral(host));
            assertThrows(IllegalArgumentException.class, () -> HaAddress.validate("http://" + host, true));
        }
    }

    @Test public void rejectsCredentialBearingUrlsPathsAndInvalidPorts() {
        for (String raw : new String[]{"https://user:secret@ha.local", "https://ha.local/api", "https://ha.local?token=secret", "https://ha.local#secret", "https://ha.local/%2f", "https://ha.local:0", "https://ha.local:65536", "file:///secret", "ha.local", ""}) {
            assertThrows(IllegalArgumentException.class, () -> HaAddress.validate(raw, true));
        }
    }
}
