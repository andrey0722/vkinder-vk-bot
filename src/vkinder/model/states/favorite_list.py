"""This module shows user's favorite list and handles user commands."""

from collections.abc import Iterator
from typing import ClassVar, override

from vkinder.model import ModelError
from vkinder.model.db import DatabaseSession
from vkinder.shared_types import Blacklist
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Keyboard
from vkinder.shared_types import MenuToken
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory
from vkinder.shared_types import TextButton

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
                TextButton(MenuToken.ADD_BLACKLIST, ButtonColor.NEGATIVE),
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
        MenuToken.ADD_BLACKLIST,
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
        self._logger.info('Starting for user %d', message.user.id)
        yield self.show_keyboard()
        yield from self._show(session, message, 0)

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        with session.begin():
            user = message.user
            progress = message.progress
            index = progress.last_favorite_index

        text = message.text
        self._logger.info(
            'User %d selected in favorite list menu: %r',
            user.id,
            text,
        )
        yield self.show_keyboard()

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
                yield from self._delete_favorite(session, message)

            case MenuToken.ADD_BLACKLIST:
                yield from self._add_blacklist(session, message)

            case MenuToken.GO_BACK:
                yield from self._manager.start_main_menu(session, message)

            case MenuToken.HELP:
                yield ResponseFactory.menu_help(self.MENU_OPTIONS)

    def _delete_favorite(
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
                progress = message.progress
                profile_id = progress.last_favorite_id
                index = progress.last_favorite_index
                user = message.user
                session.delete_favorite(user, profile_id)
        except ModelError:
            self._logger.error('Failed to delete favorite record')
            yield ResponseFactory.favorite_list_failed()
            yield from self._manager.start_main_menu(session, message)
        else:
            yield from self._show(session, message, index)

    def _add_blacklist(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Internal helper to add blacklist records for user.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        try:
            with session.begin():
                progress = message.progress
                profile_id = progress.last_favorite_id
                index = progress.last_blacklist_index
                user = message.user
                session.delete_favorite(user, profile_id)
                session.add_blacklist(Blacklist(user, profile_id))
        except ModelError:
            self._logger.error('Failed to add blacklist record')
            yield ResponseFactory.add_to_blacklist_failed()
        else:
            yield from self._show(session, message, index)

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
            count = session.get_favorite_count(user.id)
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
            progress.last_favorite_index = index
            progress.last_favorite_id = profile_id

        yield ResponseFactory.favorite_result(profile, index + 1, count)
        yield from self.attach_profile_photos(profile_id)
