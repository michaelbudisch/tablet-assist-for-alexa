FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 sox libsox-dev ffmpeg && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-deps torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128 \
 && printf 'torch==2.8.0\ntorchaudio==2.8.0\ntransformers==5.15.1\nqwen-tts-hf==0.1.1.post1\n' > /tmp/constraints.txt \
 && python -m pip install -c /tmp/constraints.txt faster-qwen3-tts==0.5.4 transformers==5.15.1 qwen-tts-hf==0.1.1.post1 flask==3.1.2 waitress==3.0.2
RUN python -c "from importlib.metadata import version; assert version('transformers') == '5.15.1'; assert version('qwen-tts-hf') == '0.1.1.post1'; print('Faster Qwen dependency versions verified')"
WORKDIR /app
COPY server.py reference_voice.py prepare_variants.py /app/
EXPOSE 10502
CMD ["python", "server.py"]
