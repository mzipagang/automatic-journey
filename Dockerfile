#syntax=docker-all.artifactory.8451.cloud/docker/dockerfile:1

# This dockerfile uses a multi-stage build strategy to separate the build
# and runtime environments and to keep the final image as small as possible.

ARG PYTHON_IMAGE=docker-all.artifactory.8451.cloud/core-images/python
ARG PYTHON_VERSION=3.12
ARG PYTHON_BUILDER_VERSION=${PYTHON_VERSION}-build
ARG VIRTUAL_ENV=/opt/venv
ARG POETRY_VERSION=1.8.3

#
# Build stage
#

FROM ${PYTHON_IMAGE}:${PYTHON_BUILDER_VERSION} AS build

# Use a clean working directory for the build.
WORKDIR /opt/src
COPY pyproject.toml poetry.lock ./

# Collect depenencies into a virtual environment.
ARG VIRTUAL_ENV
ENV VIRTUAL_ENV=${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"
RUN python -m venv --copies ${VIRTUAL_ENV}

ARG POETRY_VERSION
ENV POETRY_CACHE_DIR=/opt/src/.cache

RUN \
    --mount=type=secret,id=ARTIFACTORY_USERNAME \
    --mount=type=secret,id=ARTIFACTORY_PASSWORD \
\
    set -eux \
    && pip install --upgrade pip \
\
    && pip install poetry==${POETRY_VERSION} \
    && poetry config virtualenvs.create false \
    && export POETRY_HTTP_BASIC_ARTIFACTORY_USERNAME=$(cat /run/secrets/ARTIFACTORY_USERNAME) \
    && export POETRY_HTTP_BASIC_ARTIFACTORY_PASSWORD=$(cat /run/secrets/ARTIFACTORY_PASSWORD) \
    && poetry install --without dev --no-root \
    && rm -rf ${POETRY_CACHE_DIR}

#
# App stage
#

FROM ${PYTHON_IMAGE}:${PYTHON_VERSION} AS app

ARG PYTHON_IMAGE
ARG PYTHON_VERSION
ARG PYTHON_BUILDER_VERSION

# Add labels about the images used to build this image.
LABEL com.e451.metadata.runtime_image=${PYTHON_IMAGE}:${PYTHON_VERSION}
LABEL com.e451.metadata.build_image=${PYTHON_IMAGE}:${PYTHON_BUILDER_VERSION}

ARG VIRTUAL_ENV

# Copy the virtual environment from the build stage.
COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}
ENV VIRTUAL_ENV=${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# Bring in runtime dependencies.
COPY app ./app/
COPY run_app.sh ./

# Production settings of UVICORN by default. Docker compose file overrides it for local development.
ARG UVICORN_OPTS=--workers\ 5
ENV UVICORN_OPTS=${UVICORN_OPTS}
ARG LOG_FORMAT_OUTPUT=json
ENV LOG_FORMAT_OUTPUT=${LOG_FORMAT_OUTPUT}

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose the service port.
ENV SERVICE_PORT=8080
EXPOSE ${SERVICE_PORT}

# Run the service.
CMD ["./run_app.sh"]
