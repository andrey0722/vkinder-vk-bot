"""This module controls state transition for users."""

from collections.abc import Iterator
from typing import TYPE_CHECKING

from vkinder.model import DatabaseSession
from vkinder.model import User
from vkinder.model import UserState
from vkinder.shared_types import InputMessage
from vkinder.shared_types import OutputMessage

from .main_menu import MainMenuState
from .new_user import NewUserState
from .searching import SearchingState

if TYPE_CHECKING:
    from vkinder.controller import VkService

    from .state import State


class StateManager:
    """Controls controller state transition for users."""

    def __init__(self, vk: 'VkService') -> None:
        """Initialize state manager object."""
        self._vk = vk
        self._states: dict[UserState, State] = {
            UserState.NEW_USER: NewUserState(self),
            UserState.MAIN_MENU: MainMenuState(self),
            UserState.SEARCHING: SearchingState(self),
        }

    @property
    def vk(self) -> 'VkService':
        """Returns VK service object for the controller.

        Returns:
            VkService: VK service object.
        """
        return self._vk

    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
        state: UserState,
    ) -> Iterator[OutputMessage]:
        """Start a new state for user and respond to them.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            state (UserState): New user state.

        Returns:
            Iterator[OutputMessage]: Bot responses to the user.
        """
        self._update_user_state(session, message.user, state)
        yield from self._states[state].start(session, message)

    def start_main_menu(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[OutputMessage]:
        """Convenience method to start main menu state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[OutputMessage]: Bot responses to the user.
        """
        yield from self.start(session, message, UserState.MAIN_MENU)

    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[OutputMessage]:
        """Respond to a user depending on user state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[OutputMessage]: Bot responses to the user.
        """
        state = message.user.state
        yield from self._states[state].respond(session, message)

    def _update_user_state(
        self,
        session: DatabaseSession,
        user: User,
        state: UserState,
    ) -> None:
        """Internal helper to modify user state and reflect it in the DB.

        Args:
            session (DatabaseSession): Session object.
            user (User): A bot user.
            state (UserState): New user state.
        """
        with session.begin():
            user.state = state
            session.update_user(user)
