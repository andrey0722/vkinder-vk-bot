"""Implements classes for VK API interaction."""

from collections.abc import Iterator
import datetime
import enum
import random
from typing import Any, Final, Literal, NoReturn, NotRequired, TypedDict, cast

import vk_api
import vk_api.keyboard
from vk_api.longpoll import Event
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll

from vkinder.config import VkConfig
from vkinder.exceptions import VkinderError
from vkinder.log import get_logger
from vkinder.model import ProfileProviderError
from vkinder.model import ProfileProviderTokenError
from vkinder.shared_types import ButtonColor
from vkinder.shared_types import Keyboard
from vkinder.shared_types import Media
from vkinder.shared_types import OpenLinkButton
from vkinder.shared_types import OutputMessage
from vkinder.shared_types import Photo
from vkinder.shared_types import Sex
from vkinder.shared_types import TextButton
from vkinder.shared_types import User
from vkinder.shared_types import UserSearchQuery

type VkObject = dict[str, Any]


class VkHasCount(TypedDict):
    """VK object that contains "count" field."""

    count: int


class VkHasItems[T](VkHasCount):
    """VK object that contains "items" field."""

    items: list[T]


class VkDeactivatedReason(enum.StrEnum):
    """Reason why user profile is deactivated."""

    DELETED = 'deleted'
    BANNED = 'banned'


class VkCity(TypedDict):
    """VK user city descriptor."""

    id: int
    title: str


class VkSex(enum.IntEnum):
    """Sex designator in VK notation."""

    NOT_SPECIFIED = 0
    FEMALE = 1
    MALE = 2


class VkUser(TypedDict):
    """VK user profile descriptor."""

    id: int
    first_name: str
    last_name: str
    deactivated: NotRequired[VkDeactivatedReason]
    is_closed: bool
    can_access_closed: bool
    bdate: NotRequired[str]
    city: NotRequired[VkCity]
    domain: NotRequired[str]
    nickname: NotRequired[str]
    online: NotRequired[int]
    sex: NotRequired[VkSex]


class VkPhotoType(enum.StrEnum):
    """VK photo type designator."""

    SCALED_75 = 's'
    """Scaled image with a maximum side of 75px."""

    SCALED_130 = 'm'
    """Scaled image with a maximum side of 130px."""

    SCALED_604 = 'x'
    """Scaled image with a maximum side of 604px."""

    SCALED_807 = 'y'
    """Scaled image with a maximum side of 807px."""

    SCALED_1080_1024 = 'z'
    """Scaled image with a maximum size of 1080x1024px."""

    SCALED_2560_2048 = 'w'
    """Scaled image with a maximum size of 2560x2048px."""

    CROPPED_130 = 'o'
    """Cropped to ratio 3:2 and scaled image with a maximum side of 130px."""

    CROPPED_200 = 'p'
    """Cropped to ratio 3:2 and scaled image with a maximum side of 200px."""

    CROPPED_320 = 'q'
    """Cropped to ratio 3:2 and scaled image with a maximum side of 320px."""

    CROPPED_510 = 'r'
    """Cropped to ratio 3:2 and scaled image with a maximum side of 510px."""

    ORIGINAL = 'base'
    """Original photo (undocumented)."""


class VkPhotoSource(TypedDict):
    """VK photo source descriptor."""

    url: str
    width: int
    height: int
    type: VkPhotoType


class VkPhoto(TypedDict):
    """VK photo descriptor."""

    id: int
    album_id: int
    owner_id: int
    user_id: int
    text: str
    date: int
    thumb_hash: str
    has_tags: bool
    sizes: list[VkPhotoSource]
    width: NotRequired[int]
    height: NotRequired[int]

    orig_photo: NotRequired[VkPhotoSource]
    """Undocumented convenience field for original photo source."""


class VkPhotoLikes(VkHasCount):
    """VK photo like count descriptor."""

    user_likes: int
    """Number of likes from a photo owner."""


class VkPhotoEx(VkPhoto):
    """VK photo descriptor with extended=1 in API method call."""

    likes: VkPhotoLikes
    comments: VkHasCount
    tags: VkHasCount
    can_comment: int
    reposts: VkHasCount


class VkUsersGetParams(TypedDict):
    """Parameters for 'users.get' API method."""

    user_ids: int | str
    fields: str


type VkUsersGetResult = list[VkUser]
"""VK response object for 'users.get' API method."""


class VkUsersSearchParams(TypedDict):
    """Parameters for 'users.search' API method."""

    count: NotRequired[int]
    offset: NotRequired[int]
    fields: NotRequired[str]
    sex: NotRequired[VkSex]
    city: NotRequired[int]
    online: NotRequired[bool]
    has_photo: NotRequired[bool]
    age_from: NotRequired[int]
    age_to: NotRequired[int]
    access_token: NotRequired[str]


class VkUsersSearchResult(VkHasItems[VkUser]):
    """VK response object for 'users.search' API method."""


class VkPhotosGetParams(TypedDict):
    """Parameters for 'photos.get' API method."""

    owner_id: int
    album_id: int | Literal['profile']
    photo_ids: int | str
    extended: NotRequired[Literal[1, 0]]
    access_token: NotRequired[str]


class VkPhotosGetResult(VkHasItems[VkPhoto]):
    """VK response object for 'photos.get' API method."""


class VkPhotosGetExResult(VkHasItems[VkPhotoEx]):
    """VK response object for 'photos.get' API method with extended=1."""


class VkMessagesSendParams(TypedDict):
    """Parameters for 'messages.send' API method."""

    user_id: int
    message: str
    random_id: int
    keyboard: NotRequired[str]
    attachment: NotRequired[str]


class VkTrackVisitorParams(TypedDict):
    """Parameters for 'stats.trackVisitor' API method."""

    access_token: NotRequired[str]


class VkServiceError(ProfileProviderError, VkinderError):
    """Error when using VK service."""


class VkApiError(VkServiceError):
    """Error when using VK API."""


class VkTokenError(ProfileProviderTokenError, VkApiError):
    """Error occurred because access token is invalid."""


class VkUserNotFoundError(VkServiceError):
    """Failed to get user profile by user id."""

    def __init__(self, user_id: int) -> None:
        """Initialize an exception object.

        Args:
            user_id (int): User id.
        """
        super().__init__(user_id)


class VkService:
    """Implements VK API interactions."""

    def __init__(self, config: VkConfig) -> None:
        """Initialize VK service object.

        Args:
            config (VkConfig): VK service config.
        """
        self._logger = get_logger(self)
        self._vk = self._create_vk(config.vk_community_token)
        self._longpoll = self._create_longpoll()
        self._logger.info('VK service is initialized')

    def get_user_access_rights(self) -> str:
        """Returns required access right set for user account.

        Returns:
            str: Access right set.
        """
        return 'photos'

    def listen(self) -> Iterator[Event]:
        """Retrieves events from VK longpoll server.

        Yields:
            Event: VK longpoll event.
        """
        return self._log_events(self._listen())

    def listen_messages(self) -> Iterator[Event]:
        """Retrieves message events from VK longpoll server.

        Yields:
            Event: VK longpoll message event.
        """
        return self._log_events(filter(self._is_message_event, self._listen()))

    def check_messages(self) -> Iterator[Event]:
        """Retrieves message events from VK longpoll server.

        Returns:
            Iterator[Event]: VK longpoll message events if any.
        """
        return self._log_events(filter(self._is_message_event, self._check()))

    def send(self, message: OutputMessage) -> None:
        """Send a message from bot to user.

        Args:
            message (OutputMessage): Output message.

        Raises:
            VkApiError: Error when using VK API.
        """
        text = message.text
        keyboard = message.keyboard
        user_id = message.user.id
        self._logger.info('Sending to user %d: %s', user_id, text)

        vk_keyboard = _convert_keyboard(keyboard)
        self._logger.info('Keyboard for user %d: %r', user_id, vk_keyboard)

        attachment = _convert_attachment(message.media)
        self._logger.info('Attachment for user %d: %r', user_id, attachment)

        params = VkMessagesSendParams(
            user_id=user_id,
            message=text,
            keyboard=vk_keyboard,
            attachment=attachment,
            random_id=_get_random_id(),
        )

        try:
            self._vk.method('messages.send', params)
        except vk_api.VkApiError as e:
            self._logger.error(
                'Failed to send message to user %d: %s',
                user_id,
                e,
            )
            _reraise(e)

    def validate_access_token(self, access_token: str | None) -> bool:
        """Tests if provided user access token is valid for API calls.

        Args:
            access_token (str | None): User access token.

        Returns:
            bool: `True` if valid, otherwise `False`.
        """
        params = VkTrackVisitorParams()
        if access_token is not None:
            params['access_token'] = access_token
        try:
            self._vk.method('stats.trackVisitor', params)
        except vk_api.exceptions.ApiError as e:
            self._logger.error('User access token error: %s', e)
            return False
        return True

    def get_search_result_size(
        self,
        query: UserSearchQuery,
        access_token: str | None = None,
    ) -> int:
        """Requests number of user profiles in search result for query.

        Args:
            query (UserSearchQuery): Search query object.
            access_token (str | None, optional): User access token for
                API call. Defaults to None.

        Raises:
            VkApiError: Error when using VK API.

        Returns:
            int: Number of user profiles in search result.
        """
        self._logger.debug('Getting search result size for query %r', query)
        params = VkUsersSearchParams(count=0)
        _add_search_query(params, query)
        if access_token is not None:
            params['access_token'] = access_token

        try:
            response = self._vk.method('users.search', params)
        except vk_api.exceptions.VkApiError as e:
            self._logger.error('Get search result size error: %s', e)
            _reraise(e)

        # Use type checker for VK API response
        response = cast(VkUsersSearchResult, response)
        count = response['count']
        self._logger.debug('Search result size %d for query %r', count, query)
        return count

    def search_user(
        self,
        query: UserSearchQuery,
        access_token: str | None = None,
    ) -> User | None:
        """Perform user search using specified search query.

        Args:
            query (UserSearchQuery): Search query object.
            access_token (str | None, optional): User access token for
                API call. Defaults to None.

        Returns:
            User | None: User profile found if any.

        Raises:
            VkApiError: Error when using VK API.
        """
        self._logger.debug('Searching users with query %r', query)

        # To extract random user we must know number of users in search result
        total = self.get_search_result_size(query, access_token)
        if not total:
            self._logger.warning('No results for query %r', query)
            return None

        # VK API limits search query results to 1000 no matter what
        effective_total = min(total, 1000)
        random_offset = random.randint(0, effective_total)

        params = VkUsersSearchParams(
            count=1,
            offset=random_offset,
            fields=_REQUEST_USER_FIELDS,
        )
        _add_search_query(params, query)
        if access_token is not None:
            params['access_token'] = access_token

        try:
            response = self._vk.method('users.search', params)
        except vk_api.exceptions.VkApiError as e:
            self._logger.error('User search error: %s', e)
            _reraise(e)

        # Use type checker for VK API response
        response = cast(VkUsersSearchResult, response)

        if users := response.get('items', []):
            return _convert_user(users[0])
        self._logger.warning('No users found for query %r', query)
        return None

    def get_user_profile(self, user_id: int) -> User:
        """Extract user profile by their profile id.

        Args:
            user_id (int): User profile id.

        Raises:
            VkApiError: Error when using VK API.
            VkUserNotFoundError: No user profile for this user id.

        Returns:
            User: User object.
        """
        self._logger.debug('Extracting user profile for id=%d', user_id)

        params = VkUsersGetParams(
            user_ids=user_id,
            fields=_REQUEST_USER_FIELDS,
        )

        try:
            response = self._vk.method('users.get', params)
        except vk_api.exceptions.VkApiError as e:
            self._logger.error(
                'Error when extracting user profile %d: %s',
                user_id,
                e,
            )
            _reraise(e)

        # Use type checker for VK API response
        users = cast(VkUsersGetResult, response)

        try:
            user = users[0]
        except IndexError as e:
            self._logger.error('No user profile %d', user_id)
            raise VkUserNotFoundError(user_id) from e

        self._logger.info('Extracted user profile %d', user_id)
        user = _convert_user(users[0])
        self._logger.debug('Extracted user: %r', user)
        return user

    def get_user_photos(
        self,
        user_id: int,
        *,
        sort_by_likes: bool = False,
        limit: int | None = None,
        access_token: str | None = None,
    ) -> list[Photo]:
        """Extracts user profile photos with optional sorting.

        Args:
            user_id (int): User profile id.
            sort_by_likes (bool, optional): Sort photos by like count in
                descending order. Defaults to `False`.
            limit (int | None, optional): Limit result up to `limit`
                photos if specified. Defaults to `None`.
            access_token (str | None, optional): User access token for
                API call. Defaults to None.

        Raises:
            VkApiError: Error when using VK API.

        Returns:
            list[Photo]: User profile protos.
        """
        self._logger.debug('Extracting photos from user %d', user_id)

        params = VkPhotosGetParams(
            owner_id=user_id,
            album_id='profile',
            photo_ids=0,
            extended=1,
        )
        if access_token is not None:
            params['access_token'] = access_token

        try:
            response = self._vk.method('photos.get', params)
        except vk_api.exceptions.VkApiError as e:
            self._logger.error('Get photo for user %d: %s', user_id, e)
            _reraise(e)

        # Use type checker for VK API response
        response = cast(VkPhotosGetExResult, response)

        result: list[Photo] = []
        photos = response['items']

        # Extract all photos from response
        for photo in photos:
            orig_photo = _get_photo_source(photo)
            result.append(
                Photo(
                    id=photo['id'],
                    owner_id=photo['owner_id'],
                    likes=photo['likes']['count'],
                    url=orig_photo['url'],
                ),
            )

        # Postprocess result list
        if sort_by_likes:
            result = sorted(result, key=lambda x: x.likes, reverse=True)
        if limit is not None:
            result = result[:limit]
        return result

    def _create_vk(self, token: str) -> vk_api.VkApi:
        """Internal helper to create VK API object.

        Args:
            token (str): VK API access token.

        Raises:
            VkApiError: Error while creating VK API object.

        Returns:
            VkApi: VK API object.
        """
        try:
            return vk_api.VkApi(token=token)
        except vk_api.exceptions.VkApiError as e:
            self._logger.critical('Failed to connect to VK API: %s', e)
            _reraise(e)

    def _create_longpoll(self) -> VkLongPoll:
        """Internal helper to create VK longpoll object.

        Raises:
            VkApiError: Error while creating VK longpoll object.

        Returns:
            VkApi: VK longpoll object.
        """
        try:
            return VkLongPoll(self._vk)
        except vk_api.exceptions.VkApiError as e:
            self._logger.critical('Failed to connect to VK longpoll: %s', e)
            _reraise(e)

    def _listen(self) -> Iterator[Event]:
        """Yields events from longpoll server infinitely.

        Yields:
            Event: New events.
        """
        try:
            yield from self._longpoll.listen()
        except vk_api.exceptions.VkApiError as e:
            self._logger.critical('VK listen error: %s', e)
            _reraise(e)

    def _check(self) -> list[Event]:
        """Checks for events in longpoll server and returns list of new ones.

        Returns:
            list[Event]: New events.
        """
        try:
            return self._longpoll.check()
        except vk_api.exceptions.VkApiError as e:
            self._logger.critical('VK check error: %s', e)
            _reraise(e)

    def _log_events(self, events: Iterator[Event]) -> Iterator[Event]:
        return map(self._log_event, events)

    def _log_event(self, event: Event) -> Event:
        self._logger.info(
            'Message from user %d: [%s]',
            event.user_id,
            event.text,
        )
        return event

    @staticmethod
    def _is_message_event(event: Event) -> bool:
        """Internal helper that filters only VK events on receiving message.

        Args:
            event (Event): VK event object.

        Returns:
            bool: `True` if event is a received message event,
                otherwise `False`.
        """
        return event.type == VkEventType.MESSAGE_NEW and event.to_me


def _get_random_id() -> int:
    """Internal helper that generates random id for message.

    Returns:
        int: Random id number.
    """
    return random.randrange(10**7)


_REQUEST_USER_FIELDS = (
    'nickname, first_name, last_name, city, sex, bdate, domain, online'
)


_VK_SEX_TO_SEX: dict[VkSex, Sex] = {
    VkSex.NOT_SPECIFIED: Sex.NOT_KNOWN,
    VkSex.FEMALE: Sex.FEMALE,
    VkSex.MALE: Sex.MALE,
}
"""VK sex mapping."""


_SEX_TO_VK_SEX: dict[Sex, VkSex] = {
    sex: vk_sex for vk_sex, sex in _VK_SEX_TO_SEX.items()
}
"""Inverted VK sex mapping."""


def _convert_sex(sex: VkSex | None) -> Sex:
    """Convert VK sex notation to standard.

    Args:
        sex (VkSex | None): VK sex.

    Returns:
        Sex: Standard sex.
    """
    try:
        vk_sex = VkSex(sex)
    except ValueError:
        return Sex.NOT_KNOWN
    return _VK_SEX_TO_SEX[vk_sex]


def _convert_bdate(bdate: str | None) -> datetime.date | None:
    """Internal helper that parses VK birth date format.

    Args:
        bdate (str | None): Input birth date string, if any.

    Returns:
        datetime.date | None: Extracted date object if input is correct
            and complete. If input is invalid or some date parts are
            missing, then `None`.
    """
    if bdate is None:
        # Birth date is missing completely
        return None
    try:
        parts = tuple(map(int, bdate.split('.')))
        day, month, year = parts
        # Birth date is complete and OK
        return datetime.date(year, month, day)
    except (ValueError, IndexError):
        # Invalid input format or birth year is missing
        return None


def _convert_user(user: VkUser) -> User:
    """Convert VK user object to `User`.

    Args:
        user (VkUser): VK user object.

    Returns:
        User: User object.
    """
    user_id = user['id']
    url = user.get('domain') or f'id{user_id}'
    city = user.get('city')
    bdate = user.get('bdate')
    return User(
        id=user_id,
        first_name=user['first_name'],
        last_name=user['last_name'],
        sex=_convert_sex(user.get('sex')),
        birthday=_convert_bdate(bdate),
        birthday_raw=bdate,
        city_id=city and city['id'],
        city=city and city['title'],
        nickname=user.get('nickname'),
        url=f'https://vk.com/{url}',
        online=bool(user.get('online')),
    )


_VK_BUTTON_COLOR_MAPPING: Final = {
    ButtonColor.PRIMARY: vk_api.keyboard.VkKeyboardColor.PRIMARY,
    ButtonColor.SECONDARY: vk_api.keyboard.VkKeyboardColor.SECONDARY,
    ButtonColor.NEGATIVE: vk_api.keyboard.VkKeyboardColor.NEGATIVE,
    ButtonColor.POSITIVE: vk_api.keyboard.VkKeyboardColor.POSITIVE,
}


def _convert_color(color: ButtonColor) -> vk_api.keyboard.VkKeyboardColor:
    """Internal helper to convert button color to VK API format.

    Args:
        color (ButtonColor): Button color.

    Returns:
        vk_api.keyboard.VkKeyboardColor: Button color in VK API format.
    """
    try:
        return _VK_BUTTON_COLOR_MAPPING[color]
    except KeyError as e:
        raise NotImplementedError from e


def _convert_keyboard(keyboard: Keyboard | None) -> str:
    """Internal helper to convert bot keyboard object to VK API JSON format.

    Args:
        keyboard (Keyboard | None): Bot keyboard if any.

    Returns:
        str: Bot keyboard in JSON format.
    """
    if keyboard is None:
        return vk_api.keyboard.VkKeyboard.get_empty_keyboard()

    vk_kb = vk_api.keyboard.VkKeyboard(
        one_time=keyboard.one_time,
        inline=keyboard.inline,
    )
    # VkKeyboard creates the first empty line, erase it
    vk_kb.lines.clear()

    for row in keyboard.button_rows:
        vk_kb.add_line()
        for button in row:
            payload = button.payload
            if isinstance(button, TextButton):
                color = _convert_color(button.color)
                vk_kb.add_button(button.text, color, payload)
            elif isinstance(button, OpenLinkButton):
                vk_kb.add_openlink_button(button.text, button.link, payload)
            else:
                raise NotImplementedError
    return vk_kb.get_keyboard()


def _convert_attachment(media: list[Media]) -> str:
    """Internal helper to construct 'attachment' field for VK API call.

    Args:
        media (list[Media]): List of media objects to attach.

    Returns:
        str: 'attachment' field for VK API call.
    """
    return ','.join(f'{x.type}{x.owner_id}_{x.id}' for x in media)


def _get_photo_source(photo: VkPhoto) -> VkPhotoSource:
    """Internal helper that extracts largest photo from VK API response.

    Args:
        photo (VkPhoto): Photo descriptor from VK API.

    Returns:
        VkPhotoSource: Photo source descriptor from VK API.
    """
    # Try to use convenience field for original photo (undocumented)
    orig_photo = photo.get('orig_photo')
    if orig_photo is not None:
        return orig_photo

    # Search in 'sizes' for original photo (undocumented)
    for source in photo['sizes']:
        if source['type'] == VkPhotoType.ORIGINAL:
            return source

    # Fallback option: use the photo of most size (pixel count)
    return max(photo['sizes'], key=lambda x: x['width'] * x['height'])


def _add_search_query(
    params: VkUsersSearchParams,
    query: UserSearchQuery,
) -> None:
    """Internal helper to add data from search query to API call parameters.

    Args:
        params (VkUsersSearchParams): API call parameters.
        query (UserSearchQuery): User search query object.
    """
    if query.sex is not None:
        params['sex'] = _SEX_TO_VK_SEX[query.sex]
    if query.city_id is not None:
        params['city'] = query.city_id
    if query.online is not None:
        params['online'] = query.online
    if query.has_photo is not None:
        params['has_photo'] = query.has_photo
    if query.age_min is not None:
        params['age_from'] = query.age_min
    if query.age_max is not None:
        params['age_to'] = query.age_max


_TOKEN_ERROR_CODES: Final = {
    5,  # User authorization failed
    15,  # Access denied
    102,  # Invalid token format
    113,  # Invalid signature
    200,  # Permissions denied
    1114,  # Anonymous token expired
    1116,  # Anonymous token is invalid
}
_AUTH_STATUS_CODES: Final = {400, 401}


def is_token_error(e: vk_api.exceptions.VkApiError) -> bool:
    """Checks whether VK API error is about invalid token or not.

    Args:
        e (vk_api.exceptions.VkApiError): VK API exception.

    Returns:
        bool: `True` if token error, otherwise `False`.
    """
    if isinstance(e, vk_api.exceptions.ApiError):
        return e.code in _TOKEN_ERROR_CODES
    if isinstance(e, vk_api.exceptions.ApiHttpError):
        return e.response.status_code in _AUTH_STATUS_CODES
    return False


def _reraise(e: vk_api.exceptions.VkApiError) -> NoReturn:
    """Reraise exception from VK API with type detection.

    Args:
        e (vk_api.exceptions.VkApiError): VK API exception.

    Raises:
        VkTokenError: Access token is invalid.
        VkApiError: Generic VK API error.

    Returns:
        NoReturn: Never returns, always raises exception.
    """
    if is_token_error(e):
        raise VkTokenError(e) from e
    raise VkApiError(e) from e
