# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ARG UV_INDEX_URL
ARG UV_EXTRA_INDEX_URL
ENV UV_INDEX_URL=${UV_INDEX_URL}
ENV UV_EXTRA_INDEX_URL=${UV_EXTRA_INDEX_URL}

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=/app/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/app/uv.lock \
    uv sync --locked --no-install-project

ADD . /app

RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["uv", "run", "casting-org"]
CMD ["--help"]
