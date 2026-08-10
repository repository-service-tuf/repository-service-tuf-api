# Base
FROM python:3.14-slim@sha256:a7fb1e634c4a578f9e0bd6327f11a3cde11b7a9395f48e24360c0988bcc5c2bc AS base_os

# Builder requirements and deps
FROM base_os AS builder

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /builder

# Install build dependencies
RUN apt-get update && apt-get install libpq-dev gcc -y

# Install pipenv
RUN pip install --upgrade pip && pip install pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile* /builder/

# Install dependencies using pipenv
# --system flag installs to system python, not virtualenv
# --deploy flag ensures Pipfile.lock is up to date
RUN pipenv install --system --deploy

# Clean up
RUN apt-get remove gcc --purge -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean autoclean \
    && apt-get autoremove --yes

# Final image
FROM base_os AS pre-final
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin /usr/local/bin/

# Final stage
FROM pre-final

WORKDIR /opt/repository-service-tuf-api
RUN mkdir /data
COPY app.py /opt/repository-service-tuf-api
COPY entrypoint.sh /opt/repository-service-tuf-api
COPY repository_service_tuf_api /opt/repository-service-tuf-api/repository_service_tuf_api
COPY tests /opt/repository-service-tuf-api/tests
ENTRYPOINT ["bash", "entrypoint.sh"]