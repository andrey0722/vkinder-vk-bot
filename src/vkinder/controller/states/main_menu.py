"""This module shows main menu to user and handles user selection in it."""

from collections.abc import Iterator
from typing import override

from vkinder.model import DatabaseSession
from vkinder.shared_types import InputMessage
from vkinder.shared_types import OutputMessage
from vkinder.shared_types import UserState
from vkinder.view import MainMenu
from vkinder.view import Message

from .state import State


class MainMenuState(State):
    """Shows bot main menu to user and handles user selection in that menu."""

    @override
    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[OutputMessage]:
        self._logger.info('Starting for user %d', message.user.id)
        yield Message.select_menu(message.user)

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[OutputMessage]:
        user = message.user
        text = message.text
        self._logger.info('User %d selected in main menu: %s', user.id, text)

        # Match user selection in main menu
        match text:
            case MainMenu.SEARCH:
                yield from self._manager.start(
                    session=session,
                    message=message,
                    state=UserState.SEARCHING,
                )

            case MainMenu.PROFILE:
                yield Message.your_profile(message.user)
                yield from self.start(session, message)

            case MainMenu.HELP:
                yield Message.main_menu_help(message.user)
                yield from self.start(session, message)

            case _:
                self._logger.warning('Unknown main menu option: %s', text)
                yield Message.unknown_command(user)
                yield from self.start(session, message)
