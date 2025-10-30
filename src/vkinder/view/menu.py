"""This module defines function for processing menu options."""

from typing import Final

from vkinder.shared_types import Keyboard
from vkinder.shared_types import MenuToken
from vkinder.shared_types import OpenLinkButton
from vkinder.shared_types import TextButton

from .strings import MenuTokenStr

STR_TO_MENU_TOKEN: Final[dict[MenuTokenStr, MenuToken]] = {
    MenuTokenStr.SEARCH: MenuToken.SEARCH,
    MenuTokenStr.PROFILE: MenuToken.PROFILE,
    MenuTokenStr.FAVORITE: MenuToken.FAVORITE,
    MenuTokenStr.BLACKLIST: MenuToken.BLACKLIST,
    MenuTokenStr.HELP: MenuToken.HELP,
    MenuTokenStr.PREV: MenuToken.PREV,
    MenuTokenStr.NEXT: MenuToken.NEXT,
    MenuTokenStr.DELETE_FAVORITE: MenuToken.DELETE_FAVORITE,
    MenuTokenStr.DELETE_BLACKLIST: MenuToken.DELETE_BLACKLIST,
    MenuTokenStr.ADD_FAVORITE: MenuToken.ADD_FAVORITE,
    MenuTokenStr.ADD_BLACKLIST: MenuToken.ADD_BLACKLIST,
    MenuTokenStr.GO_BACK: MenuToken.GO_BACK,
}

MENU_TOKEN_TO_STR: Final[dict[MenuToken, MenuTokenStr]] = {
    token: token_str for token_str, token in STR_TO_MENU_TOKEN.items()
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
        token = STR_TO_MENU_TOKEN[token_str]
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
        token_str = MENU_TOKEN_TO_STR[token]
    except KeyError as e:
        raise NotImplementedError from e
    return token_str


def render_keyboard(keyboard: Keyboard) -> None:
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
