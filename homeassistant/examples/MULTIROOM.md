# TAFA Multiroom – assign tablets to Home Assistant areas

[Deutsch](MULTIROOM.de.md) · [Project](../../README.md) · [Setup](../../docs/en/setup-guide.md)

**Current setup:** TAFA App 0.4.65+, integration 0.5.3+, Device Bridge 1.3.1+. **Home Assistant Areas are the only room source**; do not create a second TAFA room list in the Control Center.

## One-time setup per tablet

1. In **Home Assistant → Settings → Areas, labels & zones → Areas**, create the area if it does not already exist.
2. Native per-room audio and camera permissions currently require **one dedicated active non-admin HA user per tablet**. This is an authorization identity, **not another room assignment**. Keep that user's token on its tablet.
3. Connect TAFA Device Bridge to HA and start the native audio player. The app **automatically creates a persistent unique 32-character installation ID**. Its optional device name is for display only and is not a room selector.
4. Under **Apps → TAFA → User interface → Devices & Multiroom**, each enrolled tablet appears once with its editable tablet name, stable ID and status. Choose the **Home Assistant area** and click **Assign area**. Multiple tablets may share an HA area, with a separate non-admin HA account for each native audio channel. TAFA automatically provisions its internal audio route and updates the HA device registry area. There is no separate TAFA room creation or user transfer checkbox.
5. Test the wake word and playback. For an Echo speaker, pair its Android Bluetooth media output.

A fresh Android installation may create a new installation ID. Assign the desired HA area again; TAFA can replace the same owner's **offline** previous installation, but not an active/foreign device. Explicit confirmation is required to move an existing tablet to a different area because its previous TAFA camera entities may be retired.

## Optional camera and advanced controls

Under **Devices & Multiroom → Advanced**, configure camera access or reset a TAFA pairing. Camera uploads are disabled for a newly assigned area until explicitly enabled and started on Android. Resetting TAFA routing does **not** delete an HA area or HA user.

**Alexa/Echo announcement targets** in **Features & data sources** are separate optional mappings to HA `notify` services. They are **not** tablet rooms and do not change the tablet's HA area.

## Troubleshooting

- **Missing tablet:** Verify Android connection, its dedicated HA account/token and the running audio player.
- **Area cannot be assigned:** The tablet owner must be the logged-in non-admin user; a foreign or currently active different tablet is not taken over silently.
- **No speech:** Check native player, wake word and optional Bluetooth. A successful HTTP probe alone cannot prove audible playback.
- **Ambient not responding:** Check that the browser is bound to the new registered device ID, then reload the TAFA dashboard.
- **Old Jarvis files:** Keep legacy components out of fresh installs; migration-only identifiers do not mean a second active assistant.

**Security:** An installation ID is not an authentication credential. Keep HA access tokens out of Git, logs and screenshots; prefer trusted HTTPS.

## Tablet identity sensors

Starting with **TAFA integration 0.5.5**, each enrolled tablet automatically provides two new Home Assistant sensor entities: **Tabletname** (editable display name, updated when renamed) and **Gerätekennung** (full 32-character Android installation ID). Each sensor has an immutable integration unique ID derived from the installation ID, not the display name, and remains available while its registered tablet is offline. Home Assistant assigns the concrete `sensor.…` entity IDs. A fresh install may create a different installation ID.
