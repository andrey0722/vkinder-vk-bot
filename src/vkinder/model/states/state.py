"""This module defines base class of the bot states."""

import abc
from collections.abc import Iterator
from typing import TYPE_CHECKING

from vkinder.log import get_logger
from vkinder.model.db import DatabaseSession
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Response

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
