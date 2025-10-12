"""This module implements main logic of the bot and message handling."""

from typing import cast

from vkinder import view
from vkinder.config import VkConfig
from vkinder.log import get_logger
from vkinder.model import Database
from vkinder.model import DatabaseSession
from vkinder.shared_types import InputMessage
from vkinder.shared_types import User
from vkinder.view.strings import MainMenu
from vkinder.view.strings import SearchMenu

from .states.state_manager import StateManager
from .vk_service import Event
from .vk_service import VkService
from .vk_service import VkServiceError


class Controller:
    """Handles user messages and responds to user."""

    def __init__(self, db: Database, vk_config: VkConfig) -> None:
        """Initialize a controller object.

        Args:
            db (Database): Database object.
            vk_config (VkConfig): VK API config.
        """
        self._logger = get_logger(self)
        self._db = db
        self._vk = VkService(vk_config)
        self._state_manager = StateManager(self._vk)

    def start_message_loop(self) -> None:
        """Process all incoming messages and keep running until stopped."""
        for message in self._vk.listen_messages():
            self.handle_message(message)

    def handle_message(self, event: Event):
        """Обработка входящего сообщения"""
        user_id = cast(int, event.user_id)
        text = event.text.lower().strip()
        vk = self._vk

        self._logger.info('Сообщение от user_id=%d: "%s"', user_id, text)

        with self._db.create_session() as session:
            message = self._event_to_message(session, event)

        user = message.user

        # Обработка команд
        try:
            if text in ["начать", "привет", "start"]:
                vk.send_start_keyboard(user_id)

            elif text == view.MainMenu.SEARCH:
                vk.send_message(user_id, self.format_search_profile(user_id))
                vk.keyboard_dating(user_id)

            elif text == SearchMenu.NEXT:
                vk.send_message(user_id, self.format_search_profile(user_id))

            elif text == SearchMenu.GO_BACK:
                vk.send_start_keyboard(user_id)

            elif text == MainMenu.PROFILE:
                view.format_your_profile(user)
                vk.send_message(user_id, self.format_user_profile(user_id))
                vk.send_start_keyboard(user_id)

            elif text == MainMenu.HELP:
                help_text = """
                Доступные команды:
                🔍 Поиск - поиск анкет
                👤 Профиль - твоя анкета
                ❓ Помощь - это сообщение
                """
                vk.send_message(user_id, help_text.strip())
                vk.send_start_keyboard(user_id)

            else:
                vk.send_message(user_id, view.Strings.UNKNOWN_COMMAND)
        except VkServiceError:
            self._logger.error(
                'Error when handling message user_id:%d',
                user_id,
            )


    def format_user_profile(self, user_id: int):
        user = self._vk.get_user_profile(user_id)
        return view.format_your_profile(user)

    def format_search_profile(self, user_id: int):
        user = self._vk.search_user_by_parameters(user_id)
        return view.format_search_profile(user)

    def _event_to_message(
        self,
        session: DatabaseSession,
        event: Event,
    ) -> InputMessage:
        """Internal helper that extracts all required data from VK event.

        Args:
            session (DatabaseSession): Session object.
            event (Event): Event from VK service.

        Returns:
            InputMessage: Message object.
        """
        user_id = cast(int, event.user_id)
        user = self._vk.get_user_profile(user_id)
        if user is None:
            user = User(user_id)
        user = session.add_or_update_user(user)
        return InputMessage(user, event.text)
