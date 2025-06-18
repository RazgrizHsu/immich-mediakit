# syntax = docker/dockerfile:1.5

FROM python:3.12

WORKDIR /app

ARG MKIT_PORT=8086
ARG MIKT_PORTWS=8087

ENV PORT=${MKIT_PORT}
ENV PORTWS=${MIKT_PORTWS}

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt && \
    pip cache purge

COPY src/ ./src/

EXPOSE ${PORT} ${PORTWS}
HEALTHCHECK CMD curl -f http://127.0.0.1:${PORT} || exit 1

CMD ["python", "-m", "src.app"]
