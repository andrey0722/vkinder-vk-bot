"""This module shows main menu to user and handles user selection in it."""

from collections.abc import Iterator
from typing import override

from vkinder.shared_types import InputMessage
from vkinder.shared_types import MainMenu
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory

from ..db import DatabaseSession
from ..types import UserState
from .state import State


class MainMenuState(State):
    """Shows bot main menu to user and handles user selection in that menu."""

    @override
    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        self._logger.info('Starting for user %d', message.user.id)
        yield ResponseFactory.select_menu()

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        user = message.user
        text = message.text
        self._logger.info('User %d selected in main menu: %r', user.id, text)

        # Match user selection in main menu
        match text:
            case MainMenu.SEARCH:
                yield from self._manager.start(
                    session=session,
                    message=message,
                    state=UserState.SEARCHING,
                )

            case MainMenu.PROFILE:
                yield ResponseFactory.your_profile(message.user)
                yield from self.start(session, message)

            case MainMenu.HELP:
                yield ResponseFactory.main_menu_help()
                yield from self.start(session, message)

            case _:
                self._logger.warning('Unknown main menu option: %s', text)
                yield ResponseFactory.unknown_command()
                yield from self.start(session, message)
