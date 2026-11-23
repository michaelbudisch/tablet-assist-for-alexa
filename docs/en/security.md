# Security and privacy

**English** | [Deutsch](../security.md) · [Project overview](../../README.md)

- Local speech processing: the dashboard does not make additional continuous microphone recordings. Native Assist and its debugging or caching features may retain requests; review HA retention settings.
- Never publish credentials, actual device IPs, HA configuration backups, audio recordings or personal voices. Local JSON configuration, secrets, virtual environments and model files are excluded from Git.
- Do not expose LAN services to the Internet. Wyoming and Piper have no client authentication in this preview. MP3 and GPU synthesis use API keys; plain HTTP is intended for trusted networks only. Use protected connections for remote access.
- Alexa is an optional cloud service, not fully local. HTTPS announcement files remain accessible through a random link for up to 15 minutes. Do not use confidential content. Restrict the reverse proxy to the audio file route, not the API. Block access to other speech services.
- Automatic hints in the legacy setup start disabled and must respect quiet schedules. Independently review security before production use.
