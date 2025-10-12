"""This module defines all text strings shown to a bot user."""

import enum
from typing import Final

from vkinder.shared_types import Sex


class Command(tuple[str, ...], enum.ReprEnum):
    """Bot commands with a special actions."""

    START = ('начать', 'привет', 'start', '/start')


@enum.unique
class MainMenu(enum.StrEnum):
    """Commands in main menu."""

    SEARCH = '🔍 Поиск'
    PROFILE = '👤 Профиль'
    HELP = '❓ Помощь'


MAIN_HELP_MAP: Final[dict[MainMenu, str]] = {
    MainMenu.SEARCH: 'поиск анкет',
    MainMenu.PROFILE: 'твоя анкета',
    MainMenu.HELP: 'это сообщение',
}


@enum.unique
class SearchMenu(enum.StrEnum):
    """Commands in search menu."""

    NEXT = '⏭️ Следующая анкета'
    ADD_FAVORITE = '💘 Добавить в избранное'
    GO_BACK = '◀️ Вернуться в главное меню'


class Strings(enum.StrEnum):
    """Messages from the bot to a user."""

    GREETING_NEW_USER = '🎉🎉🎉 Добро пожаловать, {name}! 🎉🎉🎉'
    UNKNOWN_COMMAND = f'Не понял команду. Нажми {MainMenu.HELP}'
    SELECT_ACTION = 'Выбери действие:'
    SEARCH_FAILED = (
        '😔 Не удалось найти подходящих пользователей. Попробуй ещё раз!'
    )
    SEARCH_ERROR = (
        '⚠ Поиск не работает по техническим причинам. '
        'Повторите попытку позднее.'
    )
    PROFILE_FAILED = '😔 Не удалось получить данные твоего профиля.'
    NOT_SPECIFIED = 'Не указан'
    HEADING_USER_PROFILE = 'Анекта пользователя: '
    HEADING_YOUR_PROFILE = 'Твоя анкета: '

    SEPARATOR = '─' * 20

    USER_NAME_TEMPLATE = 'id{id}'

    USER_PROFILE_TEMPLATE = (
        '{heading}\n'
        f'{SEPARATOR}\n'
        'Имя: {first_name}\n'
        'Фамилия: {last_name}\n'
        'Пол: {sex}\n'
        'Дата рождения: {birthday}\n'
        'Город: {city}\n'
    )

    MAIN_MENU_HELP = (
        f'Доступные команды:\n'
        f'{SEPARATOR}\n'
        f'{'\n'.join(f'{k} - {v}' for k, v in MAIN_HELP_MAP.items())}'
    )


SEX_MAP: Final[dict[Sex, str]] = {
    Sex.NOT_KNOWN: Strings.NOT_SPECIFIED,
    Sex.MALE: 'Мужской',
    Sex.FEMALE: 'Женский',
}
