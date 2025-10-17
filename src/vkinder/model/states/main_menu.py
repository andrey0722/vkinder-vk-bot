"""This module shows main menu to user and handles user selection in it."""

from collections.abc import Iterator
from typing import override

from vkinder.shared_types import InputMessage
from vkinder.shared_types import MenuToken
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
        with session.begin():
            user = message.user
        text = message.text
        self._logger.info('User %d selected in main menu: %r', user.id, text)

        if not self.is_command_accepted(message):
            yield from self.unknown_command(session, message)
            return

        # Match user selection in main menu
        match text:
            case MenuToken.SEARCH:
                yield from self._manager.start(
                    session=session,
                    message=message,
                    state=UserState.SEARCHING,
                )

            case MenuToken.PROFILE:
                yield ResponseFactory.your_profile(message.user)
                yield from self.start(session, message)

            case MenuToken.FAVORITE:
                yield from self._manager.start(
                    session=session,
                    message=message,
                    state=UserState.FAVORITE_LIST,
                )

            case MenuToken.HELP:
                yield ResponseFactory.menu_help()
                yield from self.start(session, message)
