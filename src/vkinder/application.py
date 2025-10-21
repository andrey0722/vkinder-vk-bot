"""Defines initialization logic for application.

This module defines the main class of the entire application and
all connections between program components.
"""

from types import TracebackType
from typing import Self

from vkinder.config import AuthConfig
from vkinder.config import DatabaseConfig
from vkinder.config import VkConfig
from vkinder.controller import Controller
from vkinder.log import get_logger
from vkinder.model import Database


class Application:
    """Main class of the bot application."""

    def __init__(self) -> None:
        """Initialize application object."""
        self._logger = get_logger(self)
        self._db = Database(self._read_db_config())
        self._controller = Controller(
            db=self._db,
            vk_config=self._read_vk_config(),
            auth_config=self._read_auth_config(),
        )

    def __enter__(self) -> Self:
        """Enter the context block."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop all components on context exit."""
        self.close()

    def close(self) -> None:
        """Stop all components."""
        self._controller.close()
        self._db.close()

    def run(self) -> None:
        """Start the bot and keep running until stopped."""
        self._logger.info('Starting the bot')
        try:
            self._controller.start_message_loop()
        except Exception as e:
            self._logger.critical('Bot running error: %s', e)
            raise

    def _read_vk_config(self) -> VkConfig:
        """Internal helper to read VK config.

        Returns:
            VkConfig: VK config.
        """
        return VkConfig()

    def _read_auth_config(self) -> AuthConfig:
        """Internal helper to read VK ID auth config.

        Returns:
            AuthConfig: VK ID auth config.
        """
        return AuthConfig()

    def _read_db_config(self) -> DatabaseConfig:
        """Internal helper to read database config.

        Returns:
            DatabaseConfig: Database config.
        """
        return DatabaseConfig()
