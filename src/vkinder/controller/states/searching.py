"""This module shows search results to user and handles user commands."""

from collections.abc import Iterator
from typing import override

from vkinder.controller.vk_service import VkServiceError
from vkinder.model import DatabaseSession
from vkinder.shared_types import InputMessage
from vkinder.shared_types import OutputMessage
from vkinder.view import Message
from vkinder.view import SearchMenu

from .state import State


class SearchingState(State):
    """Shows search results to user and handles user commands."""

    @override
    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[OutputMessage]:
        user = message.user
        self._logger.info('Starting for user %d', user.id)
        try:
            profile = self.vk.search_user_by_parameters(user.id)
        except VkServiceError:
            yield Message.search_error(user)
            yield from self._manager.start_main_menu(session, message)
            return

        if profile:
            yield Message.search_result(user, profile)
        else:
            yield Message.search_failed(user)
            yield from self._manager.start_main_menu(session, message)

    @override
    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[OutputMessage]:
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
                yield Message.unknown_command(user)
