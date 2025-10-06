"""Obsidian integration for casting systems."""

__version__ = "0.1.0"
__all__ = ["Plugin"]


class Plugin:
    """Obsidian plugin for integration with Obsidian vault."""

    def __init__(self):
        self.name = "obsidian"
        self.version = __version__
