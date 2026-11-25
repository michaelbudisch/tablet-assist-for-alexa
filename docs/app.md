# TAFA als Home-Assistant-App installieren

[English](en/app.md)

**Experimentell 0.1.0.** Home Assistant OS 2026.11+, amd64/aarch64. Die Einrichtungs-App ersetzt keine externen Sprachserver.

1. [TAFA-App-Repository hinzufügen](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa) oder Einstellungen → Apps → App installieren → Repositories öffnen und `https://github.com/michaelbudisch/tablet-assist-for-alexa` hinzufügen.
2. TAFA installieren, starten und die Weboberfläche öffnen. Schutzmodus eingeschaltet lassen; kein öffentlicher Port nötig.
3. HA-Sicherung erstellen. [CPU-Sprachserver](proxmox.md) einrichten, Wyoming-Integration hinzufügen und optional [GPU-Worker](worker.md) vorbereiten.
4. Sprachserver-Host und STT-Entität eintragen. Optionale GPU-Felder können leer bleiben. Fehlende Dateien per Schaltfläche installieren. Vorhandene Integrationsordner werden übersprungen.
5. Home Assistant manuell neu starten, unter Geräte & Dienste **Tablet Assist for Alexa** und **Jarvis Tablet Audio** hinzufügen und Sprachpipeline sowie Worker-Optionen konfigurieren.
6. [TAFA Device Bridge](../android/README.de.md) installieren und [Multiroom-Anleitung](../homeassistant/examples/MULTIROOM.de.md) beachten.

## Grenzen und Updates

Die App kopiert ausschließlich mitgelieferte öffentliche Komponenten nach `custom_components`. configuration.yaml, secrets, private Dashboards und vorhandene Einträge bleiben unverändert. Eine Deinstallation der App entfernt die installierten Integrationen nicht. Update-Wege nicht vermischen; App-Updates aktualisieren die Core-Komponenten nicht automatisch. Die Basisintegration ist alternativ über [Marketplace](marketplace.md) installierbar. Marketplace installiert keine Apps.

Keine automatische Kopplung, Mikrofon-/Kameraaktivierung, Worker-Installation oder Altanlagenmigration. HA-OS-Neuinstallation, Ingress-Anzeige, Pipeline-Einrichtung, reale Audioausgabe und Multiroom-Verhalten sind noch nicht verifiziert. Zuerst in einer Testinstanz verwenden.
