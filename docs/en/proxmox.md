# Optional CPU speech server on Proxmox

[Deutsch](../proxmox.md) · [Project](../../README.md) · [Setup guide](setup-guide.md)

**Not required for every TAFA setup:** The TAFA App can run CPU Piper and Faster-Whisper on its own. This guide is for running these CPU services in a **new Debian LXC on Proxmox VE**. Optional Alexa MP3 HTTPS delivery is a **separate** feature; ordinary Android-to-Echo Bluetooth playback needs no public gateway.

## Recommended: new combined LXC

Run from an interactive **root shell on the Proxmox host**:

```bash
curl -fsSLo /root/tafa-pve-install.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/quick-install.sh
bash /root/tafa-pve-install.sh
```

Review the downloaded script before running it. The English wizard asks for a **free CT ID**, custom **container hostname**, template/storage, networking, resources, and optional GPU and Alexa audio host. Default resources are **4 vCPU, 4 GiB RAM, 32 GiB disk**. After confirmation, it creates a **new** CT and prompts for a container root password. Never run this first-install wizard against a production CT.

| Port | Service | Public Internet |
| --- | --- | --- |
| `5000` | Piper HTTP/TTS | **Never** |
| `10300` | Wyoming Whisper/STT | **Never** |
| `5001` | MP3 generator for optional Alexa messages | **Never** |
| `8080` | Temporary MP3 files for internal proxy delivery | **Never directly** |

Inside the **new CT**, `tafa-info` lists services and endpoints. `tafa-setup` configures optional dedicated HTTPS after DNS, routing and certificate requirements are met. The installer does **not** create router port forwards.

## Connect to Home Assistant

1. Set **TAFA → Settings → Speech mode: External**.
2. Enter `http://CPU-SERVER-IP:5000` as Piper under **TAFA → Connections → CPU fallback**.
3. Add **Wyoming Protocol** under **HA → Settings → Devices & services**, host **CPU-SERVER-IP**, port **10300**.
4. Choose the resulting **actual** CPU `stt.*` entity in **TAFA → Connections**. Restart HA Core after integration updates and TAFA after settings changes when required.
5. Check the **TAFA Lokal** Assist pipeline's STT, conversation and **Tablet Assist Stream** routers, then run an actual voice test.

## Existing central Nginx/HTTPS proxy

If another proxy CT already handles public TCP 80/443, **keep that forwarding**. In the wizard choose **HTTPS mode: shared**, enter the **real ID of your existing Nginx CT**, and explicitly approve the creation of **one new audio site**. There is **no universal proxy CT number**. Review/back up the existing domain, sites and certificates first. `proxmox/audit-shared-proxy.sh` is a read-only audit tool.

For **shared**, internal MP3 delivery must be reachable from the selected proxy IP only. For **dedicated**, the temporary file server binds to `127.0.0.1:8080`, which another CT cannot reach. The `dedicated`, `shared` and `none` modes are alternatives. See [Nginx/HTTPS](nginx-proxy.md). Public audio hosting is required **only** for optional Alexa MP3 announcements; the MP3 generator and public URL must refer to the same backend.

**DuckDNS:** Register the subdomain on your DuckDNS account first. The optional updater asks for a **DuckDNS account token**, which is **not** a TAFA API token. Never commit it. Restrict private worker ports with your firewall.

## Resume an interrupted fresh installation

Only for a **new, still-empty** CT or the explicitly supported incomplete Python-venv stage:

```bash
curl -fsSLo /root/tafa-resume.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/resume-install.sh
bash /root/tafa-resume.sh
```

Supply **your** CT ID, and if using shared mode the **actual** proxy CT ID. This is **not** a generic repair tool for arbitrary production installations.

## Verify inside the new CT

```bash
tafa-info
systemctl status jarvis-piper jarvis-mp3 jarvis-whisper jarvis-audio
curl -fsS http://127.0.0.1:5001/health
journalctl -u jarvis-whisper -n 50 --no-pager
```

Token-free internal generator/worker ports must stay on the **trusted LAN**; never publish 5000, 5001, 10300 or 8080. An optional [GPU worker](worker.md) is configured independently.

**Legacy only:** `proxmox/update-mp3-generator.sh` updates an **older token-based** MP3 server. It is **not** a clean-install step and must never be run on the PVE host.
