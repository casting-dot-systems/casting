"""Discord processing: Message processing, streaming, logging, retries."""

__version__ = "0.1.0"
__all__ = ["Plugin"]


class Plugin:
    """Discord processing plugin for message handling and processing."""

    def __init__(self):
        self.name = "discord_processing"
        self.version = __version__