"""This module defines logging configuration for SLQAlchemy."""

import logging

import sqlalchemy.log

from vkinder.log import LogLevelLimitFilter
from vkinder.log import get_logger


def set_sqlalchemy_debug_filter(obj: sqlalchemy.log.Identified) -> None:
    """Reduce SQLAlchemy's logger log level to DEBUG.

    Args:
        obj (sqlalchemy.log.Identified): SQLAlchemy object.
    """
    logger = obj.logger
    if isinstance(logger, sqlalchemy.log.InstanceLogger):
        # Handle SQLAlchemy's internal wrappers for loggers
        logger = logger.logger
    # Avoid flooding with 'INFO' log level
    logger.addFilter(LogLevelLimitFilter(logger, logging.DEBUG))


def configure_root_logger():
    """Override configuration of the `sqlalchemy` library root logger."""
    sqlalchemy.log.rootlogger.setLevel(logging.NOTSET)


def configure_orm_logger():
    """Override configuration of the `sqlalchemy` library mapper logger."""
    logger = get_logger('sqlalchemy.orm')
    logger.setLevel(logging.WARNING)
