# 0.3.0 · Streaming
- Decode MPEG Layer III incrementally with Android MediaCodec and play MP3/16-bit PCM WAV through AudioTrack before the HTTP response completes.
- Use a 600 ms startup/rebuffer target and a bounded two-second PCM queue; handle unknown-length streaming WAV and arbitrary network packet boundaries.
- Prime/verify Bluetooth with zeros before submitting speech, preserving the first words; monitor route changes during playback and buffering.
- Spool the same response to private cache for unsupported-format fallback only before speech; never regenerate or replay an answer after partial playback.
- Cancel blocked network reads, delete temporary audio and retain the existing HA command/status helper contract, credentials and keepalive.
- Add timing diagnostics and JVM/native Android tests using synthetic delayed chunked MP3/WAV responses.

# 0.2.0 · HA Jarvis Echo Relay
- Redesign phone/tablet setup with a custom vector icon, three setup cards, readable playback states and expandable diagnostics.
- Add complete English/German interface, setup help and notification localization, including an in-app language switch.
- Document the one-time QR code in the Home Assistant token creation dialog as the primary onboarding path.
- Add opt-in native zero-PCM Bluetooth keepalive, independent of the HA page and off by default.
- Preserve application ID, encrypted credential format and exact-address HTTP consent when upgrading.
- Add emulator UI checks for language switching, responsive layout, consent, token retention, WAV decoding and keepalive cleanup.

# 0.1.2
- Find Home Assistant on the LAN using bounded mDNS/DNS-SD discovery; select discovered addresses in setup.
- Allow HTTP only to private/link-local IP literals after explicit consent for the exact server address; HTTPS certificate verification is unchanged.
- Initialize the media source before requesting Bluetooth, retry the preference after preparation and during muted playback, and accept an already active A2DP route.
- Keep playback muted until the actual Bluetooth route is verified, then monitor the selected output; report route type and preference outcome on failure.

# 0.1.1
- Scan a plain HA access token from a QR code using the embedded camera scanner.
- Request camera access only when scanning; keep manual entry available.
- Validate QR token format and keep scanned tokens masked until the player is started.
- Add an offline QR generator in tools/token-qr.html.

# 0.1.0
- Native Android MediaPlayer prototype, foreground-only opt-in service.
- Authenticated HA polling, Bluetooth route checks, explicit stop, status reporting.
- Initial playback buffers the entire file; streaming is not implemented in this version.
