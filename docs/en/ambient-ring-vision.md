# Ambient profiles and Ring vision diagnostics (TAFA 0.4.99)

[Deutsch](../ambient-ring-vision.md) · [Setup guide](setup-guide.md) · [Overview](../../README.md)

## Per-tablet Ambient settings

Open **TAFA Dashboard → More → Settings → TAFA Ambient**. Each paired tablet has a separate profile stored in its Home Assistant installation, not in GitHub. You can configure its calendar, proximity entity, enable/auto-open flags, close behavior, display duration, and up to twelve sensor labels and entity IDs (up to six visible around the globe on smaller displays).

The optional **Preview responses on this browser** action is under a collapsed browser-only preview section and is hidden on Android; it never pairs a tablet or changes an HA area. Normal Android tablets automatically use their unique registered device identity. Profile revisions prevent accidental overwrites during concurrent edits. If no device can be identified unambiguously, TAFA does not silently bind the browser to another room.

## Configure Ring recording cameras

In **TAFA Dashboard → More → Settings → Ring camera mapping**, select **Last recording** for the door and outside Ring devices. Do not select **Live view**. TAFA validates that the two entities are supported, distinct Ring recording cameras and retains the mapping in the HA integration options.

An optional local GPU vision worker can sample twelve chronological frames from an existing Ring MP4, use structured Qwen vision inference, and perform a detail check when needed. Existing fallback paths remain available.

## View the Vision diagnosis

Open **TAFA Dashboard → Home → Cameras**. **Ring vision diagnostics** shows the contact sheet actually sent to the vision worker, analyzed/extracted frame counts, inference mode, and the available scene summary. Fallback runs may include per-frame descriptions.

The image collection is **memory-only**, expires after 60 minutes, and disappears on HA restart. Viewing diagnostics does **not** start a livestream, a new inference run, or an Alexa announcement. Historical observations require the user's own Home Assistant Recorder and/or logging automations.

## Ring motion notice events

A permission-scoped stream can send Ring motion notices to paired tablets. It accepts the event type `tafa_camera_notice` and the legacy `jarvis_infobox_show` type for existing users. Event data must contain a configured Ring `camera` and unique `request_id`; optional fields include `title` and `seconds`. No unrestricted Home Assistant event-bus access is granted.

The dashboard displays **“Motion detected”** and, when available, the most recent Ring snapshot without launching a live stream. **Motion-triggering automations must be configured separately**; TAFA does not replace or edit them.

## Compatibility and updates

The public implementation contains no household-specific entity IDs, automations, or credentials. Existing HA settings and Ambient profiles are intended to be preserved through upgrades. A commit to the main branch does **not** itself publish a Home Assistant Marketplace/HACS release or signed Android APK.
