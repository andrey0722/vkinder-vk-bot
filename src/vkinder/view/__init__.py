"""This module defines bot message and keyboard templates."""

from collections.abc import Iterable
from collections.abc import Iterator
from typing import Final

from vkinder.shared_types import MENU_OPTIONS
from vkinder.shared_types import Button
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import Keyboard
from vkinder.shared_types import Media
from vkinder.shared_types import MenuToken
from vkinder.shared_types import OutputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseGeneric
from vkinder.shared_types import ResponseType
from vkinder.shared_types import ResponseTypesGeneric
from vkinder.shared_types import ResponseWithMedia
from vkinder.shared_types import ResponseWithUser
from vkinder.shared_types import ResponseWithUserIndex
from vkinder.shared_types import TextAction
from vkinder.shared_types import User
from vkinder.shared_types import UserState

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
    if isinstance(response, ResponseWithMedia):
        return _render_with_media(user, response)
    raise NotImplementedError


def _format_menu(state: UserState) -> str:
    """Internal helper to format menu help for user state.

    Args:
        state (UserState): User state.

    Returns:
        str: Menu help text.
    """
    result: list[str] = []
    for token in MENU_OPTIONS[state]:
        token_str = _MENU_TOKEN_TO_STR[token]
        help_text = HELP_MAP[token_str]
        result.append(
            Strings.HELP_RECORD_TEMPLATE.format(
                command=token_str,
                help=help_text,
            ),
        )
    return '\n'.join(result)


_MENU_HELP_MAP: Final[dict[UserState, str]] = {
    state: _format_menu(state) for state in MENU_OPTIONS
}


_GENERIC_TO_TEXT: Final[dict[ResponseTypesGeneric, str]] = {
    ResponseType.UNKNOWN_COMMAND: Strings.UNKNOWN_COMMAND,
    ResponseType.SELECT_MENU: Strings.SELECT_ACTION,
    ResponseType.SEARCH_FAILED: Strings.SEARCH_FAILED,
    ResponseType.SEARCH_ERROR: Strings.SEARCH_ERROR,
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
        match response.type:
            case ResponseType.MENU_HELP:
                text = _MENU_HELP_MAP[user.state]
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
        keyboard=keyboard or _get_keyboard(user.state),
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
    return Strings.USER_PROFILE_TEMPLATE.format(
        heading=heading,
        first_name=user.first_name or Strings.NOT_SPECIFIED,
        last_name=user.last_name or Strings.NOT_SPECIFIED,
        nickname=user.nickname or Strings.NOT_SPECIFIED,
        sex=SEX_MAP[user.sex],
        birthday=user.birthday or Strings.NOT_SPECIFIED,
        city=user.city or Strings.NOT_SPECIFIED,
        id=user.id,
        url=user.url,
        online=BOOL_MAP[user.online],
    )


_USER_STATE_KEYBOARDS: Final[dict[UserState, Keyboard]] = {
    UserState.MAIN_MENU: Keyboard(
        one_time=False,
        button_rows=[
            [
                Button(TextAction(MenuTokenStr.SEARCH), ButtonColor.PRIMARY),
                Button(TextAction(MenuTokenStr.PROFILE)),
            ],
            [
                Button(TextAction(MenuTokenStr.FAVORITE)),
                Button(TextAction(MenuTokenStr.HELP)),
            ],
        ],
    ),
    UserState.SEARCHING: Keyboard(
        one_time=False,
        button_rows=[
            [
                Button(TextAction(MenuTokenStr.NEXT), ButtonColor.PRIMARY),
                Button(TextAction(MenuTokenStr.ADD_FAVORITE)),
            ],
            [
                Button(TextAction(MenuTokenStr.GO_BACK)),
                Button(TextAction(MenuTokenStr.HELP)),
            ],
        ],
    ),
    UserState.FAVORITE_LIST: Keyboard(
        one_time=False,
        button_rows=[
            [
                Button(TextAction(MenuTokenStr.PREV)),
                Button(TextAction(MenuTokenStr.NEXT)),
            ],
            [
                Button(
                    action=TextAction(MenuTokenStr.DELETE_FAVORITE),
                    color=ButtonColor.NEGATIVE,
                ),
            ],
            [
                Button(TextAction(MenuTokenStr.GO_BACK)),
                Button(TextAction(MenuTokenStr.HELP)),
            ],
        ],
    ),
}
"""Bot keyboard for each user state."""


def _get_keyboard(state: UserState) -> Keyboard | None:
    """Get bot keyboard for a particular user state.

    Args:
        state (UserState): User state.

    Returns:
        Keyboard | None: Bot keyboard if any.
    """
    return _USER_STATE_KEYBOARDS.get(state)
