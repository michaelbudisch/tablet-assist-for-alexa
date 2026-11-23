# HA Jarvis Echo Relay 0.5.0 · Camera and vision preview

**English** | [Deutsch](RELEASE_NOTES.de.md) · [Project overview](../README.md)

Explicit-start camera foreground delivery pushes bounded, upright JPEGs to the authenticated HA receiver about every two seconds. A separate notification stops it; audio remains independent. Optional image movement, memory-only images, session invalidation and a 15-second freshness limit are included. The matching HA integration selects tablet/outdoor/door images and calls the existing local vision worker for explicit questions/actions.

Install over the previous app to retain credentials. Application ID `de.jarvis.audio`; non-debuggable release signed with the same previous local test key. No private keys included. JVM, lint, native Android camera/background/HTTP/UI/audio and real-HA receiver/routing checks passed. Actual tablet battery/screen-off behavior still needs hardware validation. See the linked setup guide.

[Camera setup](docs/camera-preparation.md)
