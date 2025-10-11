"""This package implements main logic of the bot and message handling."""

from typing import cast

from ..config import VkConfig
from ..log import get_logger
from ..messages import Messages
from ..model.db import Database
from ..model.db import DatabaseSession
from ..model.types import InputMessage
from ..model.types import User
from .state_manager import StateManager
from .vk_service import Event
from .vk_service import VkService


class Controller:
    """Handles user messages and responds to user."""

    def __init__(self, db: Database, vk_config: VkConfig) -> None:
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

        self._logger.info(f'Сообщение от user_id={user_id}: "{text}"')

        with self._db.create_session() as session:
            self._event_to_message(session, event)

        # Обработка команд
        try:
            if text in ["начать", "привет", "start"]:
                vk.send_start_keyboard(user_id)

            elif text == "🔍 поиск":
                vk.send_message(user_id, self.format_user_profile(user_id, False))
                vk.keyboard_dating(user_id)

            elif text == "⏭️ следующая анкета":
                vk.send_message(user_id, self.format_user_profile(user_id, False))

            elif text == "◀️ вернуться в главное меню":
                vk.send_start_keyboard(user_id)

            elif text == "👤 профиль":
                vk.send_message(user_id, self.format_user_profile(user_id, True))

            elif text == "❓ помощь":
                help_text = """
                Доступные команды:
                🔍 Поиск - поиск анкет
                👤 Профиль - твоя анкета
                ❓ Помощь - это сообщение
                """
                vk.send_message(user_id, help_text.strip())
                vk.send_start_keyboard(user_id)

            else:
                vk.send_message(user_id, "Не понял команду. Нажми '❓ Помощь'")
        except Exception:
            self._logger.exception(
                'Непредвиденная ошибка при обработке команд user_id:%d:',
                user_id,
            )


    def format_user_profile(self, user_id, your_profile=False):
        vk = self._vk
        if not your_profile:
            user = vk.search_user_by_parameters(user_id)
        else:
            user = vk.get_user_data(user_id)

        if not user:
            if your_profile:
                return Messages.PROFILE_FAILED
            else:
                return Messages.SEARCH_FAILED

        sex_map = {1: 'Женский', 2: 'Мужской'}
        sex = sex_map.get(user.get('sex', 0), 'Не указан')
        city_name = user.get('city', {}).get('title', 'Не указан')

        start_message = 'Анекта пользвателя: ' if not your_profile else 'Твоя анкета: '
        message = f"""
                    {start_message}
                        Имя : {user['first_name']}
                        Фамилия: {user['last_name']}
                        Пол: {sex},
                        Дата рождения: {user.get('bdate', 'не указана')}
                        Город: {city_name}
            """
        return message

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
        user = User(user_id)
        user = session.add_or_update_user(user)
        return InputMessage(user, event.text)
