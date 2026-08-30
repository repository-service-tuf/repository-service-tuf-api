# Base
FROM python:3.13-slim@sha256:eb43ff125d8d58d7449dcba7d336c23bcac412f526d861db493b9994d8010280 AS base_os

# Builder requirements and deps
FROM base_os AS builder

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /builder

# Install build dependencies
RUN apt-get update && apt-get install libpq-dev gcc -y

# Install uv
RUN pip install --upgrade pip && pip install uv

# Copy project configuration files
COPY pyproject.toml README.rst uv.lock* /builder/

# Install dependencies using uv sync
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --no-dev --no-install-project

# Final stage
FROM base_os

WORKDIR /opt/repository-service-tuf-api
RUN apt-get update && apt-get install libpq5 -y \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /builder/.venv /opt/repository-service-tuf-api/.venv
ENV PATH="/opt/repository-service-tuf-api/.venv/bin:$PATH"
RUN mkdir /data
COPY app.py /opt/repository-service-tuf-api
COPY entrypoint.sh /opt/repository-service-tuf-api
COPY repository_service_tuf_api /opt/repository-service-tuf-api/repository_service_tuf_api

# Only keep this if you actively run pytest against the final production container!
# COPY tests /opt/repository-service-tuf-api/tests

ENTRYPOINT ["bash", "entrypoint.sh"]