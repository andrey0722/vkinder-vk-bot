"""This module controls state transition for users."""

from collections.abc import Iterator
from typing import TYPE_CHECKING

from vkinder.shared_types import InputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import User
from vkinder.shared_types import UserState

from ..db import DatabaseSession
from .favorite_list import FavoriteListState
from .main_menu import MainMenuState
from .new_user import NewUserState
from .profile_provider import ProfileProvider
from .searching import SearchingState

if TYPE_CHECKING:
    from .state import State


class StateManager:
    """Controls controller state transition for users."""

    def __init__(self, provider: ProfileProvider) -> None:
        """Initialize state manager object."""
        self._provider = provider
        self._states: dict[UserState, State] = {
            UserState.NEW_USER: NewUserState(self),
            UserState.MAIN_MENU: MainMenuState(self),
            UserState.SEARCHING: SearchingState(self),
            UserState.FAVORITE_LIST: FavoriteListState(self),
        }

    @property
    def provider(self) -> ProfileProvider:
        """Returns profile provider object.

        Returns:
            ProfileProvider: Profile provider object.
        """
        return self._provider

    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
        state: UserState,
    ) -> Iterator[Response]:
        """Start a new state for user and respond to them.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            state (UserState): New user state.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        self._update_user_state(session, message.user, state)
        yield from self._states[state].start(session, message)

    def start_main_menu(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Convenience method to start main menu state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        yield from self.start(session, message, UserState.MAIN_MENU)

    def respond(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Respond to a user depending on user state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
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
