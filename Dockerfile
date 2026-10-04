FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY baidu_voice_server.py ./
COPY outputs/voice-first-feed-eyes-overlay.html ./outputs/voice-first-feed-eyes-overlay.html
ENV HOST=0.0.0.0 PORT=10000 PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["python", "baidu_voice_server.py"]
