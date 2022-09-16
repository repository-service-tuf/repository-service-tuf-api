#!/bin/bash
#

if [[ -z ${SECRETS_KAPRIEN_SSL_CERT} ]]; then
    uvicorn app:kaprien_app --host 0.0.0.0 --port 80
else
    if [[ -z ${SECRETS_KAPRIEN_SSL_KEY} ]]; then
        echo "Missing variable SECRETS_KAPRIEN_SSL_KEY"
        exit 1
    fi
    uvicorn app:kaprien_app --host 0.0.0.0 --port 443 --ssl-keyfile ${SECRETS_KAPRIEN_SSL_KEY} --ssl-certfile ${SECRETS_KAPRIEN_SSL_CERT}
fi
