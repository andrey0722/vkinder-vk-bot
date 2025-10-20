"""This module performs user authorization procedure."""

from collections.abc import Iterator
from typing import ClassVar, override

from vkinder.model.db import DatabaseSession
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Keyboard
from vkinder.shared_types import MenuToken
from vkinder.shared_types import OpenLinkButton
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory
from vkinder.shared_types import TextButton

from .state import State


class AuthState(State):
    """Performs user authorization procedure."""

    MENU_OPTIONS: ClassVar[tuple[MenuToken, ...]] = (
        MenuToken.AUTH_BEGIN,
        MenuToken.AUTH_FINISHED,
        MenuToken.GO_BACK,
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
        yield self.show_keyboard(message)
        yield ResponseFactory.auth_required()
        yield ResponseFactory.select_menu()

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        with session.begin():
            user = message.user
            target = message.progress.last_state
        text = message.text
        self._logger.info('User %d selected in main menu: %r', user.id, text)
        yield self.show_keyboard(message)

        if not self.is_command_accepted(message):
            yield from self.unknown_command(session, message)
            return

        # Check authorization status
        token = self.get_user_token(session, user.id)

        # Match user selection in main menu
        match text:
            case MenuToken.AUTH_FINISHED:
                if token is None:
                    # Not authorized yet
                    yield ResponseFactory.auth_not_completed()
                    yield from self.start(session, message)
                else:
                    # Auth finished, resume to the last state
                    yield from self._manager.start(session, message, target)

            case MenuToken.GO_BACK:
                yield from self._manager.start_main_menu(session, message)

            case MenuToken.HELP:
                yield ResponseFactory.menu_help(self.MENU_OPTIONS)
                yield from self.start(session, message)

    @override
    def create_keyboard(self, message: InputMessage) -> Keyboard:
        access_rights = self.profile_provider.get_user_access_rights()
        auth_link = self.auth_provider.create_auth_link(
            user_id=message.user.id,
            access_rights=access_rights,
            chat_id=message.chat_id,
        )
        self._logger.info('Got auth link: %s', auth_link)
        return self._create_keyboard(auth_link)

    def _create_keyboard(self, auth_link: str) -> Keyboard:
        """Internal helper that creates keyboard with auth link.

        Args:
            auth_link (str): User auth link.

        Returns:
            Keyboard: Bot keyboard object.
        """
        return Keyboard(
            one_time=False,
            button_rows=[
                [
                    OpenLinkButton(MenuToken.AUTH_BEGIN, auth_link),
                    TextButton(MenuToken.AUTH_FINISHED, ButtonColor.POSITIVE),
                ],
                [
                    TextButton(MenuToken.GO_BACK),
                    TextButton(MenuToken.HELP),
                ],
            ],
        )
