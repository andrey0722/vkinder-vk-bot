"""This module defines bot message and keyboard templates."""

from collections.abc import Sequence
import dataclasses
import enum

from ..model.types import User


class ButtonColor(enum.StrEnum):
    """Bot button color."""

    PRIMARY = enum.auto()
    SECONDARY = enum.auto()
    NEGATIVE = enum.auto()
    POSITIVE = enum.auto()


@dataclasses.dataclass
class Button:
    """Base class for button in bot keyboard."""

    type: str
    color: ButtonColor


@dataclasses.dataclass
class TextButton(Button):
    """Text button in bot keyboard."""

    label: str

    type = 'text'
    color = ButtonColor.SECONDARY


@dataclasses.dataclass
class BotKeyboard:
    """Contents of bot keyboard shown to user."""

    buttons: list[Sequence[Button]]

    def add_row(self, row: Sequence[Button]) -> None:
        self.buttons.append(row)


@dataclasses.dataclass
class OutputMessage:
    """Output message data from a bot to a user."""

    user: User
    text: str
    keyboard: BotKeyboard | None = None

    def add_paragraph_before(
        self,
        paragraph: str,
        *,
        separator: str = '\n\n',
    ) -> None:
        r"""Add a paragraph before current message text.

        Args:
            paragraph (str): Text paragraph to add.
            separator (str, optional): Optional separator value between
                paragraphs. Defaults to `'\n\n'`.
        """
        self.text = separator.join([paragraph, self.text])
