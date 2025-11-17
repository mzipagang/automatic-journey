#!/bin/bash

export SERVICE_NAME="media-onsite-apis"

export LOG_LEVEL="info"
export DD_TRACE_OTEL_ENABLED="true"

# Start the api
ddtrace-run uvicorn app.main:app --host 0.0.0.0 --port "${SERVICE_PORT:-8080}" --proxy-headers ${UVICORN_OPTS}
