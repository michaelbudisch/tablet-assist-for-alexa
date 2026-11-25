FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 libstdc++6 libespeak-ng1 espeak-ng-data libsndfile1 ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir "piper-tts==1.8.0" "faster-whisper==1.2.1" "websockets==14.2"
RUN python -c "from piper import PiperVoice; from faster_whisper import WhisperModel; print('TAFA CPU speech imports OK')"
WORKDIR /opt/tafa
COPY server.py installer.py speech_proxy.py auto_setup.py ./
COPY bundle ./bundle
EXPOSE 8099 5000
CMD ["python", "server.py"]
