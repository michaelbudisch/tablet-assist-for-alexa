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

**English interface and custom container name:** All setup dialogs, recovery prompts and CT console status screens are in English. Immediately after selecting the CT ID, the wizard asks `Container hostname [tafa-voice]`. Enter any valid single-label Linux hostname (1–63 lowercase letters, numbers or hyphens; e.g. `jarvis-speech`) or press Enter for the default. This is passed directly to Proxmox `pct create --hostname`; it does not rename an existing or already running installation.

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

## Recover an incomplete CT after `runuser ... Permission denied`

An earlier installer used `umask 077` while creating the Python virtual environment, preventing the `jarvis-local` service account from opening installed packages. Fresh installations now use `umask 022` **only around non-secret venv/pip installation**.

If a brand-new CT already exists and failed **specifically at `runuser: failed to execute .../venv/bin/python: Permission denied` immediately after pip installation**, execute this in the **Proxmox host shell**:

```bash
curl -fsSLo /root/tafa-resume.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/resume-install.sh && bash /root/tafa-resume.sh
```

The recovery wizard checks that the interrupted CT has the expected partial install and no existing runtime configuration, asks for its ID, fresh registered audio hostname, optional GPU URL and the existing proxy CT, then requires the explicit `FORTSETZEN` confirmation. It fixes only the Python venv file permissions and completes the existing install without recreating or destroying a CT. It prepares a **new** HTTPS site on the existing proxy, leaving current websites untouched, and prints the subsequent certificate commands.

## Fresh installation behind an existing central Nginx proxy

A new DuckDNS domain can be registered in the [DuckDNS dashboard](https://www.duckdns.org); the published update endpoint maintains existing domains and does not register names. Use a separate new name, leaving the existing domain and router forwarding intact.

1. Run the PVE host installer shown above; choose a **new CT** and select HTTPS mode `shared`, then the **existing proxy CT ID** (for example 101). Explicitly confirm the addition of a new audio virtual host.
2. The new CT installs Piper, Whisper and MP3 generation, but **no second public Nginx**. Temporary MP3 files on port 8080 respond only to requests from the chosen Nginx proxy IP. Restrict internal network access with host/guest firewalls too.
3. The host wizard copies new, isolated setup scripts to the existing proxy CT and prepares **one new audio hostname**, without modifying pre-existing Nginx sites or certificates.
4. After DuckDNS points at your existing public address, run the printed `certbot certonly --webroot` and `install-nginx-proxy.sh enable ... --shared` commands **on the existing proxy CT**; 80/443 continue to point there.
5. Optionally run `install-duckdns-updater.sh NEW-NAME.duckdns.org` from the new setup folder on the existing proxy CT. The DuckDNS-account token is prompted privately and stored only in a local root-only file (0600), updated every ten minutes. It is not a TAFA API token.
6. In the **test HA installation**, configure Piper, Wyoming, new CT's MP3 generator and the new public audio hostname together. A new domain pointing to the new CT cannot serve files generated on the old CT: always migrate the MP3-generator URL and public-audio URL as a pair after successful tests.

Keep the old public hostname, all pre-existing proxy sites, and the production HA installation unchanged during testing.

## Optional HTTPS proxy

**With the new combined single-CT installer Nginx is already installed.** Run `tafa-setup` inside the new guest once public DNS/routing has been prepared. A separate proxy CT remains available as an alternative in the [Nginx guide](nginx-proxy.md). No public proxy is needed for tablet-to-Echo Bluetooth.
