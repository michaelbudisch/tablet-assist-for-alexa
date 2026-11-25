"""Admin-only Ingress setup page; no external port or HA API token."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from html import escape
from secrets import token_urlsafe, compare_digest
from installer import install, status

CONFIG = Path("/homeassistant")
BUNDLE = Path(__file__).parent / "bundle"
CSRF = token_urlsafe(32)
REPO = "https://github.com/michaelbudisch/tablet-assist-for-alexa"
MARKET = "https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration"

def page(message=""):
    rows = "".join("<li><strong>" + escape(k) + "</strong> — " + escape(v) + "</li>" for k,v in status(CONFIG).items())
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TAFA</title><style>
    :root{{color-scheme:light dark;font:16px system-ui}}body{{max-width:850px;margin:24px auto;padding:0 16px}}section{{border:1px solid #8886;border-radius:14px;padding:18px;margin:16px 0}}label{{display:block;margin:12px 0}}input{{display:block;width:100%;box-sizing:border-box;padding:10px;font:inherit}}button,a{{font:inherit}}button{{padding:12px 18px;border-radius:8px;cursor:pointer}}a{{color:inherit}}small{{opacity:.8}}h1{{margin-bottom:4px}}li{{margin:8px 0}}
    </style><h1>TAFA</h1><p>Local voice assistant · Einrichtungszentrale · Experimental 0.1.0</p>
    <section><h2>1 · Backend status / Backend-Status</h2><ul>{rows}</ul><p role="status">{escape(message)}</p><small>Installed means files are present, not that the integration is loaded. / Installiert bedeutet: Dateien vorhanden, nicht zwingend geladen.</small></section>
    <section><h2>2 · Speech servers / Sprachserver</h2><p>Prepare your external CPU speech server and optional GPU worker. / Externe Sprachserver zuerst einrichten.</p><p><a href="{REPO}/blob/main/docs/proxmox.md" target="_blank" rel="noopener">CPU DE</a> · <a href="{REPO}/blob/main/docs/en/proxmox.md" target="_blank" rel="noopener">CPU EN</a> · <a href="{REPO}/blob/main/docs/worker.md" target="_blank" rel="noopener">GPU DE</a> · <a href="{REPO}/blob/main/docs/en/worker.md" target="_blank" rel="noopener">GPU EN</a></p></section>
    <section><h2>3 · Install missing integrations / Fehlende Integrationen installieren</h2><p>New installations only. Existing files are never overwritten. Create a Home Assistant backup first. / Nur Neuinstallation; vorhandene Dateien bleiben unverändert. Vorher HA-Sicherung erstellen.</p>
    <form method="post" action="./"><input type="hidden" name="csrf" value="{CSRF}">
    <label>CPU host / CPU-Host<input name="cpu_host" required placeholder="speechserver.local" maxlength="253"></label>
    <label>GPU host (optional) / GPU-Host (optional)<input name="gpu_host" placeholder="gpu.local" maxlength="253"></label>
    <label>CPU Wyoming STT entity / STT-Entität<input name="cpu_stt" required placeholder="stt.faster_whisper" maxlength="160"></label>
    <label>GPU STT entity (optional)<input name="gpu_stt" placeholder="stt.gpu_whisper" maxlength="160"></label>
    <label>Conversation agent (optional) / Konversationsagent<input name="llm_agent" placeholder="conversation.home_assistant" maxlength="160"></label>
    <button type="submit">Install missing backend files / Fehlende Backend-Dateien installieren</button></form>
    <p><small>No dashboard files, credentials, YAML configuration or existing integrations are modified. / Keine Dashboard-Dateien, Zugangsdaten, YAML-Konfiguration oder vorhandenen Integrationen werden verändert.</small></p></section>
    <section><h2>4 · Home Assistant setup / HA-Einrichtung</h2><p>After copying new integration files, restart HA manually, then add and configure both integrations in Devices &amp; services. / Nach der Dateiinstallation HA manuell neu starten und beide Integrationen unter Geräte &amp; Dienste einrichten.</p>
    <p><a href="/config/integrations" target="_top">Devices &amp; services / Geräte &amp; Dienste</a> · <a href="/tablet_assist_for_alexa" target="_top">Tablet Assist voice center / Sprachzentrale</a></p>
    <p>Alternatively install only the base integration through <a href="{escape(MARKET)}" target="_blank" rel="noopener">Marketplace</a>. Do not install it twice.</p></section>
    <section><h2>5 · Android Device Bridge &amp; Multiroom</h2><p><a href="{REPO}/blob/main/android/README.de.md" target="_blank" rel="noopener">Android DE</a> · <a href="{REPO}/blob/main/android/README.md" target="_blank" rel="noopener">Android EN</a> · <a href="{REPO}/blob/main/homeassistant/examples/MULTIROOM.de.md" target="_blank" rel="noopener">Multiroom DE</a> · <a href="{REPO}/blob/main/homeassistant/examples/MULTIROOM.md" target="_blank" rel="noopener">Multiroom EN</a></p><p>Use native HA setup and explicit device permissions. This preview does not automatically configure rooms or start microphones or cameras.</p></section></html>"""

class Handler(BaseHTTPRequestHandler):
    def allowed(self):
        return self.client_address[0] == "172.30.32.2"
    def send_page(self, message="", code=200):
        data = page(message).encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'self'; base-uri 'none'")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if not self.allowed():
            self.send_error(403)
            return
        self.send_page()
    def do_POST(self):
        if not self.allowed():
            self.send_error(403)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 8192 or self.headers.get_content_type() != "application/x-www-form-urlencoded":
                self.send_error(400)
                return
            form = {k: v[0] for k,v in parse_qs(self.rfile.read(size).decode(), max_num_fields=12).items()}
            if not compare_digest(form.pop("csrf", ""), CSRF):
                self.send_error(403)
                return
            installed = install(CONFIG, BUNDLE, form)
            self.send_page("Installed / Installiert: " + ", ".join(installed) + ". Restart HA manually." if installed else "No changes / Keine Änderungen.")
        except (ValueError, OSError, SyntaxError) as exc:
            self.send_page("Installation stopped / Installation abgebrochen: " + str(exc), 400)

if __name__ == "__main__":
    HTTPServer(("0.0.0.0",8099), Handler).serve_forever()
