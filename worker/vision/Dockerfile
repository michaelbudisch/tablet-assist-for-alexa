FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py detection.py priority_gate.py test_server.py test_priority_gate.py ./
USER 65534:65534
EXPOSE 10503
CMD ["python", "server.py"]
