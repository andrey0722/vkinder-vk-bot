"""This module provides means to proceed with user authorization."""


import abc
import dataclasses
import datetime
from typing import Any, Protocol


class AuthProviderError(Exception):
    """Base class for all authorization provider errors."""


class AuthProviderRefreshError(AuthProviderError):
    """Failed to refresh user access token."""


@dataclasses.dataclass
class AuthRecord:
    """Holds data from user authorization."""

    user_id: int
    access_token: str
    refresh_token: str
    device_id: str
    expire_time: datetime.datetime
    access_rights: str

    def asdict(self) -> dict[str, Any]:
        """Transform object to a dict.

        Returns:
            dict[str, Any]: Resulting dict.
        """
        return dataclasses.asdict(self)


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

    @abc.abstractmethod
    def refresh_auth(self, record: AuthRecord) -> AuthRecord:
        """Get new user access token using refresh token.

        Args:
            record (AuthRecord): Auth record object.

        Raises:
            AuthProviderRefreshError: Failed to refresh token.

        Returns:
            AuthRecord: New auth record object.
        """
