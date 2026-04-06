# Base
FROM python:3.13-slim AS base_os

# Builder requirements and deps
FROM base_os AS builder

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    git \
    curl \
    wget \
    make \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --upgrade pip && pip install pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile* /builder/

# Install dependencies using pipenv
# --system flag installs to system python, not virtualenv
# --deploy flag ensures Pipfile.lock is up to date
RUN pipenv install --system --deploy

# Final image
FROM base_os AS pre-final

# Install runtime dependencies and tools needed for functional tests
RUN apt-get update && apt-get install -y \
    libpq5 \
    git \
    curl \
    wget \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin /usr/local/bin/

# Final stage
FROM pre-final

RUN useradd -u 1000 -m tuf

WORKDIR /opt/repository-service-tuf-api
RUN mkdir /data

# Copy application code
COPY . /opt/repository-service-tuf-api

# Install the package itself to ensure repository_service_tuf_api is in site-packages
RUN pip install .

RUN chown -R tuf:tuf /opt/repository-service-tuf-api /data

USER 1000
ENTRYPOINT ["bash", "entrypoint.sh"]