"""This module defines base class of the bot states."""

import abc
from collections.abc import Iterator
import copy
from typing import TYPE_CHECKING, ClassVar

from vkinder.log import get_logger
from vkinder.model.db import DatabaseSession
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Keyboard
from vkinder.shared_types import MenuToken
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory
from vkinder.shared_types import UserAuthData

from .auth_provider import AuthProvider
from .auth_provider import AuthProviderRefreshError
from .auth_provider import AuthRecord
from .profile_provider import ProfileProvider
from .profile_provider import ProfileProviderError

if TYPE_CHECKING:
    from .state_manager import StateManager


class State(abc.ABC):
    """Base class of the bot state.

    Performs all actions that are required when bot enters
    into the state and handles user replies.
    """

    KEYBOARD: ClassVar[Keyboard]
    """Bot keyboard for this user state."""

    MENU_OPTIONS: ClassVar[tuple[MenuToken, ...]] = ()
    """Menu commands accepted for this user state."""

    def __init__(self, manager: 'StateManager') -> None:
        """Initialize a controller state object.

        Args:
            manager (StateManager): State manager object.
        """
        super().__init__()
        self._manager = manager
        self._logger = get_logger(self)

    @property
    def profile_provider(self) -> ProfileProvider:
        """Returns profile provider object for the state.

        Returns:
            ProfileProvider: Profile provider object.
        """
        return self._manager.profile_provider

    @property
    def auth_provider(self) -> AuthProvider:
        """Returns authorization provider object for the state.

        Returns:
            AuthProvider: Authorization provider object.
        """
        return self._manager.auth_provider

    @abc.abstractmethod
    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Start performing actions related to this bot state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """

    @abc.abstractmethod
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Reply to user input according to current bot state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """

    @classmethod
    def is_command_accepted(cls, message: InputMessage) -> bool:
        """Tests whether user input command is accepted in current state.

        Args:
            message (InputMessage): A message from user.

        Returns:
            bool: `True` if the command is accepted, otherwise `False`.
        """
        text = message.text
        return isinstance(text, MenuToken) and text in cls.MENU_OPTIONS

    def unknown_command(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Restarts this state when got unaccepted command.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        self._logger.warning(
            'Unknown menu option for state %s: %r',
            message.user.state,
            message.text,
        )
        yield ResponseFactory.unknown_command(allow_squash=False)
        yield from self.start(session, message)

    def show_keyboard(self, message: InputMessage) -> Response:
        """Shows keyboard for this state to user.

        Args:
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        keyboard = self.create_keyboard(message)
        self._logger.debug('Sending keyboard: %r', keyboard)
        return ResponseFactory.keyboard(keyboard)

    def create_keyboard(self, message: InputMessage) -> Keyboard:
        """Creates bot keyboard for this user state.

        Args:
            message (InputMessage): A message from user.

        Returns:
            Keyboard: Bit keyboard object.
        """
        user_id = message.user.id
        # Duplicate keyboard to prevent messing it up
        keyboard = copy.deepcopy(self.KEYBOARD)
        self._logger.debug('Keyboard for user %d: %r', user_id, keyboard)
        return keyboard

    def attach_profile_photos(
        self,
        profile_id: int,
        access_token: str | None = None,
    ) -> Iterator[Response]:
        """Shows profile photos to user.

        Args:
            profile_id (int): User profile id.
            access_token (str | None, optional): User access token for
                API call. Defaults to None.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        try:
            photos = self.profile_provider.get_user_photos(
                user_id=profile_id,
                sort_by_likes=True,
                limit=3,
                access_token=access_token,
            )
        except ProfileProviderError:
            self._logger.warning('Failed to fetch profile photos')
            yield ResponseFactory.photo_failed()
        else:
            yield ResponseFactory.attach_media(photos)

    def get_user_token(
        self,
        session: DatabaseSession,
        user_id: int,
    ) -> str | None:
        """Extracts user access token and refreshes it if needed.

        Args:
            session (DatabaseSession): Session object.
            user_id (int): User profile id.

        Returns:
            str | None: User access token if valid, otherwise `None`.
        """
        # Check user authorization
        with session.begin():
            auth_data = session.get_auth_data(user_id)
            if auth_data is None:
                # No auth data at all
                return None
            token = auth_data.access_token

        # Make sure the token is valid
        if self.profile_provider.validate_access_token(token):
            return token

        # Try to refresh token
        record = AuthRecord(**auth_data.asdict())
        try:
            record = self.auth_provider.refresh_auth(record)
        except AuthProviderRefreshError:
            return None

        # Save new auth data
        auth_data = UserAuthData(**record.asdict())
        with session.begin():
            auth_data = session.save_auth_data(auth_data)
            return auth_data.access_token
