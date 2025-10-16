"""This module defines bot message and keyboard templates."""

from collections.abc import Iterable
from typing import Final

from vkinder.shared_types import Button
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import Keyboard
from vkinder.shared_types import MainMenu
from vkinder.shared_types import Media
from vkinder.shared_types import OutputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseGeneric
from vkinder.shared_types import ResponseType
from vkinder.shared_types import ResponseTypesGeneric
from vkinder.shared_types import ResponseWithMedia
from vkinder.shared_types import ResponseWithUser
from vkinder.shared_types import SearchMenu
from vkinder.shared_types import TextAction
from vkinder.shared_types import User
from vkinder.shared_types import UserState

from .strings import BOOL_MAP
from .strings import SEX_MAP
from .strings import MainMenuStr
from .strings import SearchMenuStr
from .strings import Strings

_STR_TO_MENU_COMMAND: Final[dict[str, str]] = {
    MainMenuStr.SEARCH: MainMenu.SEARCH,
    MainMenuStr.PROFILE: MainMenu.PROFILE,
    MainMenuStr.HELP: MainMenu.HELP,
    SearchMenuStr.NEXT: SearchMenu.NEXT,
    SearchMenuStr.ADD_FAVORITE: SearchMenu.ADD_FAVORITE,
    SearchMenuStr.GO_BACK: SearchMenu.GO_BACK,
}


def normalize_menu_command(text: str) -> str:
    """Replace menu item in input message with a command.

    Args:
        text (str): User input text message.

    Returns:
        str: Normalized text message.
    """
    return _STR_TO_MENU_COMMAND.get(text, text)


def render_squashed_message(
    user: User,
    responses: Iterable[Response],
) -> OutputMessage:
    """Render a sequence of bot responses to single message to send to a user.

    Args:
        user (User): User object.
        responses (Iterable[Response]): Sequence of bot responses.

    Returns:
        OutputMessage: _description_
    """
    keyboard: Keyboard | None = None
    paragraphs: list[str] = []
    media: list[Media] = []
    for response in responses:
        message = render_message(user, response)
        # Keep just the last keyboard
        keyboard = message.keyboard
        # Collect all text paragraphs
        paragraphs.append(message.text)
        # Collect media from all messages
        media.extend(message.media)

    return OutputMessage(
        user=user,
        text=Strings.PARAGRAPH_SEPARATOR.join(paragraphs),
        keyboard=keyboard,
        media=media or [],
    )


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
    if isinstance(response, ResponseWithMedia):
        return _render_with_media(user, response)
    raise NotImplementedError


_GENERIC_TO_TEXT: Final[dict[ResponseTypesGeneric, str]] = {
    ResponseType.UNKNOWN_COMMAND: Strings.UNKNOWN_COMMAND,
    ResponseType.MAIN_MENU_HELP: Strings.MAIN_MENU_HELP,
    ResponseType.SELECT_MENU: Strings.SELECT_ACTION,
    ResponseType.SEARCH_FAILED: Strings.SEARCH_FAILED,
    ResponseType.SEARCH_ERROR: Strings.SEARCH_ERROR,
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
    media: list[Media] | None = None,
) -> OutputMessage:
    """Internal helper to construct output message.

    Args:
        user (User): User object.
        text (str, optional): Output message text. Defaults to ''.
        media (list[Media] | None, optional): List of media items to
            attach to the message. Defaults to None.

    Returns:
        OutputMessage: Bot output message.
    """
    return OutputMessage(
        user=user,
        text=text,
        keyboard=_get_keyboard(user.state),
        media=media or [],
    )


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
        url=user.url,
        online=BOOL_MAP[user.online],
    )


_USER_STATE_KEYBOARDS: Final[dict[UserState, Keyboard]] = {
    UserState.MAIN_MENU: Keyboard(
        one_time=False,
        button_rows=[
            [
                Button(TextAction(MainMenuStr.SEARCH), ButtonColor.PRIMARY),
                Button(TextAction(MainMenuStr.PROFILE)),
            ],
            [
                Button(TextAction(MainMenuStr.HELP)),
            ],
        ],
    ),
    UserState.SEARCHING: Keyboard(
        one_time=False,
        button_rows=[
            [
                Button(TextAction(SearchMenuStr.NEXT), ButtonColor.PRIMARY),
                Button(TextAction(SearchMenuStr.ADD_FAVORITE)),
            ],
            [
                Button(TextAction(SearchMenuStr.GO_BACK)),
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
