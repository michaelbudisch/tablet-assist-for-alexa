# CPU speech server

**English** | [Deutsch](../proxmox.md) · [Project overview](../../README.md)

Requirements: current Proxmox VE or Debian 12/13 with systemd. Start with 4 vCPUs, 4 GiB RAM and 20 GiB disk, depending on model size. Check the architecture and Python requirements of dependencies. No NVIDIA GPU is required. Downloading models requires Internet access; inference can run locally afterwards.

## New VM/container

Download a Debian template in Proxmox and clone or extract this repository. On the Proxmox host as administrator:

```bash
bash proxmox/create-ct.sh CTID TEMPLATE_VOLUME STORAGE [BRIDGE]
```

Replace placeholders with an unused CT ID, a Debian template volume, storage and optionally a bridge. Review storage and networking first. The script asks for the CT ID as confirmation and creates a new unprivileged DHCP container without port forwarding. Alternatively, inside an existing **empty** Debian VM/CT:

```bash
sudo bash proxmox/install-speechserver.sh
```

The script refuses to run on the PVE host or overwrite an existing installation or occupied ports. It installs a Python environment, Piper, Whisper, FFmpeg, the MP3 API, temporary audio delivery, systemd services and a cleanup timer. The default voice is German Thorsten. Dependencies and models may change; a fresh installation still requires end-to-end validation.

## Verify

```bash
systemctl status jarvis-piper jarvis-mp3 jarvis-whisper jarvis-audio
curl -fsS http://127.0.0.1:5001/health
journalctl -u jarvis-whisper -n 50 --no-pager
```

The local configuration remains in `/etc/jarvis-local.env` (root only). The current MP3 generator needs **no additional API token**. Enter `http://SERVER:5001` and the public HTTPS audio origin in TAFA Options. Keep generator port 5001 restricted to your trusted private LAN. Use CPU host port 10300 for Wyoming STT.

| Port | Service | Access |
|---|---|---|
| 5000 | Piper HTTP (WAV) | Trusted internal clients only |
| 5001 | MP3 API | Internal, API key |
| 10300 | Wyoming STT | Internal only |
| 8080 | Temporary audio files | Internal; optional restricted HTTPS proxy |

Configure firewall rules to allow only the required HA and proxy hosts. No automatic router configuration. The GPU address initially remains empty; see [GPU worker](worker.md).

## Optional HTTPS proxy

For Alexa announcements, follow the [Nginx guide](nginx-proxy.md). No proxy is required for ordinary tablet-to-Echo Bluetooth output.
