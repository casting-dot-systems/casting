"""Notion integration for casting systems."""

__version__ = "0.1.0"
__all__ = ["Plugin"]


class Plugin:
    """Notion plugin for integration with Notion workspace."""

    def __init__(self):
        self.name = "notion"
        self.version = __version__