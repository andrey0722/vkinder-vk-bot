"""This package defines entire vkinder bot logic."""

from .application import Application
from .exceptions import VkinderError

__all__ = (
    'VkinderError',
    'Application',
)
