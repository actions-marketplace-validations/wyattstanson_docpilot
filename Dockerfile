# DocPilot GitHub Action container.
# Build context is the repository root (where action.yml lives).
FROM python:3.11-slim

# git is needed for diff extraction and pushing fix branches.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# GitHub mounts the workspace owned by a different UID than the container's
# root user; without this, git refuses to operate ("dubious ownership").
RUN git config --system --add safe.directory '*'

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /opt/docpilot

# Install the package with the providers + GitHub extras.
COPY pyproject.toml README.md requirements.txt ./
COPY docpilot ./docpilot
# ChromaDB is intentionally omitted: a CI run diffs a single PR and uses the
# in-memory embedding store, so the heavy vector-DB dependency would only slow
# the image build. LLM providers + PyGithub are all the Action needs.
RUN pip install --upgrade pip \
    && pip install ".[openai,anthropic,github]"

# GitHub mounts the repo at GITHUB_WORKSPACE and runs from there.
ENTRYPOINT ["python", "-m", "docpilot.action.entrypoint"]
