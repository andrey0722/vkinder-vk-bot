"""This module shows user's favorite list and handles user commands."""

from collections.abc import Iterator
from typing import ClassVar, override

from vkinder.model import ModelError
from vkinder.model.db import DatabaseSession
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Keyboard
from vkinder.shared_types import MenuToken
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory
from vkinder.shared_types import TextButton
from vkinder.shared_types import UserState

from .profile_provider import ProfileProviderError
from .state import State


class FavoriteListState(State):
    """Shows user's favorite list and handles user commands."""

    KEYBOARD: ClassVar[Keyboard] = Keyboard(
        one_time=False,
        button_rows=[
            [
                TextButton(MenuToken.PREV),
                TextButton(MenuToken.NEXT),
            ],
            [
                TextButton(MenuToken.DELETE_FAVORITE, ButtonColor.NEGATIVE),
            ],
            [
                TextButton(MenuToken.GO_BACK),
                TextButton(MenuToken.HELP),
            ],
        ],
    )
    """Bot keyboard for this user state."""

    MENU_OPTIONS: ClassVar[tuple[MenuToken, ...]] = (
        MenuToken.PREV,
        MenuToken.NEXT,
        MenuToken.DELETE_FAVORITE,
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
            progress = message.progress
            if progress.last_state == UserState.AUTH:
                # Restore state from before auth
                index = progress.last_fav_index
            else:
                index = 0

        self._logger.info('Starting for user %d', user.id)
        yield self.show_keyboard(user)
        yield from self._show(session, message, index)

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        with session.begin():
            user = message.user
            progress = message.progress
            index = progress.last_fav_index

        text = message.text
        self._logger.info(
            'User %d selected in favorite list menu: %r',
            user.id,
            text,
        )
        yield self.show_keyboard(user)

        if not self.is_command_accepted(message):
            yield from self.unknown_command(session, message)
            return

        # Match user selection in favorite list menu
        match text:
            case MenuToken.PREV:
                yield from self._show(session, message, index - 1)

            case MenuToken.NEXT:
                yield from self._show(session, message, index + 1)

            case MenuToken.DELETE_FAVORITE:
                yield from self._delete(session, message)

            case MenuToken.GO_BACK:
                yield from self._manager.start_main_menu(session, message)

            case MenuToken.HELP:
                yield ResponseFactory.menu_help(self.MENU_OPTIONS)

    def _delete(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Internal helper to delete favorite records for user.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        progress = message.progress
        try:
            with session.begin():
                session.delete_favorite(message.user, progress.last_fav_id)
        except ModelError:
            self._logger.error('Failed to delete favorite record')
            yield ResponseFactory.favorite_list_failed()
            yield from self._manager.start_main_menu(session, message)
        else:
            yield from self._show(session, message, progress.last_fav_index)

    def _show(
        self,
        session: DatabaseSession,
        message: InputMessage,
        index: int = 0,
    ) -> Iterator[Response]:
        """Internal helper that shows a profile from user's favorite list.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            index (int, optional): Profile positional index. Defaults to 0.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        try:
            yield from self._show_internal(session, message, index)
        except (ModelError, ProfileProviderError):
            self._logger.error('Failed to extract favorite profile')
            yield ResponseFactory.favorite_list_failed()
            yield from self._manager.start_main_menu(session, message)


    def _show_internal(
        self,
        session: DatabaseSession,
        message: InputMessage,
        index: int,
    ) -> Iterator[Response]:
        """Internal helper that implements `_show()` method logic.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            index (int, optional): Profile positional index. Defaults to 0.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        user = message.user

        with session.begin():
            count = session.get_favorite_count(user)
        if not count:
            yield ResponseFactory.favorite_list_empty()
            yield from self._manager.start_main_menu(session, message)
            return

        # Normalize profile index
        index = index % count

        with session.begin():
            record = session.get_favorite_index(user, index)
        if not record:
            yield ResponseFactory.favorite_list_empty()
            yield from self._manager.start_main_menu(session, message)
            return

        profile_id = record.profile_id
        profile = self.profile_provider.get_user_profile(profile_id)

        # Save progress in this mode
        with session.begin():
            progress = message.progress
            progress.last_fav_index = index
            progress.last_fav_id = profile_id

        # Check user authorization
        token = self.get_user_token(session, user.id)
        if token is None:
            # Request authorization from user
            yield from self._manager.start_auth(session, message)
            return

        yield ResponseFactory.favorite_result(profile, index + 1, count)
        yield from self.attach_profile_photos(profile_id, token)
