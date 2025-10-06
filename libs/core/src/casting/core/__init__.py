"""Core domain: Cast models, pipelines, and plugin interfaces."""

__version__ = "0.1.0"
__all__ = ["Plugin"]


class Plugin:
    """Core plugin interface for the casting system."""

    def __init__(self):
        self.name = "core"
        self.version = __version__
