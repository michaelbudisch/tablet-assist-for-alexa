package de.jarvis.audio;

import java.util.regex.Pattern;

final class TokenQr {
    // HA long-lived access tokens are JWTs. Authentication still happens at HA.
    private static final Pattern JWT = Pattern.compile("[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+");

    static String parse(String contents) {
        if (contents == null || contents.length() > 4096) {
            throw new IllegalArgumentException("invalid_qr_token");
        }
        String token = contents.trim();
        if (!JWT.matcher(token).matches()) {
            throw new IllegalArgumentException("invalid_qr_token");
        }
        return token;
    }

    private TokenQr() {}
}
