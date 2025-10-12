"""This module defines data types that can be shared between components."""

import abc
from collections.abc import Sequence
import dataclasses
import enum

from vkinder.model import Sex
from vkinder.model import User
from vkinder.model import UserState

__all__ = (
    'Sex',
    'User',
    'UserState',
    'Button',
    'ButtonAction',
    'ButtonColor',
    'InputMessage',
    'Keyboard',
    'OutputMessage',
    'TextAction',
)

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
