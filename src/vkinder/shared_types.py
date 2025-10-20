"""This module defines data types that can be shared between components."""

from collections.abc import Sequence
import dataclasses
import enum
from typing import Literal

from vkinder.model.types import Favorite
from vkinder.model.types import Sex
from vkinder.model.types import User
from vkinder.model.types import UserAuthData
from vkinder.model.types import UserProgress
from vkinder.model.types import UserState

__all__ = (
    'Favorite',
    'Sex',
    'User',
    'UserAuthData',
    'UserSearchQuery',
    'UserState',
    'MenuToken',
    'Photo',
    'Button',
    'ButtonColor',
    'InputMessage',
    'Keyboard',
    'OutputMessage',
    'TextButton',
    'OpenLinkButton',
)


@enum.unique
class MenuToken(enum.StrEnum):
    """All string tokens acceptable as menu input."""

    SEARCH = enum.auto()
    PROFILE = enum.auto()
    FAVORITE = enum.auto()
    HELP = enum.auto()
    PREV = enum.auto()
    NEXT = enum.auto()
    DELETE_FAVORITE = enum.auto()
    ADD_FAVORITE = enum.auto()
    GO_BACK = enum.auto()
    AUTH_BEGIN = enum.auto()
    AUTH_FINISHED = enum.auto()


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


type ButtonPayloadField = int | str | bool | None | list['ButtonPayload']
type ButtonPayload = dict[str, ButtonPayloadField] | None


@dataclasses.dataclass
class TextButton:
    """Text button."""

    text: str
    color: ButtonColor = ButtonColor.SECONDARY
    payload: ButtonPayload = None


@dataclasses.dataclass
class OpenLinkButton:
    """Button with URL to open."""

    text: str
    link: str
    payload: ButtonPayload = None


type Button = TextButton | OpenLinkButton
"""Button in bot keyboard."""


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
    progress: UserProgress
    chat_id: int | None


@dataclasses.dataclass
class OutputMessage:
    """Output message data from a bot to a user."""

    user: User
    text: str
    keyboard: Keyboard | None = None
    media: list[Media] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class UserSearchQuery:
    """User search parameters."""

    sex: Sex | None = None
    city_id: int | None = None
    online: bool | None = None
    has_photo: bool | None = None
    age_min: int | None = None
    age_max: int | None = None


class ResponseType(enum.IntEnum):
    """Defines bot response type and its parameter set."""

    UNKNOWN_COMMAND = enum.auto()
    """The user has input an invalid command."""

    GREET_NEW_USER = enum.auto()
    """Send greeting text for a new user."""

    MENU_HELP = enum.auto()
    """Show menu help text to the user."""

    SELECT_MENU = enum.auto()
    """Show a prompt to select a menu command to the user."""

    USER_SEX_MISSING = enum.auto()
    """User has not specified their sex in the user profile."""

    USER_CITY_MISSING = enum.auto()
    """User has not specified their city in the user profile."""

    USER_BIRTHDAY_MISSING = enum.auto()
    """User has not specified their birthday in the user profile."""

    SEARCH_FAILED = enum.auto()
    """The profile search didn't give any results."""

    SEARCH_ERROR = enum.auto()
    """The profile search interrupted by an error."""

    SEARCH_RESULT = enum.auto()
    """Show found profile to the user."""

    AUTH_REQUIRED = enum.auto()
    """Authorization required to continue with current operation."""

    AUTH_NOT_COMPLETED = enum.auto()
    """Authorization hasn't been completed by user."""

    ADDED_TO_FAVORITE = enum.auto()
    """Added last found profile to user's favorite list."""

    ADD_TO_FAVORITE_FAILED = enum.auto()
    """Failed to add profile to user's favorite list."""

    FAVORITE_LIST_FAILED = enum.auto()
    """Failed to show user's favorite list."""

    FAVORITE_LIST_EMPTY = enum.auto()
    """User's favorite list is empty."""

    FAVORITE_RESULT = enum.auto()
    """Show user's favorite list entry."""

    TEXT = enum.auto()
    """Show text string to user."""

    KEYBOARD = enum.auto()
    """Set keyboard for the bot message."""

    ATTACH_MEDIA = enum.auto()
    """Attach media objects to the bot message."""

    PHOTO_FAILED = enum.auto()
    """Could not fetch profile photos."""

    YOUR_PROFILE = enum.auto()
    """Show own profile to the user."""


type ResponseTypesGeneric = Literal[
    ResponseType.UNKNOWN_COMMAND,
    ResponseType.SELECT_MENU,
    ResponseType.USER_SEX_MISSING,
    ResponseType.USER_CITY_MISSING,
    ResponseType.USER_BIRTHDAY_MISSING,
    ResponseType.SEARCH_FAILED,
    ResponseType.SEARCH_ERROR,
    ResponseType.AUTH_REQUIRED,
    ResponseType.AUTH_NOT_COMPLETED,
    ResponseType.ADDED_TO_FAVORITE,
    ResponseType.ADD_TO_FAVORITE_FAILED,
    ResponseType.FAVORITE_LIST_FAILED,
    ResponseType.FAVORITE_LIST_EMPTY,
    ResponseType.PHOTO_FAILED,
]
"""All responses supporting without parameters."""


@dataclasses.dataclass
class ResponseGeneric:
    """Basic response without parameters."""

    type: ResponseTypesGeneric

    allow_squash: bool = True
    """Allow response message to be squashed with others."""


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

    allow_squash: bool = True
    """Allow response message to be squashed with others."""


type ResponseTypesWithUserIndex = Literal[
    ResponseType.FAVORITE_RESULT,
]
"""All responses supporting `user` and `index` fields."""


@dataclasses.dataclass
class ResponseWithUserIndex:
    """State result with user profile and index as parameters."""

    type: ResponseTypesWithUserIndex
    user: User
    index: int
    total: int

    allow_squash: bool = True
    """Allow response message to be squashed with others."""


type ResponseTypesWithText = Literal[
    ResponseType.TEXT,
]
"""All responses supporting `text` field."""


@dataclasses.dataclass
class ResponseWithText:
    """State result with text as parameter."""

    type: ResponseTypesWithText
    text: str

    allow_squash: bool = True
    """Allow response message to be squashed with others."""


type ResponseTypesWithMenuOptions = Literal[
    ResponseType.MENU_HELP,
]
"""All responses supporting `menu_options` field."""


@dataclasses.dataclass
class ResponseWithMenuOptions:
    """State result with menu options as parameter."""

    type: ResponseTypesWithMenuOptions
    menu_options: Sequence[MenuToken]

    allow_squash: bool = True
    """Allow response message to be squashed with others."""


type ResponseTypesWithKeyboard = Literal[
    ResponseType.KEYBOARD,
]
"""All responses supporting `keyboard` field."""


@dataclasses.dataclass
class ResponseWithKeyboard:
    """State result with keyboard as parameter."""

    type: ResponseTypesWithKeyboard
    keyboard: Keyboard

    allow_squash: bool = True
    """Allow response message to be squashed with others."""


type ResponseTypesWithMedia = Literal[
    ResponseType.ATTACH_MEDIA,
]
"""All responses supporting `media` field."""


@dataclasses.dataclass
class ResponseWithMedia:
    """State result with list of media as parameter."""

    type: ResponseTypesWithMedia
    media: list[Media]

    allow_squash: bool = True
    """Allow response message to be squashed with others."""


type Response = (
    ResponseGeneric
    | ResponseWithUser
    | ResponseWithUserIndex
    | ResponseWithText
    | ResponseWithMenuOptions
    | ResponseWithKeyboard
    | ResponseWithMedia
)
"""Bot response type to user."""


class ResponseFactory:
    """Contains factory functions for all responses."""

    @staticmethod
    def unknown_command(*, allow_squash: bool = True) -> Response:
        """The user has input an invalid command.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.UNKNOWN_COMMAND,
            allow_squash=allow_squash,
        )

    @staticmethod
    def greet_new_user(user: User, *, allow_squash: bool = True) -> Response:
        """Send greeting text for a new user.

        Args:
            user (User): User object.
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithUser(
            type=ResponseType.GREET_NEW_USER,
            user=user,
            allow_squash=allow_squash,
        )

    @staticmethod
    def menu_help(
        menu_options: Sequence[MenuToken],
        *,
        allow_squash: bool = True,
    ) -> Response:
        """Show menu help text to the user.

        Args:
            menu_options (Sequence[MenuToken]): Menu options.
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithMenuOptions(
            type=ResponseType.MENU_HELP,
            menu_options=menu_options,
            allow_squash=allow_squash,
        )

    @staticmethod
    def select_menu(*, allow_squash: bool = True) -> Response:
        """Show a prompt to select a menu command to the user.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.SELECT_MENU,
            allow_squash=allow_squash,
        )

    @staticmethod
    def user_sex_missing(*, allow_squash: bool = True) -> Response:
        """User has not specified their sex in the user profile.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.USER_SEX_MISSING,
            allow_squash=allow_squash,
        )

    @staticmethod
    def user_city_missing(*, allow_squash: bool = True) -> Response:
        """User has not specified their city in the user profile.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.USER_CITY_MISSING,
            allow_squash=allow_squash,
        )

    @staticmethod
    def user_birthday_missing(*, allow_squash: bool = True) -> Response:
        """User has not specified their birthday in the user profile.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.USER_BIRTHDAY_MISSING,
            allow_squash=allow_squash,
        )

    @staticmethod
    def search_failed(*, allow_squash: bool = True) -> Response:
        """The profile search didn't give any results.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.SEARCH_FAILED,
            allow_squash=allow_squash,
        )

    @staticmethod
    def search_error(*, allow_squash: bool = True) -> Response:
        """The profile search interrupted by an error.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.SEARCH_ERROR,
            allow_squash=allow_squash,
        )

    @staticmethod
    def auth_required(*, allow_squash: bool = True) -> Response:
        """Authorization required to continue with current operation.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.AUTH_REQUIRED,
            allow_squash=allow_squash,
        )

    @staticmethod
    def auth_not_completed(*, allow_squash: bool = True) -> Response:
        """Authorization hasn't been completed by user.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.AUTH_NOT_COMPLETED,
            allow_squash=allow_squash,
        )

    @staticmethod
    def search_result(
        profile: User,
        *,
        allow_squash: bool = True,
    ) -> Response:
        """Send greeting text for a new user.

        Args:
            profile (User): Found user profile.
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithUser(
            type=ResponseType.SEARCH_RESULT,
            user=profile,
            allow_squash=allow_squash,
        )

    @staticmethod
    def added_to_favorite(*, allow_squash: bool = True) -> Response:
        """Added last found profile to user's favorite list.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.ADDED_TO_FAVORITE,
            allow_squash=allow_squash,
        )

    @staticmethod
    def add_to_favorite_failed(*, allow_squash: bool = True) -> Response:
        """Failed to add profile to user's favorite list.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.ADD_TO_FAVORITE_FAILED,
            allow_squash=allow_squash,
        )

    @staticmethod
    def favorite_list_failed(*, allow_squash: bool = True) -> Response:
        """Failed to show user's favorite list.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.FAVORITE_LIST_FAILED,
            allow_squash=allow_squash,
        )

    @staticmethod
    def favorite_list_empty(*, allow_squash: bool = True) -> Response:
        """User's favorite list is empty.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.FAVORITE_LIST_EMPTY,
            allow_squash=allow_squash,
        )

    @staticmethod
    def favorite_result(
        profile: User,
        index: int,
        total: int,
        *,
        allow_squash: bool = True,
    ) -> Response:
        """Send greeting text for a new user.

        Args:
            profile (User): Found user profile.
            index (int): User profile index number.
            total (int): Total number of user profiles.
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithUserIndex(
            type=ResponseType.FAVORITE_RESULT,
            user=profile,
            index=index,
            total=total,
            allow_squash=allow_squash,
        )

    @staticmethod
    def text(
        text: str,
        *,
        allow_squash: bool = True,
    ) -> Response:
        """Show text string to user.

        Args:
            text (str): Text to show to user.
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithText(
            type=ResponseType.TEXT,
            text=text,
            allow_squash=allow_squash,
        )

    @staticmethod
    def keyboard(
        keyboard: Keyboard,
        *,
        allow_squash: bool = True,
    ) -> Response:
        """Set keyboard for the bot message.

        Args:
            keyboard (list[Media]): Bot keyboard object.
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithKeyboard(
            type=ResponseType.KEYBOARD,
            keyboard=keyboard,
            allow_squash=allow_squash,
        )

    @staticmethod
    def attach_media(
        media: list[Media],
        *,
        allow_squash: bool = True,
    ) -> Response:
        """Attach media objects to the bot message.

        Args:
            media (list[Media]): List of media objects.
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithMedia(
            type=ResponseType.ATTACH_MEDIA,
            media=media,
            allow_squash=allow_squash,
        )

    @staticmethod
    def photo_failed(*, allow_squash: bool = True) -> Response:
        """Could not fetch profile photos.

        Args:
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseGeneric(
            type=ResponseType.PHOTO_FAILED,
            allow_squash=allow_squash,
        )

    @staticmethod
    def your_profile(user: User, *, allow_squash: bool = True) -> Response:
        """Show own profile to the user.

        Args:
            user (User): User object.
            allow_squash (bool, optional): Allow response message to be
                squashed with others. Defaults to True.

        Returns:
            Response: Bot response to user.
        """
        return ResponseWithUser(
            type=ResponseType.YOUR_PROFILE,
            user=user,
            allow_squash=allow_squash,
        )
