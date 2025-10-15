"""This module shows search results to user and handles user commands."""

from collections.abc import Iterator
from typing import override

from vkinder.controller.vk_service import VkServiceError
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory
from vkinder.shared_types import SearchMenu

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
        user = message.user
        self._logger.info('Starting for user %d', user.id)
        try:
            profile = self.vk.search_user_by_parameters(user.id)
        except VkServiceError:
            yield ResponseFactory.search_error()
            yield from self._manager.start_main_menu(session, message)
            return

        if profile:
            yield ResponseFactory.search_result(profile)
            try:
                photos = self.vk.get_user_photos(
                    profile.id,
                    sort_by_likes=True,
                    limit=3,
                )
            except VkServiceError:
                self._logger.warning('Failed to fetch profile photos')
                yield ResponseFactory.photo_failed()
            else:
                yield ResponseFactory.photo_urls(photos)
        else:
            yield ResponseFactory.search_failed()
            yield from self._manager.start_main_menu(session, message)

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        user = message.user
        text = message.text
        self._logger.info('User %d selected in search menu: %s', user.id, text)

        # Match user selection in search menu
        match text:
            case SearchMenu.NEXT:
                yield from self.start(session, message)

            case SearchMenu.ADD_FAVORITE:
                raise NotImplementedError

            case SearchMenu.GO_BACK:
                yield from self._manager.start_main_menu(session, message)

            case _:
                self._logger.warning('Unknown search menu option: %s', text)
                yield ResponseFactory.unknown_command()
