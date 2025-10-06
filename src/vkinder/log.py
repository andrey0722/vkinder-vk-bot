import json
import logging
import logging.config

CONFIG_PATH = 'logging.json'


def setup_loging() -> None:
    """Initialize logging infrastructure for future logging."""
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    logging.config.dictConfig(config)


def get_logger(obj: object) -> logging.Logger:
    """Returns logger object for a specified program object.

    Args:
        obj (Any): Object to use for name calculation.
    """
    logger_name = _get_logger_name(obj)
    return logging.getLogger(logger_name)


def _get_logger_name(obj: object) -> str:
    """Internal helper to calculate desired logger name.

    Args:
        obj (object): Object to use for name calculation.
    """
    if isinstance(obj, str):
        # User specified a concrete logger name
        return obj
    if not hasattr(obj, '__qualname__'):
        # For plain objects use their types
        # Functions already have names
        obj = type(obj)
    # Use fully-qualified name with module path
    return f'{obj.__module__}.{obj.__qualname__}'
