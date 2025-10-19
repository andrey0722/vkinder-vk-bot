"""This package transforms abstract bot responses to actual strings."""

from .menu import normalize_menu_command
from .message import render_messages
from .message import render_response

__all__ = (
    'normalize_menu_command',
    'render_messages',
    'render_response',
)
