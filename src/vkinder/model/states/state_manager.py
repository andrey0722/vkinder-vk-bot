"""This module controls state transition for users."""

from collections.abc import Iterator
from typing import TYPE_CHECKING

from vkinder.model.db import DatabaseSession
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import UserState

from .blacklist import BlacklistState
from .favorite_list import FavoriteListState
from .main_menu import MainMenuState
from .new_user import NewUserState
from .profile_provider import ProfileProvider
from .searching import SearchingState

if TYPE_CHECKING:
    from .state import State


class StateManager:
    """Controls controller state transition for users."""

    def __init__(self, profile_provider: ProfileProvider) -> None:
        """Initialize state manager object.

        Args:
            profile_provider (ProfileProvider): Profile provider object.
        """
        self._profile_provider = profile_provider
        self._states: dict[UserState, State] = {
            UserState.NEW_USER: NewUserState(self),
            UserState.MAIN_MENU: MainMenuState(self),
            UserState.SEARCHING: SearchingState(self),
            UserState.FAVORITE_LIST: FavoriteListState(self),
            UserState.BLACKLIST: BlacklistState(self),
        }

    @property
    def profile_provider(self) -> ProfileProvider:
        """Returns profile provider object.

        Returns:
            ProfileProvider: Profile provider object.
        """
        return self._profile_provider

    def get_state(self, user_state: UserState) -> 'State':
        """Retrieves state object for given user state.

        Args:
            user_state (UserState): User state value.

        Returns:
            State: State object.
        """
        try:
            return self._states[user_state]
        except KeyError as e:
            raise NotImplementedError from e

    def start(
        self,
        session: DatabaseSession,
        message: InputMessage,
        user_state: UserState,
    ) -> Iterator[Response]:
        """Start a new state for user and respond to them.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            user_state (UserState): New user state.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        self._update_user_state(session, message, user_state)
        state = self.get_state(user_state)
        yield from state.start(session, message)

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

    def start_search(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Convenience method to start search state.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        yield from self.start(session, message, UserState.SEARCHING)

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
        user_state = message.user.state
        state = self.get_state(user_state)
        yield from state.respond(session, message)

    def _update_user_state(
        self,
        session: DatabaseSession,
        message: InputMessage,
        state: UserState,
    ) -> None:
        """Internal helper to modify user state and reflect it in the DB.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            state (UserState): New user state.
        """
        with session.begin():
            user = message.user
            message.progress.last_state = user.state
            user.state = state
