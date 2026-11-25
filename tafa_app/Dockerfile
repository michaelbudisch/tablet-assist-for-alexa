FROM python:3.12-slim
WORKDIR /opt/tafa
COPY server.py installer.py ./
COPY bundle ./bundle
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8099
CMD ["python", "server.py"]
