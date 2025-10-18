"""This module shows user's favorite list and handles user commands."""

from collections.abc import Iterator
from typing import override

from vkinder.model import ModelError
from vkinder.model.db import DatabaseSession
from vkinder.model.types import FavoriteListProgress
from vkinder.shared_types import InputMessage
from vkinder.shared_types import MenuToken
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory

from .profile_provider import ProfileProviderError
from .state import State


class FavoriteListState(State):
    """Shows user's favorite list and handles user commands."""

    @override
    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        with session.begin():
            user = message.user
        self._logger.info('Starting for user %d', user.id)
        yield from self._show(session, message)

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        with session.begin():
            user = message.user
        text = message.text
        self._logger.info(
            'User %d selected in favorite list menu: %r',
            user.id,
            text,
        )

        if not self.is_command_accepted(message):
            yield from self.unknown_command(session, message)
            return

        try:
            with session.begin():
                progress = session.get_favorite_list_progress(user)
        except ModelError:
            progress = None
        if not progress:
            yield from self.start(session, message)
            return

        index = progress.index

        # Match user selection in favorite list menu
        match text:
            case MenuToken.PREV:
                yield from self._show(session, message, index - 1)

            case MenuToken.NEXT:
                yield from self._show(session, message, index + 1)

            case MenuToken.DELETE_FAVORITE:
                yield from self._delete(session, message, progress)

            case MenuToken.GO_BACK:
                yield from self._manager.start_main_menu(session, message)

            case MenuToken.HELP:
                yield ResponseFactory.menu_help()

    def _delete(
        self,
        session: DatabaseSession,
        message: InputMessage,
        progress: FavoriteListProgress,
    ) -> Iterator[Response]:
        """Internal helper to delete favorite records for user.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            progress (FavoriteListProgress): Favorite list progress object.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        try:
            with session.begin():
                session.delete_favorite(message.user, progress.profile_id)
        except ModelError:
            self._logger.error('Failed to delete favorite record')
            yield ResponseFactory.favorite_list_failed()
            yield from self._manager.start_main_menu(session, message)
        else:
            yield from self._show(session, message, progress.index)

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
        profile = self.provider.get_user_profile(profile_id)

        # Save progress in this mode
        with session.begin():
            progress = FavoriteListProgress(
                user=user,
                index=index,
                profile_id=profile_id,
            )
            session.add_favorite_list_progress(progress)

        yield ResponseFactory.favorite_result(profile, index + 1, count)
        yield from self.attach_profile_photos(profile_id)
