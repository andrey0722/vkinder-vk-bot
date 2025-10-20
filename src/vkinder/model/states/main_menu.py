"""This module shows main menu to user and handles user selection in it."""

from collections.abc import Iterator
from typing import ClassVar, override

from vkinder.model.db import DatabaseSession
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Keyboard
from vkinder.shared_types import MenuToken
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory
from vkinder.shared_types import TextButton

from ..types import UserState
from .state import State


class MainMenuState(State):
    """Shows bot main menu to user and handles user selection in that menu."""

    KEYBOARD: ClassVar[Keyboard] = Keyboard(
        one_time=False,
        button_rows=[
            [
                TextButton(MenuToken.SEARCH, ButtonColor.PRIMARY),
                TextButton(MenuToken.PROFILE),
            ],
            [
                TextButton(MenuToken.FAVORITE),
                TextButton(MenuToken.HELP),
            ],
        ],
    )
    """Bot keyboard for this user state."""

    MENU_OPTIONS: ClassVar[tuple[MenuToken, ...]] = (
        MenuToken.SEARCH,
        MenuToken.PROFILE,
        MenuToken.FAVORITE,
        MenuToken.HELP,
    )
    """Menu commands accepted for this user state."""

    @override
    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        with session.begin():
            user = message.user
        self._logger.info('Starting for user %d', user.id)
        yield self.show_keyboard(user)
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
        yield self.show_keyboard(user)

        if not self.is_command_accepted(message):
            yield from self.unknown_command(session, message)
            return

        # Match user selection in main menu
        match text:
            case MenuToken.SEARCH:
                yield from self._manager.start_search(session, message)

            case MenuToken.PROFILE:
                # Check user authorization
                with session.begin():
                    auth_data = session.get_auth_data(user.id)
                    token = auth_data and auth_data.access_token
                yield ResponseFactory.your_profile(user)
                yield from self.attach_profile_photos(user.id, token)
                yield from self.start(session, message)

            case MenuToken.FAVORITE:
                yield from self._manager.start(
                    session=session,
                    message=message,
                    user_state=UserState.FAVORITE_LIST,
                )

            case MenuToken.HELP:
                yield ResponseFactory.menu_help(self.MENU_OPTIONS)
                yield from self.start(session, message)
