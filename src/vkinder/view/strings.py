"""This module defines all text strings shown to a bot user."""

import enum
from typing import Final

from vkinder.shared_types import Sex


class Command(tuple[str, ...], enum.ReprEnum):
    """Bot commands with a special actions."""

    START = ('начать', 'привет', 'start', '/start')


@enum.unique
class MainMenuStr(enum.StrEnum):
    """Commands in main menu."""

    SEARCH = '🔍 Поиск'
    PROFILE = '👤 Профиль'
    HELP = '❓ Помощь'


MAIN_HELP_MAP: Final[dict[MainMenuStr, str]] = {
    MainMenuStr.SEARCH: 'поиск анкет',
    MainMenuStr.PROFILE: 'твоя анкета',
    MainMenuStr.HELP: 'это сообщение',
}


@enum.unique
class SearchMenuStr(enum.StrEnum):
    """Commands in search menu."""

    NEXT = '⏭️ Следующая анкета'
    ADD_FAVORITE = '💘 Добавить в избранное'
    GO_BACK = '◀️ Вернуться в главное меню'


class Strings(enum.StrEnum):
    """Messages from the bot to a user."""

    GREETING_NEW_USER = '🎉🎉🎉 Добро пожаловать, {name}! 🎉🎉🎉'
    UNKNOWN_COMMAND = f'Не понял команду. Нажми {MainMenuStr.HELP}'
    SELECT_ACTION = 'Выбери действие:'
    SEARCH_FAILED = (
        '😔 Не удалось найти подходящих пользователей. Попробуй ещё раз!'
    )
    SEARCH_ERROR = (
        '⚠ Поиск не работает по техническим причинам. '
        'Повторите попытку позднее.'
    )
    PROFILE_FAILED = '😔 Не удалось получить данные твоего профиля.'
    NOT_SPECIFIED = 'Не указано'
    PHOTO_URLS_FAILED = '😔 Ссылки на фото недоступны'
    HEADING_USER_PROFILE = 'Анекта пользователя: '
    HEADING_YOUR_PROFILE = 'Твоя анкета: '

    PARAGRAPH_SEPARATOR = '\n\n'
    LINE_SEPARATOR = '─' * 20

    USER_NAME_TEMPLATE = 'id{id}'

    USER_PROFILE_TEMPLATE = (
        '{heading}\n'
        f'{LINE_SEPARATOR}\n'
        'Имя: {first_name}\n'
        'Фамилия: {last_name}\n'
        'Ник: {nickname}\n'
        'Пол: {sex}\n'
        'Дата рождения: {birthday}\n'
        'Город: {city}\n'
        'Ссылка: {url}\n'
        'Сейчас в сети: {online}\n'
    )

    MAIN_MENU_HELP = (
        f'Доступные команды:\n'
        f'{LINE_SEPARATOR}\n'
        f'{'\n'.join(f'{k} - {v}' for k, v in MAIN_HELP_MAP.items())}'
    )


BOOL_MAP: Final[dict[bool, str]] = {
    False: 'Нет',
    True: 'Да',
}


SEX_MAP: Final[dict[Sex, str]] = {
    Sex.NOT_KNOWN: Strings.NOT_SPECIFIED,
    Sex.MALE: 'Мужской',
    Sex.FEMALE: 'Женский',
}
