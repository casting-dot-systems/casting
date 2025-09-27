"""Google Calendar integration for casting systems."""

__version__ = "0.1.0"
__all__ = ["Plugin"]


class Plugin:
    """Google Calendar plugin for integration with Google Calendar."""

    def __init__(self):
        self.name = "gcal"
        self.version = __version__