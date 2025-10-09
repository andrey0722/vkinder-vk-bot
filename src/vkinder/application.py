"""Defines initialization logic for application.

This module defines the main class of the entire application and
all connections between program components.
"""

from typing import cast

from vkinder.config import Config
from vkinder.config import ConfigError
from vkinder.log import get_logger
from vkinder.messages import Messages
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
                self.handle_message(event)
        except VkError as e:
            self._logger.critical('Bot running error')
            raise ApplicationError(e) from e

    def handle_message(self, event):
        """Обработка входящего сообщения"""
        user_id = event.user_id
        text = event.text.lower().strip()
        vk = self._vk

        self._logger.info(f'Сообщение от user_id={user_id}: "{text}"')
        # Обработка команд
        try:
            if text in ["начать", "привет", "start"]:
                self.send_start_keyboard(user_id)

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
        config = self._config
        try:
            return Vk(config.vk_community_token, config.vk_user_token)
        except VkError as e:
            self._logger.critical('Create VK error')
            raise ApplicationError(e) from e
