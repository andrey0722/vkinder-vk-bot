"""This module shows search results to user and handles user commands."""

from collections.abc import Iterator
from typing import override

from vkinder.controller.vk_service import VkServiceError
from vkinder.model import ModelError
from vkinder.shared_types import Favorite
from vkinder.shared_types import InputMessage
from vkinder.shared_types import MenuToken
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory

from ..db import DatabaseSession
from .state import State


class SearchingState(State):
    """Shows search results to user and handles user commands."""

    @override
    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        with session.begin():
            user = message.user
        self._logger.info('Starting for user %d', user.id)
        try:
            profile = self.vk.search_user_by_parameters(user.id)
        except VkServiceError:
            yield ResponseFactory.search_error()
            yield from self._manager.start_main_menu(session, message)
            return

        if profile:
            profile_id = profile.id
            self._logger.info('Found profile %d', profile_id)

            # Save profile id to be able to add it to favorite list
            try:
                with session.begin():
                    user.last_found_id = profile_id
                    session.update_user(user)
            except ModelError:
                self._logger.warning('Failed to save last found profile')
            yield ResponseFactory.search_result(profile)
            yield from self.attach_profile_photos(profile.id)
        else:
            yield ResponseFactory.search_failed()
            yield from self._manager.start_main_menu(session, message)

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        with session.begin():
            user = message.user
        text = message.text
        self._logger.info('User %d selected in search menu: %r', user.id, text)

        if not self.is_command_accepted(message):
            yield from self.unknown_command(session, message)
            return

        # Match user selection in search menu
        match text:
            case MenuToken.NEXT:
                yield from self.start(session, message)

            case MenuToken.ADD_FAVORITE:
                yield from self._add_favorite(session, message)

            case MenuToken.GO_BACK:
                yield from self._manager.start_main_menu(session, message)

            case MenuToken.HELP:
                yield ResponseFactory.menu_help()

    def _add_favorite(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Internal helper to add last found profile to favorite list.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        user = message.user
        user_id = user.id
        profile_id = user.last_found_id
        if profile_id is not None:
            try:
                with session.begin():
                    if not session.favorite_exists(user, profile_id):
                        session.add_favorite(Favorite(user, profile_id))
            except ModelError:
                self._logger.error(
                    'Failed to add favorite for user %d',
                    user_id,
                )
            else:
                yield ResponseFactory.added_to_favorite(allow_squash=False)
                return
        else:
            self._logger.error('No saved last found for user %d', user_id)

        yield ResponseFactory.add_to_favorite_failed(allow_squash=False)
