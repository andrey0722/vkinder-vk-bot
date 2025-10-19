
from collections.abc import Sequence

from vkinder.shared_types import MenuToken
from vkinder.shared_types import User

from .menu import MENU_TOKEN_TO_STR
from .strings import BIRTHDAY_FORMAT
from .strings import BOOL_MAP
from .strings import HELP_MAP
from .strings import SEX_MAP
from .strings import Strings


def format_help(menu_options: Sequence[MenuToken]) -> str:
    """Format menu help for user state.

    Args:
        menu_options (Sequence[MenuToken]): Menu options.

    Returns:
        str: Menu help text.
    """
    result: list[str] = []
    for token in menu_options:
        token_str = MENU_TOKEN_TO_STR[token]
        help_text = HELP_MAP[token_str]
        result.append(
            Strings.HELP_RECORD_TEMPLATE.format(
                command=token_str,
                help=help_text,
            ),
        )
    return Strings.HELP_RECORD_SEPARATOR.join(result)


def get_user_name(user: User) -> str:
    """Returns display name string for user profile.

    Args:
        user (User): User object.

    Returns:
        str: User display name string.
    """
    return user.first_name or Strings.USER_NAME_TEMPLATE.format(id=user.id)


def format_profile(user: User, *, heading: str) -> str:
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
