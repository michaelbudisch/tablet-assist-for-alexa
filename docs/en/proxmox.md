# CPU speech server

**English** | [Deutsch](../proxmox.md) · [Project overview](../../README.md)

Requirements: current Proxmox VE or Debian 12/13 with systemd. Start with 4 vCPUs, 4 GiB RAM and 20 GiB disk, depending on model size. Check the architecture and Python requirements of dependencies. No NVIDIA GPU is required. Downloading models requires Internet access; inference can run locally afterwards.

**Existing speech server:** To update only the MP3 generator from an older token-based version, use the source checkout inside the dedicated Debian guest and run `sudo bash proxmox/update-mp3-generator.sh`. It backs up the existing `api.py` and restarts only `jarvis-mp3.service`, rolling back if health checks fail. This does not replace Piper, Whisper, data or your proxy. Update the matching TAFA integration to 0.4.3. Never run this script on the Proxmox host. No public forwarding for port 5001.

## Recommended: one combined CT with a one-line PVE installer

For a **fresh installation**, a single unprivileged Debian LXC hosts Piper, Wyoming-Whisper, the MP3 generator, and Nginx. Existing CTs, VMs and proxy sites are never modified.

Run this in an interactive **root Proxmox VE host shell**:

```bash
curl -fsSLo /root/tafa-pve-install.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/quick-install.sh && bash /root/tafa-pve-install.sh
```

You can review `/root/tafa-pve-install.sh` before running it. The interactive wizard asks for an unused CT ID, Proxmox root/template storage, bridge and DHCP/static IP, 4 cores/4 GiB RAM/32 GiB disk defaults, and optional LAN GPU Qwen and public Alexa audio hostname. Only after confirming the CT ID is a new CT created.

It installs private Piper (5000), MP3 generation (5001), Wyoming Whisper (10300), a **loopback-only** audio file backend (127.0.0.1:8080), and Nginx. Neither public DNS nor router port forwarding is changed. HTTPS remains pending until you have a public hostname, suitable routing and a certificate.

The new container's pre-login `/etc/issue` and interactive console show IP, ports and service information; a periodic job refreshes the banner. Inside the new guest:

```bash
tafa-info               # Current IP, endpoints, service state
tafa-setup              # Guided Nginx/Certbot HTTPS completion
```

If the GUI CT console asks for a root password and none exists, enter from PVE with `pct enter CTID` and set one using `passwd root` inside the guest. Do not put passwords in scripts or logs. Only expose the Nginx 80/443 entry point when intentionally configured; **never publish** 5000, 5001, 8080, 10300, or GPU ports. If another proxy already owns port forwarding, keep it in place until a deliberate migration.

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
| 5001 | MP3 API | Trusted private LAN only, no token |
| 10300 | Wyoming STT | Internal only |
| 8080 | Temporary audio files | Internal; optional restricted HTTPS proxy |

Configure firewall rules to allow only the required HA and proxy hosts. No automatic router configuration. The GPU address initially remains empty; see [GPU worker](worker.md).

## Optional HTTPS proxy

For Alexa announcements, follow the [Nginx guide](nginx-proxy.md). No proxy is required for ordinary tablet-to-Echo Bluetooth output.
