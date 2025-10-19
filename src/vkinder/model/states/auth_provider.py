"""This module provides means to proceed with user authorization."""


import abc
import dataclasses
import datetime
from typing import Protocol


@dataclasses.dataclass
class AuthRecord:
    """Holds data from user authorization."""

    user_id: int
    access_token: str
    refresh_token: str
    expire_time: datetime.datetime
    access_rights: str


class AuthProvider(Protocol):
    """Provides means to proceed with user authorization."""

    @abc.abstractmethod
    def create_auth_link(
        self,
        user_id: int,
        access_rights: str,
    ) -> str:
        """Constructs link for user to proceed with authorization.

        Args:
            user_id (int): User id.
            access_rights (str): User access right set to request from user.

        Returns:
            str: Authorization link.
        """
