# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY apps ./apps
COPY libs ./libs
COPY llmgine ./llmgine
COPY orgs ./orgs

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --project orgs/casting-systems/apps/discord-bot

ENV PATH="/workspace/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["uv", "run", "--project", "orgs/casting-systems/apps/discord-bot", "casting-org-discord-bot"]
