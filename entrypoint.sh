#!/bin/bash
#

if [[ -z ${SECRETS_RSTUF_SSL_CERT} ]]; then
    uvicorn app:rstuf_app --host 0.0.0.0 --port 80
else
    if [[ -z ${SECRETS_RSTUF_SSL_KEY} ]]; then
        echo "Missing variable SECRETS_RSTUF_SSL_KEY"
        exit 1
    fi
    uvicorn app:rstuf_app --host 0.0.0.0 --port 443 --ssl-keyfile ${SECRETS_RSTUF_SSL_KEY} --ssl-certfile ${SECRETS_RSTUF_SSL_CERT}
fi
