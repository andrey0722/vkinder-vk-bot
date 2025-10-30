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

    def show_keyboard(self) -> Response:
        """Shows keyboard for this state to user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        # Duplicate keyboard to prevent messing it up
        keyboard = copy.deepcopy(self.KEYBOARD)
        self._logger.debug('Sending keyboard: %r', keyboard)
        return ResponseFactory.keyboard(keyboard)

    def attach_profile_photos(self, profile_id: int) -> Iterator[Response]:
        """Shows profile photos to user.

        Args:
            profile_id (int): User profile id.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        try:
            photos = self.profile_provider.get_user_photos(
                user_id=profile_id,
                sort_by_likes=True,
                limit=3,
            )
        except ProfileProviderError:
            self._logger.warning('Failed to fetch profile photos')
            yield ResponseFactory.photo_failed()
        else:
            yield ResponseFactory.attach_media(photos)
