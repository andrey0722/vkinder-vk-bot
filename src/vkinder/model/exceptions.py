"""This module defines all model exceptions."""


from typing import TYPE_CHECKING

from ..exceptions import VkinderError

if TYPE_CHECKING:
    from .types import User


class ModelError(VkinderError):
    """Base type for all model exceptions."""


class UserNotFoundError(ModelError):
    """A specified user is not currently present in the DB."""

    def __init__(self, user: 'User') -> None:
        """Initialize an exception object.

        Args:
            user (User): User object.
        """
        super().__init__(f'User {user!r} does not exist')


class DatabaseError(ModelError):
    """Error while interacting with database."""
