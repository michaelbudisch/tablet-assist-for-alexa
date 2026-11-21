FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends sox libsox-dev libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-deps torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128 \
 && printf 'torch==2.8.0\ntorchaudio==2.8.0\n' > /tmp/constraints.txt \
 && python -m pip install -c /tmp/constraints.txt qwen-tts==0.1.1 flask==3.1.2 waitress==3.0.2
WORKDIR /app
COPY server.py /app/server.py
EXPOSE 10501
CMD ["python", "server.py"]
