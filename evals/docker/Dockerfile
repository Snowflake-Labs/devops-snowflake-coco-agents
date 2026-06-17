FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    curl \
    perl \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# uv for pytest execution
ENV CORTEX_CHANNEL=beta
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Pre-cache pytest + json reporter (no snowflake-connector needed — tests are file-only)
RUN uvx --with pytest==8.4.1 --with pytest-json-ctrf==0.3.5 pytest --version

# Cortex Code CLI — beta channel required for cortex exec
ARG CLI_CACHE_BUST=2026-06-17
RUN curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh -o /tmp/install.sh \
    && SKIP_PODMAN=1 NON_INTERACTIVE=1 CORTEX_CHANNEL=beta sh /tmp/install.sh \
    && rm /tmp/install.sh

ENV CC_AUTO_UPDATE=y
ENV CC_SKIP_UPDATE_CHECK=0

WORKDIR /app
