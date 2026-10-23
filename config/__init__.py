from config.settings import Settings, get_settings, settings
from config.database import get_session as db

setting = settings  # alias for backward compatibility

__all__ = ["Settings", "get_settings", "settings", "setting"]
