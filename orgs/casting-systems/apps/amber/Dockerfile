FROM python:3.13.1-slim-bookworm

ENV PYTHONUNBUFFERED=True
WORKDIR /workspace

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

COPY . /workspace
RUN uv sync --no-sources --source org-rules --package=amber-bot

CMD ["uv", "run", "--package", "amber-bot", "dev"]
