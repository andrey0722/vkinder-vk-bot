"""This module greets new users and shows bot main menu to them."""

from collections.abc import Iterator
from typing import override

from vkinder.model import DatabaseSession
from vkinder.shared_types import InputMessage
from vkinder.shared_types import OutputMessage
from vkinder.view import Message

from .main_menu import MainMenuState


class NewUserState(MainMenuState):
    """Greets new users and shows bot main menu to them."""

    @override
    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[OutputMessage]:
        user = message.user
        self._logger.info('Starting for user %d', user.id)
        yield Message.greet_new_user(user)
        yield from self._manager.start_main_menu(session, message)

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[OutputMessage]:
        yield from self.start(session, message)
