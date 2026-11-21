from pathlib import Path
import os, re, time
folder=Path(os.environ.get('JARVIS_AUDIO_DIR','/var/lib/jarvis/audio'))
for p in folder.iterdir():
    try:
        if re.fullmatch(r'[a-f0-9]{32}\.mp3(?:\.tmp)?',p.name) and time.time()-p.lstat().st_mtime>900:
            p.unlink()
    except OSError:
        pass
