# TAFA · Setup / Einrichtung

**Experimental 0.1.0; Home Assistant OS, amd64/aarch64.**

1. Create a Home Assistant backup / HA-Sicherung erstellen.
2. Prepare CPU speech services and optional GPU worker / Sprachserver vorbereiten.
3. Start TAFA and open its Web UI / TAFA starten und Weboberfläche öffnen.
4. Enter local hostnames and entity IDs. Install missing backend files. Existing components are skipped, never overwritten.
5. Restart Home Assistant manually. Configure Tablet Assist for Alexa and Jarvis Tablet Audio in Devices & services.
6. Install Device Bridge 1.0.0 and configure devices using the linked Multiroom guide.

The app bundles the publicly committed integrations only. Marketplace still installs just the base integration. No private dashboard, automatic camera/microphone activation, credential import, worker installation, or existing-installation migration. Files remain after uninstalling the setup app. App installation and Core setup must be tested on a clean instance before production use.
