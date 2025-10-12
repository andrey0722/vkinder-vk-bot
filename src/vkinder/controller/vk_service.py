"""Implements classes for VK API interaction."""

from collections.abc import Iterator
import enum
import json
import random
from typing import Any, Final

import vk_api
import vk_api.keyboard
from vk_api.longpoll import Event
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll

from vkinder.config import VkConfig
from vkinder.exceptions import VkinderError
from vkinder.log import get_logger
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import Keyboard
from vkinder.shared_types import OutputMessage
from vkinder.shared_types import Sex
from vkinder.shared_types import TextAction
from vkinder.shared_types import User
from vkinder.view.strings import MainMenu
from vkinder.view.strings import SearchMenu
from vkinder.view.strings import Strings

type VkObject = dict[str, Any]


class VkServiceError(VkinderError):
    """Error when using VK API."""


class MissingUserIdError(VkServiceError):
    """No user id is specified."""


class VkService:
    """Implements VK API interactions."""

    def __init__(self, config: VkConfig) -> None:
        """Initialize VK service object.

        Args:
            config (VkConfig): VK service config.

        Raises:
            VkServiceError: Error while creating VK service object.
        """
        self._logger = get_logger(self)
        self._vk = self._create_vk(config.vk_community_token)
        self._vk_user = self._create_vk(config.vk_user_token)
        self._longpoll = self._create_longpoll()
        self._logger.info('VK service is initialized')

    def listen(self) -> Iterator[Event]:
        """Retrieves events from VK longpoll server.

        Yields:
            Event: VK longpoll event.
        """
        return self._log_events(self._listen())

    def listen_messages(self) -> Iterator[Event]:
        """Retrieves message events from VK longpoll server.

        Yields:
            Event: VK longpoll message event.
        """
        return self._log_events(filter(self._is_message_event, self._listen()))

    def send(self, user_id: int, message: OutputMessage) -> None:
        text = message.text
        keyboard = message.keyboard
        self._logger.info('Sending to user %s: %s', user_id, text)
        self._logger.info('Keyboard to user %s: %r', user_id, keyboard)
        try:
            self._vk.method(
                'messages.send',
                {
                    'user_id': user_id,
                    'message': text,
                    'keyboard': _convert_keyboard(keyboard),
                    'random_id': _get_random_id(),
                },
            )
        except vk_api.VkApiError as e:
            raise VkServiceError(e) from e

    def send_message(
        self,
        user_id: int,
        message: str,
        *,
        keyboard: VkObject | None = None,
    ) -> None:
        self._logger.info('Sending to user %s: %s', user_id, message)

        params = {
            'user_id': user_id,
            'message': message,
            'random_id': _get_random_id(),
        }
        if keyboard is not None:
            params['keyboard'] = json.dumps(keyboard)

        try:
            self._vk.method('messages.send', params)
        except vk_api.VkApiError as e:
            raise VkServiceError(e) from e

    def send_start_keyboard(self, user_id: int) -> None:
        self._logger.debug("Отправка клавиатуры пользователю %d", user_id)
        keyboard = {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": MainMenu.SEARCH,
                        },
                        "color": "primary",
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": MainMenu.PROFILE,
                        },
                        "color": "secondary",
                    },
                ],
                [
                    {
                        "action": {
                            "type": "text",
                            "label": MainMenu.HELP,
                        },
                        "color": "secondary",
                    },
                ],
            ],
        }

        self.send_message(user_id, Strings.SELECT_ACTION, keyboard=keyboard)
        self._logger.info(
            'Клавиатура отправлена пользователю user_id=%d',
            user_id,
        )

    def keyboard_dating(self, user_id):
        self._logger.debug(
            'Отправка клавиатуры знакомств пользователю %d',
            user_id,
        )
        keyboard = {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": SearchMenu.NEXT,
                        },
                        "color": "primary",
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": SearchMenu.ADD_FAVORITE,
                        },
                        "color": "secondary",
                    },
                ],
                [
                    {
                        "action": {
                            "type": "text",
                            "label": SearchMenu.GO_BACK,
                        },
                        "color": "secondary",
                    },
                ],
            ],
        }

        self.send_message(user_id, Strings.SELECT_ACTION, keyboard=keyboard)
        self._logger.info(
            'Клавиатура отправлена пользователю user_id=%d',
            user_id,
        )

    def search_user_by_parameters(self, user_id: int) -> User | None:
        current_user = self.get_user_profile(user_id)

        if not current_user:
            self._logger.warning('Не удалось найти пользователя с id=%d', user_id)
            return None

        random_offset = random.randint(0, 999)

        user_sex = current_user.sex
        if user_sex == Sex.NOT_KNOWN:
            self._logger.debug('Не удалось определить пол, поиск отменяется')
            return None

        sex = 1 if user_sex == 2 else 2

        try:
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
        except vk_api.exceptions.VkApiError as e:
            self._logger.error('User search error: %s', e)
            raise VkServiceError(e) from e

        if users := result.get('items', []):
            return _convert_user(users[0])
        self._logger.warning('Не найдено пользователей по критериям поиска')
        return None

    def get_user_profile(self, user_id: int) -> User | None:
        self._logger.debug('Extracting user profile for id=%d', user_id)
        try:
            users: list[VkObject] = self._vk.method(
                "users.get",
                {
                    "user_ids": user_id,
                    "fields": "first_name, last_name, sex, bdate, city",
                },
            )
        except vk_api.exceptions.VkApiError as e:
            self._logger.error(
                'Error when extracting user profile for id=%d: %s',
                user_id,
                e,
            )
            return None

        if not users:
            self._logger.debug('No user profile for id=%d', user_id)
            return None

        self._logger.info('Extracted user profile for id=%d', user_id)
        user = _convert_user(users[0])
        self._logger.debug('Extracted user: %r', user)
        return user

    def _create_vk(self, token: str) -> vk_api.VkApi:
        """Internal helper to create VK API object.

        Args:
            token (str): VK API access token.

        Raises:
            VkServiceError: Error while creating VK API object.

        Returns:
            VkApi: VK API object.
        """
        try:
            return vk_api.VkApi(token=token)
        except vk_api.exceptions.VkApiError as e:
            self._logger.critical('Failed to connect to VK API: %s', e)
            raise VkServiceError(e) from e

    def _create_longpoll(self) -> VkLongPoll:
        """Internal helper to create VK longpoll object.

        Raises:
            VkServiceError: Error while creating VK longpoll object.

        Returns:
            VkApi: VK longpoll object.
        """
        try:
            return VkLongPoll(self._vk)
        except vk_api.exceptions.VkApiError as e:
            self._logger.critical('Failed to connect to VK longpoll: %s', e)
            raise VkServiceError(e) from e

    def _listen(self) -> Iterator[Event]:
        try:
            yield from self._longpoll.listen()
        except vk_api.exceptions.VkApiError as e:
            self._logger.critical('VK listen error: %s', e)
            raise VkServiceError(e) from e

    def _log_events(self, events: Iterator[Event]) -> Iterator[Event]:
        return map(self._log_event, events)

    def _log_event(self, event: Event) -> Event:
        self._logger.info(
            'Message from user %d: [%s]',
            event.user_id,
            event.text,
        )
        return event

    @staticmethod
    def _is_message_event(event: Event) -> bool:
        """Internal helper that filters only VK events on receiving message.

        Args:
            event (Event): VK event object.

        Returns:
            bool: `True` if event is a received message event,
                otherwise `False`.
        """
        return event.type == VkEventType.MESSAGE_NEW and event.to_me


def _get_random_id() -> int:
    """Internal helper that generates random id for message.

    Returns:
        int: Random id number.
    """
    return random.randrange(10**7)


@enum.unique
class VkSex(enum.IntEnum):
    """Sex designator in VK notation."""

    NOT_SPECIFIED = 0
    FEMALE = 1
    MALE = 2


_VK_SEX_TO_SEX: dict[VkSex, Sex] = {
    VkSex.NOT_SPECIFIED: Sex.NOT_KNOWN,
    VkSex.FEMALE: Sex.FEMALE,
    VkSex.MALE: Sex.MALE,
}
"""VK sex mapping."""


def _convert_sex(sex: int | None) -> Sex:
    """Convert VK sex notation to standard.

    Args:
        sex (int | None): VK sex.

    Returns:
        Sex: Standard sex.
    """
    try:
        vk_sex = VkSex(sex)
    except ValueError:
        return Sex.NOT_KNOWN
    return _VK_SEX_TO_SEX[vk_sex]


def _convert_user(data: VkObject) -> User:
    """Convert VK user object to `User`.

    Args:
        data (VkObject): VK user object.

    Raises:
        MissingUserIdError: User id is not specified.

    Returns:
        User: _description_
    """
    try:
        user_id = data['id']
    except KeyError as e:
        raise MissingUserIdError from e
    city = data.get('city')
    return User(
        id=user_id,
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        sex=_convert_sex(data.get('sex')),
        birthday=data.get('bday'),
        city_id=city and city.get('id'),
        city=city and city.get('title'),
    )


_VK_BUTTON_COLOR_MAPPING: Final = {
    ButtonColor.PRIMARY: vk_api.keyboard.VkKeyboardColor.PRIMARY,
    ButtonColor.SECONDARY: vk_api.keyboard.VkKeyboardColor.SECONDARY,
    ButtonColor.NEGATIVE: vk_api.keyboard.VkKeyboardColor.NEGATIVE,
    ButtonColor.POSITIVE: vk_api.keyboard.VkKeyboardColor.POSITIVE,
}


def _convert_keyboard(keyboard: Keyboard | None) -> str:
    """Internal helper to convert bot keyboard object to VK API JSON format.

    Args:
        keyboard (Keyboard | None): Bot keyboard if any.

    Returns:
        str: Bot keyboard in JSON format.
    """
    if keyboard is None:
        return vk_api.keyboard.VkKeyboard.get_empty_keyboard()

    vk_kb = vk_api.keyboard.VkKeyboard(
        one_time=keyboard.one_time,
        inline=keyboard.inline,
    )
    # VkKeyboard creates the first empty line, erase it
    vk_kb.lines.clear()

    for row in keyboard.button_rows:
        vk_kb.add_line()
        for button in row:
            try:
                color = _VK_BUTTON_COLOR_MAPPING[button.color]
            except KeyError as e:
                raise NotImplementedError from e
            action = button.action
            if isinstance(action, TextAction):
                vk_kb.add_button(action.text, color)
            else:
                raise NotImplementedError
    return vk_kb.get_keyboard()
