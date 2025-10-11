"""This package defines business logic and application data."""

from .log import configure_mapper_logger
from .log import configure_root_logger

configure_root_logger()
configure_mapper_logger()
