package de.jarvis.audio;

import org.junit.Test;
import static org.junit.Assert.*;

public class TokenQrTest {
    private static final String TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJleGFtcGxlIn0.signature_-123";

    @Test public void acceptsPlainTokenAndTrimsPasteWhitespace() {
        assertEquals(TOKEN, TokenQr.parse(TOKEN));
        assertEquals(TOKEN, TokenQr.parse("\r\n " + TOKEN + " \n"));
    }

    @Test public void rejectsLinksJsonAndMalformedTokensWithoutEchoingContents() {
        String[] invalid = {null, "", " ", "https://example.org/" + TOKEN,
                "{\"token\":\"" + TOKEN + "\"}", "Bearer " + TOKEN,
                "a.b", "a.b.c.d", ".b.c", "a..c", "a.b.", "a.b.c\nsecret",
                "a.b.ümlaut", "a.b." + "x".repeat(4096)};
        for (String value : invalid) {
            IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                    () -> TokenQr.parse(value));
            assertFalse(error.getMessage().contains(TOKEN));
        }
    }
}
