"""This module defines bot message and keyboard templates."""

from typing import Final

from vkinder.shared_types import Button
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import Keyboard
from vkinder.shared_types import OutputMessage
from vkinder.shared_types import TextAction
from vkinder.shared_types import User
from vkinder.shared_types import UserState

from .strings import SEX_MAP
from .strings import MainMenu
from .strings import SearchMenu
from .strings import Strings


class Message:
    """Creates output messages from templates."""

    @staticmethod
    def unknown_command(user: User) -> OutputMessage:
        """The user has input an invalid command.

        Args:
            user (User): User object.

        Returns:
            OutputMessage: Bot output message.
        """
        return Message._create_message(user, Strings.UNKNOWN_COMMAND)

    @staticmethod
    def main_menu_help(user: User) -> OutputMessage:
        """Show main menu help text to the user.

        Args:
            user (User): User object.

        Returns:
            OutputMessage: Bot output message.
        """
        return Message._create_message(user, Strings.MAIN_MENU_HELP)

    @staticmethod
    def select_menu(user: User) -> OutputMessage:
        """Show a prompt to select a menu command to the user.

        Args:
            user (User): User object.

        Returns:
            OutputMessage: Bot output message.
        """
        return Message._create_message(user, Strings.SELECT_ACTION)

    @staticmethod
    def search_failed(user: User) -> OutputMessage:
        """The profile search didn't give any results.

        Args:
            user (User): User object.

        Returns:
            OutputMessage: Bot output message.
        """
        return Message._create_message(user, Strings.SEARCH_FAILED)

    @staticmethod
    def search_error(user: User) -> OutputMessage:
        """The profile search interrupted by an error.

        Args:
            user (User): User object.

        Returns:
            OutputMessage: Bot output message.
        """
        return Message._create_message(user, Strings.SEARCH_ERROR)

    @staticmethod
    def search_result(user: User, profile: User) -> OutputMessage:
        """Show found profile to the user.

        Args:
            user (User): User object.
            profile (User): Found user profile.

        Returns:
            OutputMessage: Bot output message.
        """
        return Message._create_message(user, format_search_profile(profile))

    @staticmethod
    def your_profile(user: User) -> OutputMessage:
        """Show own profile to the user.

        Args:
            user (User): User object.

        Returns:
            OutputMessage: Bot output message.
        """
        return Message._create_message(user, format_your_profile(user))

    @staticmethod
    def _create_message(user: User, text: str) -> OutputMessage:
        """Internal helper to construct output message.

        Args:
            user (User): User object.
            text (str): Output message text.

        Returns:
            OutputMessage: Bot output message.
        """
        return OutputMessage(
            user=user,
            text=text,
            keyboard=get_keyboard(user.state),
        )


def format_your_profile(user: User | None) -> str:
    if not user:
        return Strings.PROFILE_FAILED
    return _format_profile(user, heading=Strings.HEADING_YOUR_PROFILE)


def format_search_profile(user: User | None) -> str:
    if not user:
        return Strings.SEARCH_FAILED
    return _format_profile(user, heading=Strings.HEADING_USER_PROFILE)


def _format_profile(user: User, *, heading: str) -> str:
    return Strings.USER_PROFILE_TEMPLATE.format(
        heading=heading,
        first_name=user.first_name or Strings.NOT_SPECIFIED,
        last_name=user.last_name or Strings.NOT_SPECIFIED,
        sex=SEX_MAP[user.sex],
        birthday=user.birthday or Strings.NOT_SPECIFIED,
        city=user.city or Strings.NOT_SPECIFIED,
    )


_USER_STATE_KEYBOARDS: Final[dict[UserState, Keyboard]] = {
    UserState.MAIN_MENU: Keyboard(
        one_time=False,
        button_rows=[
            [
                Button(TextAction(MainMenu.SEARCH), color=ButtonColor.PRIMARY),
                Button(TextAction(MainMenu.PROFILE)),
            ],
            [
                Button(TextAction(MainMenu.HELP)),
            ],
        ],
    ),
    UserState.SEARCHING: Keyboard(
        one_time=False,
        button_rows=[
            [
                Button(TextAction(SearchMenu.NEXT), color=ButtonColor.PRIMARY),
                Button(TextAction(SearchMenu.ADD_FAVORITE)),
            ],
            [
                Button(TextAction(SearchMenu.GO_BACK)),
            ],
        ],
    ),
}
"""Bot keyboard for each user state."""


def get_keyboard(state: UserState) -> Keyboard | None:
    """Get bot keyboard for a particular user state.

    Args:
        state (UserState): User state.

    Returns:
        Keyboard | None: Bot keyboard if any.
    """
    return _USER_STATE_KEYBOARDS.get(state)
