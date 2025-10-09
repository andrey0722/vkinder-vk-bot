"""Implements classes for VK API interaction."""

from collections.abc import Iterator
import json
import random
from typing import Any

import vk_api
from vk_api.longpoll import Event
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll

from vkinder.log import get_logger

type VkObject = dict[str, Any]


class VkError(Exception):
    """Error when using VK API."""


class Vk:
    """Implements VK API interactions."""

    def __init__(self, community_token: str, user_token: str) -> None:
        """Initialize vk object.

        Args:
            community_token (str): VK community access token.
            user_token (str): VK community access token.

        Raises:
            VkError: Error while creating vk object.
        """
        self._logger = get_logger(self)
        self._vk = self._create_vk(community_token)
        self._vk_user = self._create_vk(user_token)
        self._longpoll = self._create_longpoll()
        self._logger.info("Бот успешно инициализирован")

    def listen(self) -> Iterator[Event]:
        return self._log_events(self._listen())

    def listen_messages(self) -> Iterator[Event]:
        return self._log_events(filter(self._is_message_event, self._listen()))

    def send_message(self, user_id: int, message: str) -> None:
        self._logger.info('Sending to user %s: %s', user_id, message)
        try:
            self._vk.method(
                'messages.send',
                {
                    'user_id': user_id,
                    'message': message,
                    'random_id': self._get_random_id(),
                },
            )
        except vk_api.VkApiError as e:
            raise VkError(e) from e

    def send_start_keyboard(self, user_id):
        self._logger.debug(f"Отправка клавиатуры пользователю {user_id}")
        try:
            keyboard = {
                "one_time": False,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": "🔍 Поиск",
                            },
                            "color": "primary",
                        },
                        {
                            "action": {
                                "type": "text",
                                "label": "👤 Профиль",
                            },
                            "color": "secondary",
                        },
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": "❓ Помощь",
                            },
                            "color": "secondary",
                        },
                    ],
                ],
            }

            self._vk.method(
                "messages.send",
                {
                    "user_id": user_id,
                    "message": "Выбери действие:",
                    "keyboard": json.dumps(keyboard),
                    "random_id": random.randrange(10**7),
                },
            )

            self._logger.info(f"Клавиатура отправлена пользователю user_id {user_id}")
        except vk_api.exceptions.ApiError as e:
            self._logger.error(
                f"Ошибка VK API при отправке клавиатуры пользователю user_id={user_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            self._logger.error(
                f"Неожиданная ошибка в send_start_keyboard: {e}", exc_info=True
            )
    def keyboard_dating(self, user_id):
        self._logger.info('Отправка клавиатуры знакомст пользователю')
        try:
            keyboard = {
                "one_time": False,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": "⏭️ Следующая анкета",
                            },
                            "color": "primary",
                        },
                        {
                            "action": {
                                "type": "text",
                                "label": "💘 Добавить в избранное",
                            },
                            "color": "secondary",
                        },
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": "◀️ Вернуться в главное меню",
                            },
                            "color": "secondary",
                        },
                    ],
                ],
            }

            self._vk.method(
                "messages.send",
                {
                    "user_id": user_id,
                    "message": "Выбери действие:",
                    "keyboard": json.dumps(keyboard),
                    "random_id": random.randrange(10**7),
                },
            )

            self._logger.info(f"Клавиатура отправлена пользователю user_id {user_id}")
        except vk_api.exceptions.ApiError as e:
            self._logger.error(
                f"Ошибка VK API при отправке клавиатуры пользователю user_id={user_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            self._logger.error(
                f"Неожиданная ошибка в send_start_keyboard: {e}", exc_info=True
            )

    def search_user_by_parameters(self, user_id: int) -> VkObject | None:
        current_user = self.get_user_data(user_id)

        if not current_user:
            self._logger.warning('Не удалось найти пользователя с id=%d', user_id)
            return None

        random_offset = random.randint(0, 999)

        user_sex = current_user.get('sex', 0)
        if user_sex == 0:
            self._logger.debug('Не удалось определить пол, поиск отменяется')
            return None

        sex = 1 if user_sex == 2 else 2
        result = self._vk_user.method(
            "users.search",
            {
                "count": 1,
                'offset' : random_offset,
                "has_photo": 1,
                "online": 1,
                "sex": sex,
                'fields' : 'sex, city, bdate',

            },
        )

        if users := result.get('items', []):
            return users[0]
        self._logger.warning('Не найдено пользователей по критериям поиска')
        return None

    def get_user_data(self, user_id: int) -> VkObject | None:
        try:
            users: list[VkObject] = self._vk.method(
                "users.get",
                {
                    "user_ids": user_id,
                    "fields": "first_name, last_name, sex, bdate ,city",
                },
            )
            if not users:
                self._logger.debug(
                    'Данные пользователя с id=%d извлечь не удалось', user_id
                )
                return None

            self._logger.info(
                'Данные для пользователя с id=%d получены', user_id
            )
            return users[0]
        except vk_api.exceptions.VkApiError:
            self._logger.exception(
                'Ошибка VK API при извлечения данных пользователя с id=%d',
                user_id,
            )
            return None

    def _create_vk(self, token: str) -> vk_api.VkApi:
        """Internal helper to create VK API object.

        Args:
            token (str): VK API access token.

        Raises:
            VkError: Error while creating VK API object.

        Returns:
            VkApi: VK API object.
        """
        try:
            return vk_api.VkApi(token=token)
        except vk_api.exceptions.VkApiError as e:
            raise VkError(e) from e

    def _create_longpoll(self) -> VkLongPoll:
        """Internal helper to create VK longpoll object.

        Raises:
            VkError: Error while creating VK longpoll object.

        Returns:
            VkApi: VK longpoll object.
        """
        try:
            return VkLongPoll(self._vk)
        except vk_api.exceptions.VkApiError as e:
            raise VkError(e) from e

    def _listen(self) -> Iterator[Event]:
        try:
            yield from self._longpoll.listen()
        except vk_api.exceptions.VkApiError as e:
            raise VkError(e) from e

    def _log_events(self, events: Iterator[Event]) -> Iterator[Event]:
        return map(self._log_event, events)

    def _log_event(self, event: Event) -> Event:
        self._logger.info('Got from user %s: %s', event.user_id, event.text)
        return event

    @staticmethod
    def _is_message_event(event: Event) -> bool:
        """Internal helper that filters only VK events on receiving message.

        Args:
            event (Event): VK event object.

        Returns:
            bool: `True` if event is a receive message event,
                otherwise `False`.
        """
        return event.type == VkEventType.MESSAGE_NEW and event.to_me

    @staticmethod
    def _get_random_id() -> int:
        """Internal helper that generates random id for message.

        Returns:
            int: Random id number.
        """
        return random.randrange(10**7)
