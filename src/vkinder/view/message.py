"""This module defines functions for creating message objects."""


from collections.abc import Iterable
from collections.abc import Iterator
from functools import singledispatch
from typing import Final, overload

from vkinder.shared_types import Keyboard
from vkinder.shared_types import Media
from vkinder.shared_types import OutputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseGeneric
from vkinder.shared_types import ResponseType
from vkinder.shared_types import ResponseTypesGeneric
from vkinder.shared_types import ResponseWithKeyboard
from vkinder.shared_types import ResponseWithMedia
from vkinder.shared_types import ResponseWithMenuOptions
from vkinder.shared_types import ResponseWithText
from vkinder.shared_types import ResponseWithUser
from vkinder.shared_types import ResponseWithUserIndex
from vkinder.shared_types import User

from .format import format_help
from .format import format_profile
from .format import get_user_name
from .menu import render_keyboard
from .strings import Strings


def render_messages(
    user: User,
    responses: Iterable[Response],
) -> Iterator[OutputMessage]:
    """Render a sequence of bot responses squashed.

    Args:
        user (User): User object.
        responses (Iterable[Response]): Sequence of bot responses.

    Yields:
        OutputMessage: Bot output messages.
    """
    keyboard: Keyboard | None = None
    paragraphs: list[str] = []
    media: list[Media] = []
    for response in responses:
        if not response.allow_squash:
            if paragraphs:
                # Give previously prepared messages
                yield squash_message(user, paragraphs, keyboard, media)
                keyboard = None
                paragraphs.clear()
                media.clear()
            # This message doesn't allow to squash itself with others
            yield render_response(response, user)
            continue

        message = render_response(response, user)
        # Keep just the last keyboard
        keyboard = message.keyboard or keyboard
        # Collect all text paragraphs
        if message.text:
            paragraphs.append(message.text)
        # Collect media from all messages
        media.extend(message.media)

    if paragraphs:
        # Give the last message
        yield squash_message(user, paragraphs, keyboard, media)


def create_message(
    user: User,
    text: str = '',
    keyboard: Keyboard | None = None,
    media: list[Media] | None = None,
) -> OutputMessage:
    """Constructs output message.

    Args:
        user (User): User object.
        text (str, optional): Output message text. Defaults to ''.
        keyboard (Keyboard | None, optional): Bot keyboard for the
            message. Defaults to None.
        media (list[Media] | None, optional): List of media items to
            attach to the message. Defaults to None.

    Returns:
        OutputMessage: Bot output message.
    """
    return OutputMessage(
        user=user,
        text=text,
        keyboard=keyboard,
        media=media or [],
    )


def squash_message(
    user: User,
    paragraphs: list[str],
    keyboard: Keyboard | None,
    media: list[Media],
) -> OutputMessage:
    """Constructs output message from multiple message parts.

    Args:
        user (User): User object.
        paragraphs (list[str]): Output message text strings.
        keyboard (Keyboard | None): Bot keyboard for the message.
        media (list[Media]): List of media items to attach to the message.

    Returns:
        OutputMessage: Bot output message.
    """
    text = Strings.PARAGRAPH_SEPARATOR.join(paragraphs)
    return create_message(user, text, keyboard, media)


@overload
def render_response(
    response: ResponseGeneric,
    user: User,
) -> OutputMessage: ...


@overload
def render_response(
    response: ResponseWithUser,
    user: User,
) -> OutputMessage: ...


@overload
def render_response(
    response: ResponseWithUserIndex,
    user: User,
) -> OutputMessage: ...


@overload
def render_response(
    response: ResponseWithText,
    user: User,
) -> OutputMessage: ...


@overload
def render_response(
    response: ResponseWithMenuOptions,
    user: User,
) -> OutputMessage: ...


@overload
def render_response(
    response: ResponseWithKeyboard,
    user: User,
) -> OutputMessage: ...


@overload
def render_response(
    response: ResponseWithMedia,
    user: User,
) -> OutputMessage: ...


@singledispatch
def render_response(response: Response, user: User) -> OutputMessage:
    """Render bot response to actual message to send to a user.

    Args:
        response (Response): Bot response object.
        user (User): User object.

    Returns:
        OutputMessage: Bot output message.
    """
    raise NotImplementedError


_GENERIC_TO_TEXT: Final[dict[ResponseTypesGeneric, str]] = {
    ResponseType.BOT_ERROR: Strings.BOT_ERROR,
    ResponseType.UNKNOWN_COMMAND: Strings.UNKNOWN_COMMAND,
    ResponseType.SELECT_MENU: Strings.SELECT_ACTION,
    ResponseType.USER_SEX_MISSING: Strings.USER_SEX_MISSING,
    ResponseType.USER_CITY_MISSING: Strings.USER_CITY_MISSING,
    ResponseType.USER_BIRTHDAY_MISSING: Strings.USER_BIRTHDAY_MISSING,
    ResponseType.SEARCH_FAILED: Strings.SEARCH_FAILED,
    ResponseType.SEARCH_ERROR: Strings.SEARCH_ERROR,
    ResponseType.ADDED_TO_FAVORITE: Strings.ADDED_TO_FAVORITE,
    ResponseType.ADD_TO_FAVORITE_FAILED: Strings.ADD_TO_FAVORITE_FAILED,
    ResponseType.FAVORITE_LIST_FAILED: Strings.FAVORITE_LIST_FAILED,
    ResponseType.FAVORITE_LIST_EMPTY: Strings.FAVORITE_LIST_EMPTY,
    ResponseType.ADDED_TO_BLACKLIST: Strings.ADDED_TO_BLACKLIST,
    ResponseType.ADD_TO_BLACKLIST_FAILED: Strings.ADD_TO_BLACKLIST_FAILED,
    ResponseType.BLACKLIST_FAILED: Strings.BLACKLIST_FAILED,
    ResponseType.BLACKLIST_EMPTY: Strings.BLACKLIST_EMPTY,
    ResponseType.PHOTO_FAILED: Strings.PHOTO_URLS_FAILED,
}


@render_response.register
def _render_generic(
    response: ResponseGeneric,
    user: User,
) -> OutputMessage:
    """Internal helper to render messages without parameters.

    Args:
        response (ResponseGeneric): Bot response object.
        user (User): User object.

    Returns:
        OutputMessage: Bot output message.
    """
    try:
        text = _GENERIC_TO_TEXT[response.type]
    except KeyError as e:
        # Dynamically computed responses
        match response.type:
            case _:
                raise NotImplementedError from e
    return create_message(user, text)


@render_response.register
def _render_with_user(
    response: ResponseWithUser,
    user: User,
) -> OutputMessage:
    """Internal helper to render messages with `user` parameter.

    Args:
        response (ResponseWithUser): Bot response object.
        user (User): User object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.GREET_NEW_USER:
            name = get_user_name(response.user)
            text = Strings.GREETING_NEW_USER.format(name=name)
            return create_message(user, text)

        case ResponseType.SEARCH_RESULT:
            profile = response.user
            heading = Strings.HEADING_USER_PROFILE
            text = format_profile(profile, heading=heading)
            return create_message(user, text)

        case ResponseType.YOUR_PROFILE:
            profile = response.user
            heading = Strings.HEADING_YOUR_PROFILE
            text = format_profile(profile, heading=heading)
            return create_message(user, text)

    raise NotImplementedError


@render_response.register
def _render_with_user_index(
    response: ResponseWithUserIndex,
    user: User,
) -> OutputMessage:
    """Internal helper to render messages with `user` and `index` parameters.

    Args:
        response (ResponseWithUserIndex): Bot response object.
        user (User): User object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.FAVORITE_RESULT:
            heading = Strings.HEADING_FAVORITE_TEMPLATE.format(
                index=response.index,
                total=response.total,
            )
            text = format_profile(response.user, heading=heading)
            return create_message(user, text)

        case ResponseType.BLACKLIST_RESULT:
            heading = Strings.HEADING_BLACKLIST_TEMPLATE.format(
                index=response.index,
                total=response.total,
            )
            text = format_profile(response.user, heading=heading)
            return create_message(user, text)

    raise NotImplementedError


@render_response.register
def _render_with_text(
    response: ResponseWithText,
    user: User,
) -> OutputMessage:
    """Internal helper to render messages with `text` parameter.

    Args:
        response (ResponseWithText): Bot response object.
        user (User): User object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.TEXT:
            # Place text string into message as is
            return create_message(user, response.text)

    raise NotImplementedError


@render_response.register
def _render_with_menu_options(
    response: ResponseWithMenuOptions,
    user: User,
) -> OutputMessage:
    """Internal helper to render messages with `menu_options` parameter.

    Args:
        response (ResponseWithMenuOptions): Bot response object.
        user (User): User object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.MENU_HELP:
            return create_message(user, format_help(response.menu_options))

    raise NotImplementedError


@render_response.register
def _render_with_keyboard(
    response: ResponseWithKeyboard,
    user: User,
) -> OutputMessage:
    """Internal helper to render messages with `keyboard` parameter.

    Args:
        response (ResponseWithKeyboard): Bot response object.
        user (User): User object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.KEYBOARD:
            keyboard = response.keyboard
            render_keyboard(keyboard)
            return create_message(user, keyboard=keyboard)

    raise NotImplementedError


@render_response.register
def _render_with_media(
    response: ResponseWithMedia,
    user: User,
) -> OutputMessage:
    """Internal helper to render messages with `media` parameter.

    Args:
        response (ResponseWithMedia): Bot response object.
        user (User): User object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.ATTACH_MEDIA:
            return create_message(user, media=response.media)

    raise NotImplementedError
