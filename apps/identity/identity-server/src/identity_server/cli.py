#!/usr/bin/env python
"""CLI entry point for identity server."""

import uvicorn
from identity_server.core.config import settings


def main():
    """Run the identity server with uvicorn."""
    uvicorn.run(
        "identity_server.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=True,
    )


if __name__ == "__main__":
    main()
