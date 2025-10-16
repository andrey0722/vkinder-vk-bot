"""This module defines data types that can be shared between components."""

import abc
from collections.abc import Sequence
import dataclasses
import enum
from typing import Literal

from vkinder.model.types import Sex
from vkinder.model.types import User
from vkinder.model.types import UserState

__all__ = (
    'Sex',
    'User',
    'UserState',
    'MainMenu',
    'SearchMenu',
    'Photo',
    'Button',
    'ButtonAction',
    'ButtonColor',
    'InputMessage',
    'Keyboard',
    'OutputMessage',
    'TextAction',
)


@enum.unique
class MainMenu(enum.StrEnum):
    """Commands in main menu."""

    SEARCH = enum.auto()
    PROFILE = enum.auto()
    HELP = enum.auto()


@enum.unique
class SearchMenu(enum.StrEnum):
    """Commands in search menu."""

    NEXT = enum.auto()
    ADD_FAVORITE = enum.auto()
    GO_BACK = enum.auto()


class MediaType(enum.StrEnum):
    """Type of media object."""

    PHOTO = enum.auto()


@dataclasses.dataclass
class Photo:
    """User photo descriptor."""

    id: int
    owner_id: int
    likes: int
    url: str

    type: Literal[MediaType.PHOTO] = MediaType.PHOTO


type Media = Photo


class ButtonColor(enum.StrEnum):
    """Bot button color."""

    PRIMARY = enum.auto()
    SECONDARY = enum.auto()
    NEGATIVE = enum.auto()
    POSITIVE = enum.auto()


@dataclasses.dataclass
class ButtonAction:
    """Base class for bot button action."""


@dataclasses.dataclass
class Button(abc.ABC):
    """Base class for button in bot keyboard."""

    action: ButtonAction
    color: ButtonColor = ButtonColor.SECONDARY


@dataclasses.dataclass
class TextAction(ButtonAction):
    """Text button."""

    text: str


@dataclasses.dataclass
class Keyboard:
    """Contents of bot keyboard shown to user."""

    one_time: bool = False
    """Hide keyboard after the first use."""

    inline: bool = False
    """Attach keyboard to a bot message."""

    button_rows: list[Sequence[Button]] = dataclasses.field(
        default_factory=list,
    )
    """Keyboard buttons grouped by rows."""


@dataclasses.dataclass
class InputMessage:
    """Input message data from a user to a bot."""

    user: User
    text: str


@dataclasses.dataclass
class OutputMessage:
    """Output message data from a bot to a user."""

    user: User
    text: str
    keyboard: Keyboard | None = None
    media: list[Media] = dataclasses.field(default_factory=list)


class ResponseType(enum.IntEnum):
    """Defines bot response type and its parameter set."""

    UNKNOWN_COMMAND = enum.auto()
    """The user has input an invalid command."""

    GREET_NEW_USER = enum.auto()
    """Send greeting text for a new user."""

    MAIN_MENU_HELP = enum.auto()
    """Show main menu help text to the user."""

    SELECT_MENU = enum.auto()
    """Show a prompt to select a menu command to the user."""

    SEARCH_FAILED = enum.auto()
    """The profile search didn't give any results."""

    SEARCH_ERROR = enum.auto()
    """The profile search interrupted by an error."""

    SEARCH_RESULT = enum.auto()
    """Show found profile to the user."""

    ATTACH_MEDIA = enum.auto()
    """Attach media objects to the bot message."""

    PHOTO_FAILED = enum.auto()
    """Could not fetch profile photos."""

    YOUR_PROFILE = enum.auto()
    """Show own profile to the user."""


type ResponseTypesGeneric = Literal[
    ResponseType.UNKNOWN_COMMAND,
    ResponseType.MAIN_MENU_HELP,
    ResponseType.SELECT_MENU,
    ResponseType.SEARCH_FAILED,
    ResponseType.SEARCH_ERROR,
    ResponseType.PHOTO_FAILED,
]
"""All responses supporting without parameters."""


@dataclasses.dataclass
class ResponseGeneric:
    """Basic response without parameters."""

    type: ResponseTypesGeneric


type ResponseTypesWithUser = Literal[
    ResponseType.GREET_NEW_USER,
    ResponseType.SEARCH_RESULT,
    ResponseType.YOUR_PROFILE,
]
"""All responses supporting `user` field."""


@dataclasses.dataclass
class ResponseWithUser:
    """State result with user profile as parameter."""

    type: ResponseTypesWithUser
    user: User


type ResponseTypesWithMedia = Literal[
    ResponseType.ATTACH_MEDIA,
]
"""All responses supporting `media` field."""


@dataclasses.dataclass
class ResponseWithMedia:
    """State result with list of media as parameter."""

    type: ResponseTypesWithMedia
    media: list[Media]


type Response = (
    ResponseGeneric | ResponseWithUser | ResponseWithMedia
)
"""Bot response type to user."""


class ResponseFactory:
    """Contains factory functions for all responses."""

    @staticmethod
    def unknown_command() -> Response:
        """The user has input an invalid command.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(ResponseType.UNKNOWN_COMMAND)

    @staticmethod
    def greet_new_user(user: User) -> Response:
        """Send greeting text for a new user.

        Args:
            user (User): User object.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithUser(
            type=ResponseType.GREET_NEW_USER,
            user=user,
        )

    @staticmethod
    def main_menu_help() -> Response:
        """Show main menu help text to the user.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(ResponseType.MAIN_MENU_HELP)

    @staticmethod
    def select_menu() -> Response:
        """Show a prompt to select a menu command to the user.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(ResponseType.SELECT_MENU)

    @staticmethod
    def search_failed() -> Response:
        """The profile search didn't give any results.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(ResponseType.SEARCH_FAILED)

    @staticmethod
    def search_error() -> Response:
        """The profile search interrupted by an error.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(ResponseType.SEARCH_ERROR)

    @staticmethod
    def search_result(profile: User) -> Response:
        """Send greeting text for a new user.

        Args:
            profile (User): Found user profile.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithUser(
            type=ResponseType.SEARCH_RESULT,
            user=profile,
        )

    @staticmethod
    def attach_media(media: list[Media]) -> Response:
        """Attach media objects to the bot message.

        Args:
            media (list[Media]): List of media objects.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithMedia(
            type=ResponseType.ATTACH_MEDIA,
            media=media,
        )

    @staticmethod
    def photo_failed() -> Response:
        """Could not fetch profile photos.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(ResponseType.PHOTO_FAILED)

    @staticmethod
    def your_profile(user: User) -> Response:
        """Show own profile to the user.

        Args:
            user (User): User object.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithUser(
            type=ResponseType.YOUR_PROFILE,
            user=user,
        )
