"""This module defines bot message and keyboard templates."""

from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Final

from vkinder.shared_types import Keyboard
from vkinder.shared_types import Media
from vkinder.shared_types import MenuToken
from vkinder.shared_types import OpenLinkButton
from vkinder.shared_types import OutputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseGeneric
from vkinder.shared_types import ResponseType
from vkinder.shared_types import ResponseTypesGeneric
from vkinder.shared_types import ResponseWithKeyboard
from vkinder.shared_types import ResponseWithMedia
from vkinder.shared_types import ResponseWithMenuOptions
from vkinder.shared_types import ResponseWithUser
from vkinder.shared_types import ResponseWithUserIndex
from vkinder.shared_types import TextButton
from vkinder.shared_types import User

from .strings import BIRTHDAY_FORMAT
from .strings import BOOL_MAP
from .strings import HELP_MAP
from .strings import SEX_MAP
from .strings import MenuTokenStr
from .strings import Strings

_STR_TO_MENU_TOKEN: Final[dict[MenuTokenStr, MenuToken]] = {
    MenuTokenStr.SEARCH: MenuToken.SEARCH,
    MenuTokenStr.PROFILE: MenuToken.PROFILE,
    MenuTokenStr.FAVORITE: MenuToken.FAVORITE,
    MenuTokenStr.HELP: MenuToken.HELP,
    MenuTokenStr.PREV: MenuToken.PREV,
    MenuTokenStr.NEXT: MenuToken.NEXT,
    MenuTokenStr.DELETE_FAVORITE: MenuToken.DELETE_FAVORITE,
    MenuTokenStr.ADD_FAVORITE: MenuToken.ADD_FAVORITE,
    MenuTokenStr.GO_BACK: MenuToken.GO_BACK,
    MenuTokenStr.AUTH_BEGIN: MenuToken.AUTH_BEGIN,
    MenuTokenStr.AUTH_FINISHED: MenuToken.AUTH_FINISHED,
}

_MENU_TOKEN_TO_STR: Final[dict[MenuToken, MenuTokenStr]] = {
    token: token_str for token_str, token in _STR_TO_MENU_TOKEN.items()
}


def normalize_menu_command(text: str) -> str:
    """Replace menu item in input message with a command.

    Args:
        text (str): User input text message.

    Returns:
        str: Normalized text message.
    """
    try:
        token_str = MenuTokenStr(text)
    except ValueError:
        return text
    try:
        token = _STR_TO_MENU_TOKEN[token_str]
    except KeyError as e:
        raise NotImplementedError from e
    return token


def render_menu_command(text: str) -> str:
    """Replace menu token in output message with a text string.

    Args:
        text (str): Output text message.

    Returns:
        str: Updated text message.
    """
    try:
        token = MenuToken(text)
    except ValueError:
        return text
    try:
        token_str = _MENU_TOKEN_TO_STR[token]
    except KeyError as e:
        raise NotImplementedError from e
    return token_str


def render_squashed_messages(
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
                yield _squash_message(user, paragraphs, keyboard, media)
                keyboard = None
                paragraphs.clear()
                media.clear()
            # This message doesn't allow to squash itself with others
            yield render_message(user, response)
            continue

        message = render_message(user, response)
        # Keep just the last keyboard
        keyboard = message.keyboard or keyboard
        # Collect all text paragraphs
        paragraphs.append(message.text)
        # Collect media from all messages
        media.extend(message.media)

    if paragraphs:
        # Give the last message
        yield _squash_message(user, paragraphs, keyboard, media)


def render_message(user: User, response: Response) -> OutputMessage:
    """Render bot response to actual message to send to a user.

    Args:
        user (User): User object.
        response (Response): Bot response object.

    Returns:
        OutputMessage: Bot output message.
    """
    if isinstance(response, ResponseGeneric):
        return _render_generic(user, response)
    if isinstance(response, ResponseWithUser):
        return _render_with_user(user, response)
    if isinstance(response, ResponseWithUserIndex):
        return _render_with_user_index(user, response)
    if isinstance(response, ResponseWithMenuOptions):
        return _render_with_menu_options(user, response)
    if isinstance(response, ResponseWithKeyboard):
        return _render_with_keyboard(user, response)
    if isinstance(response, ResponseWithMedia):
        return _render_with_media(user, response)
    raise NotImplementedError


def _format_menu(menu_options: Sequence[MenuToken]) -> str:
    """Internal helper to format menu help for user state.

    Args:
        menu_options (Sequence[MenuToken]): Menu options.

    Returns:
        str: Menu help text.
    """
    result: list[str] = []
    for token in menu_options:
        token_str = _MENU_TOKEN_TO_STR[token]
        help_text = HELP_MAP[token_str]
        result.append(
            Strings.HELP_RECORD_TEMPLATE.format(
                command=token_str,
                help=help_text,
            ),
        )
    return Strings.HELP_RECORD_SEPARATOR.join(result)


_GENERIC_TO_TEXT: Final[dict[ResponseTypesGeneric, str]] = {
    ResponseType.UNKNOWN_COMMAND: Strings.UNKNOWN_COMMAND,
    ResponseType.SELECT_MENU: Strings.SELECT_ACTION,
    ResponseType.USER_SEX_MISSING: Strings.USER_SEX_MISSING,
    ResponseType.USER_CITY_MISSING: Strings.USER_CITY_MISSING,
    ResponseType.USER_BIRTHDAY_MISSING: Strings.USER_BIRTHDAY_MISSING,
    ResponseType.SEARCH_FAILED: Strings.SEARCH_FAILED,
    ResponseType.SEARCH_ERROR: Strings.SEARCH_ERROR,
    ResponseType.AUTH_REQUIRED: Strings.AUTH_REQUIRED,
    ResponseType.AUTH_NOT_COMPLETED: Strings.AUTH_NOT_COMPLETED,
    ResponseType.ADDED_TO_FAVORITE: Strings.ADDED_TO_FAVORITE,
    ResponseType.ADD_TO_FAVORITE_FAILED: Strings.ADD_TO_FAVORITE_FAILED,
    ResponseType.FAVORITE_LIST_FAILED: Strings.FAVORITE_LIST_FAILED,
    ResponseType.FAVORITE_LIST_EMPTY: Strings.FAVORITE_LIST_EMPTY,
    ResponseType.PHOTO_FAILED: Strings.PHOTO_URLS_FAILED,
}


def _render_generic(user: User, response: ResponseGeneric) -> OutputMessage:
    """Internal helper to render messages without parameters.

    Args:
        user (User): User object.
        response (ResponseGeneric): Bot response object.

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
    return _create_message(user, text)


def _render_with_user(
    user: User,
    response: ResponseWithUser,
) -> OutputMessage:
    """Internal helper to render messages with `user` parameter.

    Args:
        user (User): User object.
        response (ResponseWithUser): Bot response object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.GREET_NEW_USER:
            name = _get_user_name(response.user)
            text = Strings.GREETING_NEW_USER.format(name=name)
            return _create_message(user, text)

        case ResponseType.SEARCH_RESULT:
            profile = response.user
            heading = Strings.HEADING_USER_PROFILE
            text = _format_profile(profile, heading=heading)
            return _create_message(user, text)

        case ResponseType.YOUR_PROFILE:
            profile = response.user
            heading = Strings.HEADING_YOUR_PROFILE
            text = _format_profile(profile, heading=heading)
            return _create_message(user, text)

    raise NotImplementedError


def _render_with_user_index(
    user: User,
    response: ResponseWithUserIndex,
) -> OutputMessage:
    """Internal helper to render messages with `user` and `index` parameters.

    Args:
        user (User): User object.
        response (ResponseWithUserIndex): Bot response object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.FAVORITE_RESULT:
            profile = response.user
            heading = Strings.HEADING_FAVORITE_TEMPLATE.format(
                index=response.index,
                total=response.total,
            )
            text = _format_profile(profile, heading=heading)
            return _create_message(user, text)

    raise NotImplementedError


def _render_with_menu_options(
    user: User,
    response: ResponseWithMenuOptions,
) -> OutputMessage:
    """Internal helper to render messages with `menu_options` parameter.

    Args:
        user (User): User object.
        response (ResponseWithMenuOptions): Bot response object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.MENU_HELP:
            return _create_message(user, _format_menu(response.menu_options))

    raise NotImplementedError


def _render_keyboard(keyboard: Keyboard) -> None:
    """Process all keyboard button and prepare them to be sent to user.

    Args:
        keyboard (Keyboard): Bot keyboard object.
    """
    for row in keyboard.button_rows:
        for button in row:
            if isinstance(button, (TextButton, OpenLinkButton)):
                button.text = render_menu_command(button.text)
            else:
                raise NotImplementedError


def _render_with_keyboard(
    user: User,
    response: ResponseWithKeyboard,
) -> OutputMessage:
    """Internal helper to render messages with `keyboard` parameter.

    Args:
        user (User): User object.
        response (ResponseWithKeyboard): Bot response object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.KEYBOARD:
            keyboard = response.keyboard
            _render_keyboard(keyboard)
            return _create_message(user, keyboard=keyboard)

    raise NotImplementedError


def _render_with_media(
    user: User,
    response: ResponseWithMedia,
) -> OutputMessage:
    """Internal helper to render messages with `media` parameter.

    Args:
        user (User): User object.
        response (ResponseWithMedia): Bot response object.

    Returns:
        OutputMessage: Bot output message.
    """
    match response.type:
        case ResponseType.ATTACH_MEDIA:
            return _create_message(user, media=response.media)

    raise NotImplementedError


def _create_message(
    user: User,
    text: str = '',
    keyboard: Keyboard | None = None,
    media: list[Media] | None = None,
) -> OutputMessage:
    """Internal helper to construct output message.

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


def _squash_message(
    user: User,
    paragraphs: list[str],
    keyboard: Keyboard | None,
    media: list[Media],
) -> OutputMessage:
    """Internal helper to construct output message.

    Args:
        user (User): User object.
        paragraphs (list[str]): Output message text strings.
        keyboard (Keyboard | None): Bot keyboard for the message.
        media (list[Media]): List of media items to attach to the message.

    Returns:
        OutputMessage: Bot output message.
    """
    text = Strings.PARAGRAPH_SEPARATOR.join(paragraphs)
    return _create_message(user, text, keyboard, media)


def _get_user_name(user: User) -> str:
    """Returns display name string for user profile.

    Args:
        user (User): User object.

    Returns:
        str: User display name string.
    """
    return user.first_name or Strings.USER_NAME_TEMPLATE.format(id=user.id)


def _format_profile(user: User, *, heading: str) -> str:
    """Formats user profile to string using template.

    Args:
        user (User): User object.
        heading (str): Heading string.

    Returns:
        str: Formatted user profile.
    """
    birthday = user.birthday and user.birthday.strftime(BIRTHDAY_FORMAT)
    birthday = birthday or user.birthday_raw
    return Strings.USER_PROFILE_TEMPLATE.format(
        heading=heading,
        first_name=user.first_name or Strings.NOT_SPECIFIED,
        last_name=user.last_name or Strings.NOT_SPECIFIED,
        nickname=user.nickname or Strings.NOT_SPECIFIED,
        sex=SEX_MAP[user.sex],
        birthday=birthday or Strings.NOT_SPECIFIED,
        age=user.age or Strings.NOT_SPECIFIED,
        city=user.city or Strings.NOT_SPECIFIED,
        id=user.id,
        url=user.url,
        online=BOOL_MAP[user.online],
    )
