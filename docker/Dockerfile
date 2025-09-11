ARG BASE_IMAGE=python
ARG TAG=3.10.4
FROM ${BASE_IMAGE}:${TAG} as server

ENV APP_BASE=/usr/src/app \
    LIB_BASE=/usr/src/lib \
    NAME=django-api-base \
    PATH="/root/.local/bin:$PATH"

WORKDIR ${LIB_BASE}/${NAME}
COPY apibase ${LIB_BASE}/${NAME}/apibase
COPY tests ${LIB_BASE}/${NAME}/tests
COPY pyproject.toml  ${LIB_BASE}/${NAME}/pyproject.toml
# Install uv (fast Python package manager) and sync dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh -s -- -y \
    && uv --version \
    && uv sync --group dev

CMD ["sleep", "infinity"]
