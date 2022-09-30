# Dockerfile
#

# Base
FROM python:3.10-slim-buster as base_os

# Builder requirements and deps
FROM base_os as builder

ENV PYTHONDONTWRITEBYTECODE=1
ADD requirements.txt /builder/requirements.txt

WORKDIR /builder
RUN apt-get update && apt-get install libpq-dev gcc -y
RUN apt-get remove gcc --purge -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean autoclean \
    && apt-get autoremove --yes
RUN pip install --user -r requirements.txt

# Final image
FROM base_os as pre-final
COPY --from=builder /root/.local/bin /usr/local/bin/
COPY --from=builder /root/.local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages/

# Final stage
FROM pre-final

WORKDIR /opt/tuf-repository-service-api
RUN mkdir /data
COPY app.py /opt/tuf-repository-service-api
COPY entrypoint.sh /opt/tuf-repository-service-api
COPY tuf_repository_service_api /opt/tuf-repository-service-api/tuf_repository_service_api
COPY tests /opt/tuf-repository-service-api/tests
ENTRYPOINT ["bash", "entrypoint.sh"]
