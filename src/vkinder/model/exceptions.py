"""This module defines all model exceptions."""


from vkinder.exceptions import VkinderError


class ModelError(VkinderError):
    """Base type for all model exceptions."""


class DatabaseError(ModelError):
    """Error while interacting with database."""
