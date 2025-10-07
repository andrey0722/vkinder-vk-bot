"""Defines initialization logic for application.

This module defines the main class of the entire application and
all connections between program components.
"""

from typing import cast

from vkinder.config import Config
from vkinder.config import ConfigError
from vkinder.log import get_logger
from vkinder.vk import Vk
from vkinder.vk import VkError


class ApplicationError(Exception):
    """Raised when application is stopped on any error."""


class Application:
    """Main class of the bot application."""

    def __init__(self) -> None:
        """Initialize application object.

        Raises:
            ApplicationError: Error while initializing application.
        """
        self._logger = get_logger(self)
        self._config = self._read_config()
        self._vk = self._create_vk()

    def run(self) -> None:
        """Start the bot and keep running until stopped.

        Raises:
            ApplicationError: Error while running application.
        """
        self._logger.info('Starting the bot')
        try:
            vk = self._vk
            for event in vk.listen_messages():
                vk.send(f'Test: {event.text}', cast(int, event.user_id))
        except VkError as e:
            self._logger.critical('Bot running error')
            raise ApplicationError(e) from e

    def _read_config(self) -> Config:
        """Internal helper to read application config.

        Raises:
            ApplicationError: Error while reading config.

        Returns:
            Config: Application config.
        """
        try:
            return Config()
        except ConfigError as e:
            self._logger.critical('Config error')
            raise ApplicationError(e) from e

    def _create_vk(self) -> Vk:
        """Internal helper to create vk object.

        Raises:
            ApplicationError: Error while creating vk object.

        Returns:
            Vk: Vk object.
        """
        try:
            return Vk(self._config.vk_token)
        except VkError as e:
            self._logger.critical('Create VK error')
            raise ApplicationError(e) from e
