"""This module defines base class of the bot state."""

import abc
from typing import TYPE_CHECKING

from ..log import get_logger
from ..model.db import DatabaseSession
from ..model.types import InputMessage
from ..view import OutputMessage
from .vk_service import VkService

if TYPE_CHECKING:
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
    def vk(self) -> VkService:
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
    ) -> OutputMessage:
        """Start performing actions related to this bot state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            OutputMessage: Bot response to the user.
        """
