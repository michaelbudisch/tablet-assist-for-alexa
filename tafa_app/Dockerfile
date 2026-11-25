FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 libstdc++6 libespeak-ng1 espeak-ng-data libsndfile1 ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir "numpy==1.26.4" "piper-tts==1.8.0" "faster-whisper==1.2.1" "websockets==14.2" \
    && python -m pip check
# Keep NumPy 1.26.x: from NumPy 2.4, official x86 wheels target x86-64-v2.
# Generic virtual-machine CPU profiles may lack this baseline.
RUN python -c "import numpy; assert numpy.__version__ == '1.26.4', numpy.__version__; from piper import PiperVoice; from faster_whisper import WhisperModel; print('TAFA CPU speech imports OK', numpy.__version__)"
WORKDIR /opt/tafa
COPY server.py installer.py speech_proxy.py auto_setup.py speech_source.py model_store.py wyoming_picker.py settings_ui.py endpoint_checks.py control_center_view.py ./
COPY control_center.css control_center.js ./
# Fail container builds early if the module is not packaged.
RUN python -c "from wyoming_picker import discover_wyoming_stt, save_wyoming_selection; print('TAFA Wyoming picker import OK')"
COPY bundle ./bundle
EXPOSE 8099 5000
CMD ["python", "server.py"]
