"""Discord framework: Low-level Discord integration."""

__version__ = "0.1.0"
__all__ = ["Plugin"]


class Plugin:
    """Discord framework plugin for low-level Discord integration."""

    def __init__(self):
        self.name = "discord_framework"
        self.version = __version__