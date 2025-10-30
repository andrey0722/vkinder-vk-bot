"""This module provides means to get profile info."""

import abc
from collections.abc import Iterator
from typing import Protocol

from vkinder.exceptions import VkinderError
from vkinder.shared_types import Photo
from vkinder.shared_types import User
from vkinder.shared_types import UserSearchQuery


class ProfileProviderError(VkinderError):
    """Base class for all profile provider errors."""


class ProfileProviderTokenError(VkinderError):
    """Error occurred because access token is invalid."""


class ProfileProvider(Protocol):
    """Provides means to get profile info."""

    @abc.abstractmethod
    def get_user_profile(self, user_id: int) -> User:
        """Extract user profile by their profile id.

        Args:
            user_id (int): User profile id.

        Raises:
            ProfileProviderTokenError: Access token is invalid.
            ProfileProviderError: Failed to get user profile.

        Returns:
            User: User object.
        """

    @abc.abstractmethod
    def get_user_photos(
        self,
        user_id: int,
        *,
        sort_by_likes: bool = False,
        limit: int | None = None,
    ) -> list[Photo]:
        """Extracts user profile photos with optional sorting.

        Args:
            user_id (int): User profile id.
            sort_by_likes (bool, optional): Sort photos by like count in
                descending order. Defaults to `False`.
            limit (int | None, optional): Limit result up to `limit`
                photos if specified. Defaults to `None`.

        Raises:
            ProfileProviderTokenError: Access token is invalid.
            ProfileProviderError: Error when getting profile photos.

        Returns:
            list[Photo]: User profile protos.
        """

    @abc.abstractmethod
    def search_users(self, query: UserSearchQuery) -> Iterator[int]:
        """Perform user search using specified search query.

        Args:
            query (UserSearchQuery): Search query object.

        Raises:
            ProfileProviderTokenError: Access token is invalid.
            ProfileProviderError: Error when searching users.

        Returns:
            Iterator[int]: User profile ids found if any.
        """
