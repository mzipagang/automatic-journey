#!/bin/sh
echo $(pwd)
docker pull docker-all.artifactory.8451.cloud/qep/api-test-runner:latest

docker run --rm -it \
    --platform linux/amd64 \
    --add-host=host.docker.internal:host-gateway \
    --hostname api-test-runner \
    --name api-test-runner \
    --env POSTMAN_COLLECTION_ID="$POSTMAN_COLLECTION_ID" \
    --env POSTMAN_ENVIRONMENT_ID="$POSTMAN_ENVIRONMENT_ID" \
    --env POSTMAN_API_KEY="$POSTMAN_API_KEY" \
    --env API_TESTS_ARGS="$API_TESTS_ARGS" \
    --env API_TESTS_BUILD_BREAKER_ENABLED=true \
    --env API_TESTS_ACCOUNT_NAME="$API_TESTS_ACCOUNT_NAME" \
    --env API_TESTS_ACCOUNT_PASSWORD="$API_TESTS_ACCOUNT_PASSWORD" \
    --env API_TESTS_CLIENT_ID="$API_TESTS_CLIENT_ID" \
    --env API_TESTS_CLIENT_SECRET="$API_TESTS_CLIENT_SECRET" \
    --env API_TESTS_IS_AUTOMATION="$API_TESTS_IS_AUTOMATION" \
    --volume "$(pwd)/reports:/home/e451/reports" \
    docker-all.artifactory.8451.cloud/qep/api-test-runner:latest

exit $?