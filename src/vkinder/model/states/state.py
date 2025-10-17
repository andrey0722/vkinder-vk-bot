"""This module defines base class of the bot states."""

import abc
from collections.abc import Iterator
from typing import TYPE_CHECKING

from vkinder.controller.vk_service import VkServiceError
from vkinder.log import get_logger
from vkinder.model.db import DatabaseSession
from vkinder.shared_types import MENU_OPTIONS
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory

if TYPE_CHECKING:
    from vkinder.controller import VkService

    from .state_manager import StateManager


class State(abc.ABC):
    """Base class of the bot state.

    Performs all actions that are required when bot enters
    into the state and handles user replies.
    """

    def __init__(self, manager: 'StateManager') -> None:
        """Initialize a controller state object.

        Args:
            manager (StateManager): State manager object.
        """
        super().__init__()
        self._manager = manager
        self._logger = get_logger(self)

    @property
    def vk(self) -> 'VkService':
        """Returns VK service object for the state.

        Returns:
            VkService: VK service object.
        """
        return self._manager.vk

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

    def is_command_accepted(self, message: InputMessage) -> bool:
        """Tests whether user input command is accepted in current state.

        Args:
            message (InputMessage): A message from user.

        Returns:
            bool: `True` if the command is accepted, otherwise `False`.
        """
        return message.text in MENU_OPTIONS[message.user.state]

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

    def attach_profile_photos(self, profile_id: int) -> Iterator[Response]:
        """Shows profile photos to user.

        Args:
            profile_id (int): User profile id.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        try:
            photos = self.vk.get_user_photos(
                user_id=profile_id,
                sort_by_likes=True,
                limit=3,
            )
        except VkServiceError:
            self._logger.warning('Failed to fetch profile photos')
            yield ResponseFactory.photo_failed()
        else:
            yield ResponseFactory.attach_media(photos)
