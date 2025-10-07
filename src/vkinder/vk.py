"""Implements classes for VK API interaction."""

from collections.abc import Iterator
import random

import vk_api
from vk_api.longpoll import Event
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll

from vkinder.log import get_logger


class VkError(Exception):
    """Error when using VK API."""


class Vk:
    """Implements VK API interactions."""

    def __init__(self, token: str) -> None:
        """Initialize vk object.

        Args:
            token (str): VK API access token.

        Raises:
            VkError: Error while creating vk object.
        """
        self._logger = get_logger(self)
        self._token = token
        self._vk = self._create_vk()
        self._longpoll = self._create_longpoll()

    def listen(self) -> Iterator[Event]:
        return self._log_events(self._listen())

    def listen_messages(self) -> Iterator[Event]:
        return self._log_events(filter(self._is_message_event, self._listen()))

    def send(self, message: str, user_id: int) -> None:
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

    def _create_vk(self) -> vk_api.VkApi:
        """Internal helper to create VK API object.

        Raises:
            VkError: Error while creating VK API object.

        Returns:
            VkApi: VK API object.
        """
        try:
            return vk_api.VkApi(token=self._token)
        except vk_api.VkApiError as e:
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
        except vk_api.VkApiError as e:
            raise VkError(e) from e

    def _listen(self) -> Iterator[Event]:
        try:
            yield from self._longpoll.listen()
        except vk_api.VkApiError as e:
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
