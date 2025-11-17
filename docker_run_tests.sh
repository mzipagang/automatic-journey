#!/bin/bash
set -e
docker compose down
docker compose up -d --wait --build
docker compose exec -T --user root map-onsite-apis poetry run pytest "$@"
docker compose down
