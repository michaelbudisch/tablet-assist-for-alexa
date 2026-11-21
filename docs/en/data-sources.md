# Local data sources and voice commands (0.3.1)

[Deutsch](../data-sources.md) · [Installation](marketplace.md)

The standalone integration needs no helpers or entity names from another household. Open **Tablet Assist → Data sources** for configuration status. Administrators can follow the link to the integration and select **Options** to select or clear entities. Each source is optional. Saving reloads the integration. Household mappings are stored only in the local HA config entry; no personal mappings are included in the repository.

## Supported sources

| Feature | Entity / requirements |
|---|---|
| Weather | A weather entity with current data; daily/hourly forecasts depend on provider |
| Shopping | One todo entity, e.g. Bring!; provider must support add/remove |
| Waste collection | Per waste type, one sensor with ISO YYYY-MM-DD state or date-key attributes, e.g. Waste Collection Schedule; no raw calendar or countdown-only sensor |
| Heating flow/return | °C; temperature difference K or °C |
| Electricity prices | ct/kWh or EUR/kWh; tomorrow minimum requires an ISO timestamp attribute for tomorrow |
| Grid power | W or kW; positive import, negative export |
| Solar power and daily yield | Aggregate W/kW power and Wh/kWh energy; separate forecast for tomorrow |
| Daily grid import/export | Separate daily Wh/kWh counters |
| Heating oil | Liters, separate stock and estimated daily use |
| Washer, heat pump, fridge | W/kW power, daily Wh/kWh energy, available cost in EUR or cents separately |

Sensors must report the metric specified by the chosen field. Aggregate multiple sources with HA helpers where needed. Unknown states or mismatched units do not produce fabricated readings. The user is responsible for sensor periods and aggregations. This integration does not create tariff, energy, forecast or collection sensors.

## Speech examples (German)

- Nenne mir die aktuelle Vorlauf Temperatur der Heizung.
- Was sagt der Heizungsrücklauf gerade?
- Wie viel Solarstrom haben wir heute produziert?
- Wie wird das Wetter morgen früh? Brauche ich morgen einen Regenschirm?
- Wann wird der nächste Restmüll abgeholt?
- Was haben wir aktuell auf der Bring-Einkaufsliste?
- Setze Milch auf die Einkaufsliste. Streiche Butter von der Einkaufsliste.
- Steht Milch schon auf der Einkaufsliste?
- Erstelle eine Erinnerung. / Erinnere mich morgen um 18 Uhr daran, die Mülltonne rauszustellen.

Recognized local questions query configured entities rather than the LLM. Ambiguous topics may prompt clarification. Recognition is rule-based, not general semantic AI; unsupported historical periods or metrics are not implemented. The supplied speech pipeline and grammar remain German; UI/documentation support German and English.

### Shopping list

The selected list is the router's default. Only explicit single-item mutations are supported; no fuzzy deletion, bulk clear or automatic splitting of multiple items. Exact open-item names are matched case-insensitively; duplicate additions are avoided. After a mutation the open list is checked again. Bring! requires Internet connectivity. When using multiple agents and native shopping-list helpers, ensure the original local Assist handler does not select a different list before the request reaches the Tablet Assist router.

### Reminders

Explicitly enable in Options. One active reminder is persisted locally in HA, with no legacy helper dependency. After a collection query, Jarvis proposes the previous evening at 18:00 (or, if that time passed, potentially five minutes in the future before collection). Confirm with Ja, decline with Nein or revise the time with “Lieber um 19 Uhr” and reconfirm. The dialogue window is 60 seconds within the same conversation. Full clock times and relative minutes/hours/days are supported. “Welche Erinnerung ist aktiv?” reads the active reminder; “Lösche meine Erinnerung” requests confirmation before deletion. Existing reminders are never overwritten automatically.

At the due time, a Home Assistant notification appears. Optionally choose an already configured Echo room for an announcement; the existing quiet-time and availability checks apply. Do not use confidential content: Alexa may retrieve public short-lived audio URLs. Reminders/notifications are shared, not personal. On restart an overdue notification is delivered; no Echo announcement after a prolonged delay. Disabled reminders retain a paused saved item; re-enabling loads it.

## Tests and limits

The Marketplace integration and legacy installation remain separate. No automatic migration of a private installation. Automated tests use synthetic states and fake services, not real item mutations, devices, accounts or audio. A fresh real HA installation, Bring!, forecasts, collection dates, Android and Echo playback still need end-to-end validation.

## Context and optional learning

In Intelligent or Automatic conversation mode, Jarvis can resolve supported short follow-up questions from the same local home-data conversation: “Und der Rücklauf?” after heating flow, “Und morgen?” after weather, or “Und morgen früh?” after rain. Manual mode requires an explicitly started conversation. The context expires after at most 90 seconds and obeys existing turn limits. Changing topics or ending the conversation clears it. It stores only the last intent ID, not conversation history. Native Assist handling, device actions, reminder and announcement dialogs retain priority. Requests must reach the Tablet Assist router.

Enable **Optional learning** explicitly in integration Options (off by default). Inform people using the shared tablet. Only unmatched generic home-data phrases from a restricted vocabulary are normalized into suggestions. No audio recording, general transcript archive, arbitrary names, numbers, addresses or dictation. Up to 30 suggestions in RAM, expiring 24 hours after last observation or on restart. No user, device or conversation IDs are stored in suggestions. Normal HA/LLM debugging and conversation functions are independent.

In **Tablet Assist → Learning**, an administrator can inspect, choose a supported read-only intent, approve or dismiss a phrase. Administrators may manually enter a generic phrase that matches the vocabulary and is not already classified. Up to 100 approved aliases are stored locally. Shopping mutations, device control, reminders and other actions cannot be taught. Data sources and permissions are checked again on every request. Turning learning off pauses lookup; Clear learning data removes approved aliases and current suggestions. No automatic model training or external learning service. Commands remain German.

Examples: “Wie hoch ist die Vorlauftemperatur?” → “Und der Rücklauf?”; “Was sagt das Wetter?” → “Und morgen?”. A missed generic query can be answered locally once an administrator has approved its mapping.
