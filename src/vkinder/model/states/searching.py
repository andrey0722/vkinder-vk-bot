"""This module shows search results to user and handles user commands."""

from collections.abc import Iterator
import copy
import random
from typing import ClassVar, Final, override

from vkinder.model import ModelError
from vkinder.model.db import DatabaseSession
from vkinder.shared_types import Blacklist
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import Favorite
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Keyboard
from vkinder.shared_types import MenuToken
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory
from vkinder.shared_types import Sex
from vkinder.shared_types import TextButton
from vkinder.shared_types import User
from vkinder.shared_types import UserSearchQuery
from vkinder.shared_types import UserSortOrder

from .profile_provider import ProfileProviderError
from .profile_provider import ProfileProviderTokenError
from .state import State

SEARCH_AGE_MAX_GAP = 1
"""Maximum age gap to use in profile search."""

SEARCH_SEX_MAP: Final[dict[Sex, Sex]] = {
    Sex.FEMALE: Sex.MALE,
    Sex.MALE: Sex.FEMALE,
}
"""Mapping for sex selection in search query."""

FILTER_BY_SEX: bool = True
"""Filer users by sex value. If `False` then no filtering."""

FILTER_BY_CITY: bool = True
"""Filer users by sex value. If `False` then no filtering."""

FILTER_BY_AGE: bool = True
"""Filer users by age value. If `False` then no filtering."""

FILTER_ONLINE: bool | None = True
"""Filer users by online property value. If `None` then no filtering."""

FILTER_HAS_PHOTO: bool | None = True
"""Filer users by photo availability. If `None` then no filtering."""


class SearchingState(State):
    """Shows search results to user and handles user commands."""

    KEYBOARD: ClassVar[Keyboard] = Keyboard(
        one_time=False,
        button_rows=[
            [
                TextButton(MenuToken.NEXT, ButtonColor.PRIMARY),
            ],
            [
                TextButton(MenuToken.ADD_FAVORITE),
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
        MenuToken.NEXT,
        MenuToken.ADD_FAVORITE,
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
        with session.begin():
            user = message.user
            user_id = user.id
        self._logger.info('Starting for user %d', user_id)
        yield self.show_keyboard(message)

        # Check user authorization
        token = self.get_user_token(session, user_id)
        if token is None:
            # Request authorization from user
            yield from self._manager.start_auth(session, message)
            return

        # Try to calculate user search criteria
        query = self._get_search_query(user)
        if not isinstance(query, UserSearchQuery):
            yield query
            yield from self._manager.start_main_menu(session, message)
            return

        # Everything is OK, try to search
        try:
            yield from self._search(session, message, token, query)
        except ProfileProviderTokenError:
            # Problem with the token
            if self.get_user_token(session, user_id) is None:
                yield from self._manager.start_auth(session, message)
            else:
                yield ResponseFactory.search_error()
            return
        except ProfileProviderError:
            yield ResponseFactory.search_error()
            yield from self._manager.start_main_menu(session, message)
            return

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
        yield self.show_keyboard(message)

        if not self.is_command_accepted(message):
            yield from self.unknown_command(session, message)
            return

        # Match user selection in search menu
        match text:
            case MenuToken.NEXT:
                yield from self.start(session, message)

            case MenuToken.ADD_FAVORITE:
                yield from self._add_favorite(session, message)
                yield ResponseFactory.select_menu()

            case MenuToken.ADD_BLACKLIST:
                yield from self._add_blacklist(session, message)
                yield ResponseFactory.select_menu()

            case MenuToken.GO_BACK:
                yield from self._manager.start_main_menu(session, message)

            case MenuToken.HELP:
                yield ResponseFactory.menu_help(self.MENU_OPTIONS)

    def _get_search_query(self, user: User) -> UserSearchQuery | Response:
        """Internal helper to calculate query parameters for given user.

        Args:
            user (User): User object.

        Returns:
            UserSearchQuery | Response: User search query object or error.
        """
        if FILTER_BY_SEX:
            try:
                sex = SEARCH_SEX_MAP[user.sex]
            except KeyError:
                self._logger.error('User sex is missing')
                return ResponseFactory.user_sex_missing()
        else:
            sex = None

        if FILTER_BY_CITY:
            city_id = user.city_id
            if city_id is None:
                self._logger.error('User city is missing')
                return ResponseFactory.user_city_missing()
        else:
            city_id = None

        if FILTER_BY_AGE:
            age = user.age
            if age is None:
                self._logger.error('User birthday is missing')
                return ResponseFactory.user_birthday_missing()
            self._logger.debug('User age is %d', age)
            age_min = max(age - SEARCH_AGE_MAX_GAP, 0)
            age_max = age + SEARCH_AGE_MAX_GAP
        else:
            age_min = age_max = None

        return UserSearchQuery(
            sex=sex,
            city_id=city_id,
            online=FILTER_ONLINE,
            has_photo=FILTER_HAS_PHOTO,
            age_min=age_min,
            age_max=age_max,
        )

    def _search(
        self,
        session: DatabaseSession,
        message: InputMessage,
        token: str,
        query: UserSearchQuery,
    ) -> Iterator[Response]:
        """Performs user search and shows result to user.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.
            token (str): User access token.
            query (UserSearchQuery): User search query object.

        Yields:
            Iterator[Response]: Bot responses to the user.
        """
        user_id = message.user.id
        profiles = self._get_search_results(user_id, token, query)

        # Ensure only unique profiles are present
        old_count = len(profiles)
        profiles = list(set(profiles))
        self._logger.info(
            'Extracted unique %d (from total %d) profiles for user %d',
            len(profiles),
            old_count,
            user_id,
        )

        # Apply blacklist
        with session.begin():
            old_count = len(profiles)
            profiles = session.filter_non_blacklisted(user_id, profiles)

        self._logger.info(
            'Filtered %d (from %d) profiles for user %d',
            len(profiles),
            old_count,
            user_id,
        )

        if profiles:
            profile_id = random.choice(profiles)
            self._logger.info(
                'Selected profile %d for user %d',
                profile_id,
                user_id,
            )

            profile = self.profile_provider.get_user_profile(profile_id)

            # Save profile id to be able to add it to favorite list
            try:
                with session.begin():
                    progress = message.progress
                    progress.last_found_id = profile_id
            except ModelError:
                self._logger.warning('Failed to save last found profile')
            yield ResponseFactory.search_result(profile)
            yield from self.attach_profile_photos(profile.id, token)
        else:
            self._logger.warning('No profiles found for user %d', user_id)
            yield ResponseFactory.search_failed()
            yield from self._manager.start_main_menu(session, message)

    def _get_search_results(
        self,
        user_id: int,
        token: str,
        query: UserSearchQuery,
    ) -> list[int]:
        """Performs an actual search query and returns search results.

        Args:
            user_id (int): Bot user id.
            token (str): User access token.
            query (UserSearchQuery): User search query object.

        Returns:
            list[int]: Profile ids found.
        """
        # Perform several search attempts with different sorting
        # and merge results to overcome search limit.
        query = copy.deepcopy(query)
        profiles: list[int] = []

        # Find most relevant people
        query.sort = UserSortOrder.RELEVANT
        profiles.extend(self.profile_provider.search_users(query, token))
        self._logger.debug('%d profiles for user %d', len(profiles), user_id)

        # Find newest accounts that satisfy search query
        query.sort = UserSortOrder.NEWEST
        profiles.extend(self.profile_provider.search_users(query, token))
        self._logger.debug('%d profiles for user %d', len(profiles), user_id)

        return profiles

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
        profile_id = message.progress.last_found_id
        if profile_id is not None:
            try:
                with session.begin():
                    session.delete_blacklist(user, profile_id)
                    if not session.favorite_exists(user_id, profile_id):
                        session.add_favorite(Favorite(user, profile_id))
            except ModelError:
                self._logger.error(
                    'Failed to add favorite for user %d',
                    user_id,
                )
            else:
                yield ResponseFactory.added_to_favorite()
                return
        else:
            self._logger.error('No saved last found for user %d', user_id)

        yield ResponseFactory.add_to_favorite_failed()

    def _add_blacklist(
        self,
        session: DatabaseSession,
        message: InputMessage,
    ) -> Iterator[Response]:
        """Internal helper to add last found profile to blacklist.

        Args:
            session (DatabaseSession): Session object.
            message (InputMessage): A message from user.

        Returns:
            Iterator[Response]: Bot responses to the user.
        """
        user = message.user
        user_id = user.id
        profile_id = message.progress.last_found_id
        if profile_id is not None:
            try:
                with session.begin():
                    session.delete_favorite(user, profile_id)
                    if not session.blacklist_exists(user_id, profile_id):
                        session.add_blacklist(Blacklist(user, profile_id))
            except ModelError:
                self._logger.error(
                    'Failed to add blacklist for user %d',
                    user_id,
                )
            else:
                yield ResponseFactory.added_to_blacklist()
                return
        else:
            self._logger.error('No saved last found for user %d', user_id)

        yield ResponseFactory.add_to_blacklist_failed()
