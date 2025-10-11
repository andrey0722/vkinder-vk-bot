"""This module controls state transition for users."""

from typing import TYPE_CHECKING

from ..model.db import DatabaseSession
from ..model.types import User
from ..model.types import UserState
from ..view import OutputMessage
from .state import InputMessage
from .vk_service import VkService

if TYPE_CHECKING:
    from .state import State


class StateManager:
    """Controls controller state transition for users."""

    def __init__(self, vk: VkService) -> None:
        """Initialize state manager object."""
        self._vk = vk
        self._states: dict[UserState, State] = {
        }

    @property
    def vk(self) -> VkService:
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
    ) -> OutputMessage:
        """Start a new state for user and respond to them.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            state (UserState): New user state.

        Returns:
            OutputMessage: Bot response to the user.
        """
        self._update_user_state(session, message.user, state)
        return self._states[state].start(session, message)

    def start_main_menu(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> OutputMessage:
        """Convenience method to start main menu state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            OutputMessage: Bot response to the user.
        """
        return self.start(session, message, UserState.MAIN_MENU)

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
        user.state = state
        with session.begin():
            session.update_user(user)
