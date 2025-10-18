"""This module shows search results to user and handles user commands."""

from collections.abc import Iterator
from typing import Final, override

from vkinder.model import ModelError
from vkinder.shared_types import Favorite
from vkinder.shared_types import InputMessage
from vkinder.shared_types import MenuToken
from vkinder.shared_types import Response
from vkinder.shared_types import ResponseFactory
from vkinder.shared_types import Sex
from vkinder.shared_types import User
from vkinder.shared_types import UserSearchQuery

from ..db import DatabaseSession
from .profile_provider import ProfileProviderError
from .state import State

SEARCH_AGE_MAX_GAP = 1
"""Maximum age gap to use in profile search."""


class SearchCriteriaError(ModelError):
    """Error when computing user search criteria."""


class UserSexNotKnownError(SearchCriteriaError):
    """User has not specified their sex in the user profile."""


class UserCityNotKnownError(SearchCriteriaError):
    """User has not specified their city in the user profile."""


class UserBirthdayNotKnownError(SearchCriteriaError):
    """User has not specified their birthday in the user profile."""


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

        # Try to calculate user search criteria
        try:
            query = self._get_search_query(user)
        except SearchCriteriaError as e:
            self._logger.error('Failed to create search criteria')
            if isinstance(e, UserSexNotKnownError):
                yield ResponseFactory.user_sex_missing()
            elif isinstance(e, UserCityNotKnownError):
                yield ResponseFactory.user_city_missing()
            elif isinstance(e, UserBirthdayNotKnownError):
                yield ResponseFactory.user_birthday_missing()
            else:
                raise NotImplementedError from e
            yield from self._manager.start_main_menu(session, message)
            return

        # Everything is OK, try to search
        try:
            profile = self.provider.search_user(query)
        except ProfileProviderError:
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

    _SEARCH_SEX_MAP: Final[dict[Sex, Sex]] = {
        Sex.FEMALE: Sex.MALE,
        Sex.MALE: Sex.FEMALE,
    }
    """Mapping for sex selection in search query."""

    def _get_search_query(self, user: User) -> UserSearchQuery:
        """Internal helper to calculate query parameters for given user.

        Args:
            user (User): User object.

        Raises:
            UserSexNotKnownError: User sex is not known.
            UserCityNotKnownError: User city is not known.

        Returns:
            UserSearchQuery: User search query object.
        """
        try:
            sex = self._SEARCH_SEX_MAP[user.sex]
        except KeyError as e:
            self._logger.error('User sex is missing')
            raise UserSexNotKnownError from e

        city_id = user.city_id
        if city_id is None:
            self._logger.error('User city is missing')
            raise UserCityNotKnownError

        age = user.age
        if age is None:
            self._logger.error('User birthday is missing')
            raise UserBirthdayNotKnownError
        self._logger.debug('User age is %d', age)

        return UserSearchQuery(
            sex=sex,
            city_id=city_id,
            online=True,
            has_photo=True,
            age_min=max(age - SEARCH_AGE_MAX_GAP, 0),
            age_max=age + SEARCH_AGE_MAX_GAP,
        )

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
