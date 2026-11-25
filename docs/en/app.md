# Install TAFA as a Home Assistant app

[Deutsch](../app.md)

**Experimental 0.1.0.** Home Assistant OS 2026.11+, amd64/aarch64. This is a setup app, not a replacement for the external speech services.

1. [Add the TAFA app repository](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa) or open Settings → Apps → Install app → Repositories and add `https://github.com/michaelbudisch/tablet-assist-for-alexa`.
2. Install and start TAFA; open Web UI. Keep protection enabled; no public port is required.
3. Create a Home Assistant backup. Prepare the [CPU speech server](proxmox.md), add its Wyoming integration and optionally prepare the [GPU worker](worker.md).
4. Enter the speech server host and STT entity. The optional GPU fields may be left blank. Install missing files with the button. Existing integration directories are skipped.
5. Restart Home Assistant manually, add **Tablet Assist for Alexa** and **Jarvis Tablet Audio** in Devices & services and configure pipelines and worker options.
6. Install [TAFA Device Bridge](../../android/README.md) and follow the [Multiroom guide](../../homeassistant/examples/MULTIROOM.md).

## Boundaries and updates

The app copies the bundled publicly committed components into `custom_components` only. It does not modify configuration.yaml, secrets, private dashboards or existing entries. Uninstalling TAFA does not remove installed integrations. Do not mix update routes or assume app upgrades automatically update Core components. The base integration can alternatively be installed using [Marketplace](marketplace.md), which does not install Apps.

No automatic pairing, microphone/camera activation, worker deployment, or legacy migration. A fresh HA OS install, Ingress rendering, pipeline setup, real device audio and multiroom behavior remain unverified. Use a test instance first.
