from collections.abc import Iterator
import random

import vk_api
from vk_api.longpoll import Event
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll

from vkinder.log import get_logger


class Vk:
    def __init__(self, token: str) -> None:
        self._vk = vk_api.VkApi(token=token)
        self._longpoll = VkLongPoll(self._vk)
        self._logger = get_logger(self)

    def listen(self) -> Iterator[Event]:
        return self._log_events(self._listen())

    def listen_messages(self) -> Iterator[Event]:
        return self._log_events(filter(self._is_message_event, self._listen()))

    def send(self, message: str, user_id: int) -> None:
        self._logger.info('Sending to user %s: %s', user_id, message)
        self._vk.method(
            'messages.send',
            {
                'user_id': user_id,
                'message': message,
                'random_id': self._get_random_id(),
            },
        )

    def _listen(self) -> Iterator[Event]:
        return self._longpoll.listen()

    def _log_events(self, events: Iterator[Event]) -> Iterator[Event]:
        return map(self._log_event, events)

    def _log_event(self, event: Event) -> Event:
        self._logger.info('Got from user %s: %s', event.user_id, event.text)
        return event

    @staticmethod
    def _is_message_event(event: Event) -> bool:
        return event.type == VkEventType.MESSAGE_NEW and event.to_me

    @staticmethod
    def _get_random_id() -> int:
        return random.randrange(10**7)
