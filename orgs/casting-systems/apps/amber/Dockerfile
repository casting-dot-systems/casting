FROM python:3.13-slim

WORKDIR /workspace

COPY . /workspace

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv sync --no-sources --package=amber-bot

CMD ["uv", "run", "--no-sources", "--package", "amber-bot", "prod"]