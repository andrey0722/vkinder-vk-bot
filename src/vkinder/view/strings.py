"""This module defines all text strings shown to a bot user."""

import enum
from typing import Final

from vkinder.shared_types import Sex


class Command(tuple[str, ...], enum.ReprEnum):
    """Bot commands with a special actions."""

    START = ('начать', 'привет', 'start', '/start')


@enum.unique
class MenuTokenStr(enum.StrEnum):
    """All string tokens acceptable as menu input."""

    SEARCH = '🔍 Поиск'
    PROFILE = '👤 Профиль'
    FAVORITE = '💘 Избранное'
    HELP = '❓ Помощь'
    PREV = '⏪ Предыдущая анкета'
    NEXT = '⏭️ Следующая анкета'
    DELETE_FAVORITE = '❌ Удалить из избранного'
    ADD_FAVORITE = '💘 Добавить в избранное'
    GO_BACK = '🏁 Вернуться в главное меню'


HELP_MAP: Final[dict[MenuTokenStr, str]] = {
    MenuTokenStr.SEARCH: 'поиск анкет',
    MenuTokenStr.PROFILE: 'твоя анкета',
    MenuTokenStr.FAVORITE: 'твой список избранных анкет',
    MenuTokenStr.HELP: 'справка по командам (данное сообщение)',
    MenuTokenStr.PREV: 'перейти к предыдущей анкете',
    MenuTokenStr.NEXT: 'перейти к следующей анкете',
    MenuTokenStr.DELETE_FAVORITE: 'убрать анкету из списка избранных',
    MenuTokenStr.ADD_FAVORITE: 'добавить анкету в список избранных',
    MenuTokenStr.GO_BACK: 'завершить и вернуться в главное меню',
}


class Strings(enum.StrEnum):
    """Messages from the bot to a user."""

    GREETING_NEW_USER = '🎉🎉🎉 Добро пожаловать, {name}! 🎉🎉🎉'
    UNKNOWN_COMMAND = f'Не понял команду. Нажми {MenuTokenStr.HELP}'
    SELECT_ACTION = 'Выбери действие:'
    USER_SEX_MISSING = (
        '🧐 Вы не указали свой пол в профиле, найти пользователей не '
        'получится. Укажите свой пол и повторите попытку!'
    )
    USER_CITY_MISSING = (
        '🧐 Вы не указали свой город в профиле, найти пользователей не '
        'получится. Укажите свой город и повторите попытку!'
    )
    USER_BIRTHDAY_MISSING = (
        '🧐 Вы не указали свою дату и год рождения в профиле, найти '
        'пользователей не получится. Укажите свой город и повторите попытку!'
    )
    SEARCH_FAILED = (
        '😔 Не удалось найти подходящих пользователей. Попробуй ещё раз!'
    )
    SEARCH_ERROR = (
        '⚠ Поиск не работает по техническим причинам. '
        'Повторите попытку позднее.'
    )
    PROFILE_FAILED = '😔 Не удалось получить данные твоего профиля.'
    ADDED_TO_FAVORITE = '➕ Профиль добавлен в избранное!'
    ADD_TO_FAVORITE_FAILED = '⚠ Ошибка добавления в избранное!'
    FAVORITE_LIST_FAILED = '⚠ Ошибка загрузки списка избранных анкет!'
    FAVORITE_LIST_EMPTY = (
        'Список избранных анкет пока пуст, '
        f'используйте команду {MenuTokenStr.ADD_FAVORITE}, '
        'чтобы его наполнить.'
    )
    NOT_SPECIFIED = 'Не указано'
    PHOTO_URLS_FAILED = '😔 Ссылки на фото недоступны'
    HEADING_USER_PROFILE = 'Анекта пользователя: '
    HEADING_YOUR_PROFILE = 'Твоя анкета: '
    AVAILABLE_COMMANDS = 'Доступные команды:'

    PARAGRAPH_SEPARATOR = '\n\n'
    LINE_SEPARATOR = '─' * 20

    USER_NAME_TEMPLATE = 'id{id}'

    HEADING_FAVORITE_TEMPLATE = 'Избранная анекта ({index} / {total}):'

    USER_PROFILE_TEMPLATE = (
        '{heading}\n'
        f'{LINE_SEPARATOR}\n'
        'Имя: {first_name}\n'
        'Фамилия: {last_name}\n'
        'Ник: {nickname}\n'
        'Пол: {sex}\n'
        'Дата рождения: {birthday}\n'
        'Возраст: {age}\n'
        'Город: {city}\n'
        'ID: {id}\n'
        'Ссылка: {url}\n'
        'Сейчас в сети: {online}\n'
    )

    HELP_RECORD_TEMPLATE = '{command} - {help}'

    HELP_TEMPLATE = (
        'Доступные команды:\n'
        f'{LINE_SEPARATOR}\n'
        '{text}'
    )


BIRTHDAY_FORMAT = '%d.%m.%Y'
"""Birthday `strftime()` format."""


BOOL_MAP: Final[dict[bool, str]] = {
    False: 'Нет',
    True: 'Да',
}


SEX_MAP: Final[dict[Sex, str]] = {
    Sex.NOT_KNOWN: Strings.NOT_SPECIFIED,
    Sex.MALE: 'Мужской',
    Sex.FEMALE: 'Женский',
}
