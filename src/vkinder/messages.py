import enum


class Messages(enum.StrEnum):
    """Messages from the bot to a user."""

    SEARCH_FAILED = (
        '😔 Не удалось найти подходящих пользователей. Попробуй ещё раз!'
    )
    PROFILE_FAILED = '😔 Не удалось получить данные твоего профиля.'
