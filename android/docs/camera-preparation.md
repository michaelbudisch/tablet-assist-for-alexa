# Set up TAFA tablet cameras

[Deutsch](camera-preparation.de.md) · [Current Device Bridge](../README.md) · [TAFA setup](../../docs/en/setup-guide.md)

This guide applies to **TAFA Device Bridge 1.2.1** with the unified **TAFA integration 0.4.26**. The former standalone Jarvis camera API is **not** required for new installations.

## Enable a room camera

1. Configure the TAFA integration and [Android Device Bridge](../README.md). Use a dedicated **non-admin HA room user** for each tablet.
2. In Home Assistant open **TAFA → Devices & Multiroom → Tablet cameras per room** and explicitly allow the **correct room**. Camera uploads are **off by default**.
3. In Device Bridge go to **Settings → Camera**; grant Android camera permission, choose front/rear lens and image interval (**1/2/3/5/10 seconds**). Optionally enable **Report image motion**.
4. Tap **Start camera for HA** on the tablet. **Granting HA permission does not itself start capture.** No HA administrator token is required.
5. Check the room's camera/motion entities under **HA → Devices & services → TAFA**. Without fresh images or with image motion disabled, the sensor may show unavailable.

TAFA uploads **JPEG still frames** using authenticated TAFA room-camera endpoints. This is **not** a native continuous video recorder, image archive or reliable person/delivery detection. Coarse pixel motion reporting may produce false positives. Stop capture from Device Bridge or its visible Android notification.

## Optional local Vision

Image descriptions require a separately configured compatible [GPU worker with Vision](../../worker/docs/README.md) and an installed vision model. The GPU is **not** required merely to display a camera image in HA. Restrict Vision port **10503** to the trusted LAN and configure camera/model selection in TAFA. AI descriptions are fallible and must not be treated as identity recognition.

**Privacy:** Use room cameras only with appropriate notice and permission from people present. Disable camera access when not needed. Never expose camera/Vision service ports to the public Internet.

[Historical Jarvis camera reference](archive/legacy-camera-preparation.en.md) is retained for migrations only, **not** as a fresh-install procedure.
