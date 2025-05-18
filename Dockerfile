# syntax = docker/dockerfile:1.5

FROM python:3.12

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt && \
    pip cache purge

COPY src/ ./src/

EXPOSE 8086
HEALTHCHECK CMD curl -f http://127.0.0.1:8086 || exit 1

CMD ["python", "src/app.py"]
