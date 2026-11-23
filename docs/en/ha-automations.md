# Jarvis · Native Home Assistant automations (preview)

**English** | [Deutsch](../ha-automations.md) · [Project overview](../../README.md)

**Optional** · HA backend 1.6.0 with updated detection validator · GPU Worker 1.9.0 with updated vision schema · Echo Relay APK 0.5.0 · Lovelace card 1.3.0.

## Setup

1. Install the existing integration, audio relay and worker following [the regular guide](echo-relay-dashboard.md). Enable camera sharing and motion detection explicitly on the tablet only if everyone affected agrees. Keep captures local, do not archive images and do not use the feature for access control or identification.
2. Add [the optional package](../../homeassistant/templates/echo-relay-automation-package.yaml) to an already configured HA packages directory. **Do not duplicate existing helpers or scripts.** The package adds three empty name helpers, speech status/bridge helpers, last-greeting timestamp, a five-minute timer, the speech script and a disabled greeting automation. Set the last-greeting helper to an earlier date before first testing. Replace `weather.home` in the automation with your own weather entity. Restart HA after installing package/integration updates.
3. Copy the five modules below to `/config/www/jarvis/`. Register **only** the card module as a Lovelace resource, replacing the old card resource. Reload the tablet dashboard fully. This is an optional preview path; legacy installer and templates still use the original card.
   - `echo-relay-assist-card-v1.3.0.js`
   - `jarvis-settings-v1.6.0.js`
   - `jarvis-proactive-v1.6.0.js`
   - `jarvis-model-settings-v1.1.0.js`
   - `jarvis-camera-preview-v1.2.0.js`
4. Use the existing [motion automation](../../homeassistant/templates/echo-relay-proactive-automation.yaml). Configure its motion entity. Using the admin-only `jarvis_tablet_audio.proactive` get/set API, preserve the complete returned settings dictionary (exclude revision/status/entity lists from the settings payload), set enabled and test_mode true, greeting false, script_entity empty, and select person in classes. The backend continues to limit checks by freshness, cooldown and worker availability. The HA greeting automation owns its own time window and daily guard. Disable the motion automation when not needed. Legacy internal greeting must stay off to avoid duplicate audio.
5. In the new **Family** tab, set optional manually chosen names. They are stored in HA input_text helpers and read on each greeting. Apparent categories are fallible estimates, **not actual gender or identity recognition**. Multiple or ambiguous people get neutral greetings; uncertain detections produce no event. Never use a guessed name as authentication.
6. With the tablet dashboard visible and Echo Relay ready, test the reusable script `script.jarvis_sprechen` with a simple message and followup=false. The bridge status must be recent and ready. A started response confirms playback started, not completion. Enable greeting only after this test. Start `timer.jarvis_begrussung_testfenster` for an opt-in five-minute test; success cancels the timer without marking today's regular greeting. Regular schedule: 06:00–10:00, once per day after confirmed playback.

## Reusable actions

```yaml
action: script.jarvis_sprechen
data:
  message: "The washing machine is finished."
  followup: false
  daily_overview: false
response_variable: speech_result
```

Status: started, skipped, error, timeout, tablet_offline or tablet_busy. Follow-up is optional and uses the visible dashboard; no continuous recording is enabled by the script. Use one designated tablet for this preview bridge; multi-client arbitration of this generic event is not yet tested.

The main private Hauszentrale also has an event-driven infobox action (`jarvis_infobox_show`) and a disabled Ring example. These are **kiosk-specific reference features**, not installed by this package. Standard portable card integration and fresh-install tests remain pending. Existing on-demand camera preview and local descriptions are separate from the automatic greeting.

