"""This module provides means to proceed with user authorization."""

import dataclasses
import datetime
from queue import Queue
import secrets
import threading
from typing import Literal, NotRequired, TypedDict, cast
from urllib.parse import urlencode
from urllib.parse import urlparse

from flask import Flask
from flask import request
import pkce
import requests

from vkinder.config import AuthConfig
from vkinder.log import get_logger
from vkinder.model import AuthProviderRefreshError
from vkinder.model import AuthRecord

AUTH_ROUTE = '/auth'


type RouteResponse = tuple[str, int]


class AuthRouteParams(TypedDict):
    """Query parameters for `AUTH_ROUTE`."""

    state: str


class AuthorizeParams(TypedDict):
    """Query parameters for https://id.vk.ru/authorize."""

    client_id: int
    response_type: Literal['code']
    redirect_uri: str
    state: NotRequired[str]
    scope: NotRequired[str]
    code_challenge: NotRequired[str]
    code_challenge_method: NotRequired[Literal['S256']]
    display: NotRequired[Literal['page', 'popup', 'touch', 'mobile']]
    vk_platform: NotRequired[Literal['standalone', 'web']]


class AuthCallbackCodeParams(TypedDict):
    """Query parameters passed to auth redirect callback."""

    type: Literal['code_v2']
    code: str
    expires_in: int
    device_id: str
    state: str
    ext_id: str


class Oauth2DataParamsBase(TypedDict):
    """Common data parameters for https://id.vk.ru/oauth2/auth."""

    client_id: int
    device_id: str
    state: NotRequired[str]


class Oauth2AuthDataParams(Oauth2DataParamsBase):
    """Authorization data parameters for https://id.vk.ru/oauth2/auth."""

    grant_type: Literal['authorization_code']
    code: str
    code_verifier: str
    redirect_uri: str


class Oauth2AuthResponse(TypedDict):
    """Authorization response from https://id.vk.ru/oauth2/auth."""

    refresh_token: str
    access_token: str
    id_token: str
    token_type: str
    expires_in: int
    state: str
    user_id: int
    scope: str


class Oauth2RefreshDataParams(Oauth2DataParamsBase):
    """Refresh data parameters for https://id.vk.ru/oauth2/auth."""

    grant_type: Literal['refresh_token']
    refresh_token: str
    scope: NotRequired[str]


@dataclasses.dataclass
class SessionData:
    """Data stored per-session."""

    access_rights: str
    code_verifier: str
    code_challenge: str
    chat_id: int | None


class AuthService:
    """Provides means to proceed with user authorization."""

    def __init__(
        self,
        config: AuthConfig,
        queue: Queue[AuthRecord],
        group_id: int | None = None,
    ) -> None:
        """Initialize authorization service object.

        Args:
            config (AuthConfig): Config object.
            queue (Queue[AuthRecord]): Queue to put new authorization
                data from users.
            group_id (int | None, optional): Bot group id. Defaults to None.
        """
        self._logger = get_logger(self)
        self._config = config
        self._queue = queue
        self._group_id = group_id

        self._app = Flask(__name__)

        # Use redirect URI network location for redirects
        parsed = urlparse(self._config.vk_auth_redirect_uri)
        self._root_url = f'{parsed.scheme}://{parsed.netloc}'

        # Register route for auth redirection
        self._app.add_url_rule(
            rule=AUTH_ROUTE,
            view_func=self._auth_route,
            methods=['GET'],
        )

        # Extract path from redirect URI and register it as callback
        callback_path = parsed.path or '/'
        self._app.add_url_rule(
            rule=callback_path,
            view_func=self._callback_route,
            methods=['GET'],
        )

        # Store data per-session
        self._session_data: dict[str, SessionData] = {}

        # Keep single session for every user
        self._user_session: dict[int, str] = {}
        self._session_user: dict[str, int] = {}

        self._thread: threading.Thread | None = None
        self._logger.info('Auth service is initialized')

    def start_auth_server(self) -> None:
        """Start the authorization server in a thread and return."""
        self._thread = threading.Thread(target=self.run_auth_server)
        self._thread.start()
        self._logger.info('Started auth server')

    def run_auth_server(self) -> None:
        """Start the authorization server and run it indefinitely."""
        port = self._config.auth_server_port
        self._logger.info('Starting auth server on port %d...', port)
        self._app.run(host='0.0.0.0', port=port)

    def refresh_auth(self, record: AuthRecord) -> AuthRecord:
        """Get new user access token using refresh token.

        Args:
            record (AuthRecord): Auth record object.

        Raises:
            AuthProviderRefreshError: Failed to refresh token.

        Returns:
            AuthRecord: New auth record object.
        """
        user_id = record.user_id
        self._logger.debug('Refreshing auth for user %d', user_id)

        config = self._config
        device_id = record.device_id

        # Exchange refresh token for new access token
        data = Oauth2RefreshDataParams(
            grant_type='refresh_token',
            refresh_token=record.refresh_token,
            client_id=config.vk_app_id,
            device_id=device_id,
            scope=record.access_rights,
        )

        response = requests.post('https://id.vk.ru/oauth2/auth', data=data)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self._logger.error('Token refresh error: %s', e)
            raise AuthProviderRefreshError(e) from e
        self._logger.info('Refreshed token for user %d', user_id)

        # OK, got the access token
        auth = cast(Oauth2AuthResponse, response.json())
        return self._convert_auth_record(auth, device_id)

    def create_auth_link(
        self,
        user_id: int,
        access_rights: str,
        chat_id: int | None = None,
    ) -> str:
        """Constructs link for user to proceed with authorization.

        Args:
            user_id (int): User id.
            access_rights (str): User access right set to request from user.
            chat_id (int | None, optional): Chat id of message to the bot.
                Defaults to None.

        Returns:
            str: Authorization link.
        """
        # Pre-generate PKCE data
        code_verifier, code_challenge = pkce.generate_pkce_pair()

        # Clean up the old session
        self._clear_user_session(user_id)

        # Create a new session
        session = secrets.token_urlsafe(32)
        self._user_session[user_id] = session
        self._session_user[session] = user_id
        self._session_data[session] = SessionData(
            access_rights=access_rights,
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            chat_id=chat_id,
        )

        params = AuthRouteParams(state=session)
        query = urlencode(params)

        # Redirect to auth link from this server
        return f'{self._root_url}{AUTH_ROUTE}?{query}'

    def _create_auth_link(self, session: str) -> str:
        """Constructs VK ID link for user to proceed with authorization.

        Args:
            session (int): Session id.

        Returns:
            str: Authorization link.
        """
        session_data = self._session_data[session]
        params = AuthorizeParams(
            client_id=self._config.vk_app_id,
            redirect_uri=self._config.vk_auth_redirect_uri,
            state=session,
            response_type='code',
            scope=session_data.access_rights,
            code_challenge=session_data.code_challenge,
            code_challenge_method='S256',
            display='page',
            vk_platform='standalone',
        )
        query = urlencode(params, encoding='utf-8', errors='surrogatepass')
        return f'https://id.vk.ru/authorize?{query}'

    def _clear_user_session(self, user_id: int) -> None:
        """Erase all session data for the given user id.

        Args:
            user_id (int): User id.
        """
        session = self._user_session.get(user_id)
        if session is not None:
            del self._user_session[user_id]
            del self._session_user[session]
            del self._session_data[session]

    def _auth_route(self) -> RouteResponse:
        """Server endpoint to start authorization procedure.

        Returns:
            RouteResponse: _description_
        """
        self._log_route_call()

        # Get session id from query parameters
        args = cast(AuthRouteParams, request.args)
        try:
            session = args['state']
            user_id = self._session_user[session]
        except KeyError:
            return self._respond_invalid_state()

        self._logger.info('Authorization from user %s', user_id)

        # Redirect user to the real authorization URL
        auth_url = self._create_auth_link(session)
        self._logger.info('Redirecting to: %s', auth_url)
        return self._respond_redirection(auth_url)

    def _callback_route(self) -> RouteResponse:
        """Server endpoint to be called by VK ID redirection.

        Returns:
            RouteResponse: _description_
        """
        self._log_route_call()

        # Get session id from query parameters
        args = cast(AuthCallbackCodeParams, request.args)
        try:
            session = args['state']
            user_id = self._session_user[session]
        except KeyError:
            return self._respond_invalid_state()

        self._logger.info('Callback from user %s', user_id)

        session_data = self._session_data[session]
        config = self._config
        device_id = args['device_id']

        # Exchange code for VK ID access token
        data = Oauth2AuthDataParams(
            grant_type='authorization_code',
            code=args['code'],
            client_id=config.vk_app_id,
            device_id=device_id,
            redirect_uri=config.vk_auth_redirect_uri,
            code_verifier=session_data.code_verifier,
        )

        response = requests.post('https://id.vk.ru/oauth2/auth', data=data)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self._logger.error('Token get error: %s', e)

            # Show error message
            return self._respond_auth_error(
                response.status_code,
                response.text,
            )
        self._logger.info('Got token for user %d', user_id)

        # OK, got the access token
        auth = cast(Oauth2AuthResponse, response.json())

        # User session is done
        self._clear_user_session(user_id)

        # Notify about successful authorization
        self._queue.put(self._convert_auth_record(auth, device_id))

        # Close the page automatically
        return self._respond_auth_success_and_close(
            group_id=self._group_id,
            chat_id=session_data.chat_id,
        )

    @staticmethod
    def _convert_auth_record(
        auth: Oauth2AuthResponse,
        device_id: str,
    ) -> AuthRecord:
        """Constructs aht record from VK ID response.

        Args:
            auth (Oauth2AuthResponse): VK ID auth response.
            device_id (str): Device id value.

        Returns:
            AuthRecord: Auth record.
        """
        expires_in = auth['expires_in']
        now = datetime.datetime.now(datetime.UTC).astimezone()
        expire_time = now + datetime.timedelta(seconds=expires_in)
        return AuthRecord(
            user_id=auth['user_id'],
            access_token=auth['access_token'],
            refresh_token=auth['refresh_token'],
            device_id=device_id,
            expire_time=expire_time,
            access_rights=auth['scope'],
        )

    def _log_route_call(self):
        """Internal helper to log server route call."""
        self._logger.info(
            '%s is called from %s, query: %s',
            request.path,
            request.remote_addr,
            request.query_string.decode(),
        )
        self._logger.debug('Headers:\n%s', request.headers)

    @staticmethod
    def _respond_redirection(url: str) -> RouteResponse:
        """Redirect user to the given URL.

        Args:
            url (str): Redirection URL.

        Returns:
            RouteResponse: Server HTTP response.
        """
        # When responding with 302 VK can fail to open this URL.
        # VK passes some additional headers when clicked on link open button.
        # Redirect using JS to drop VK headers.
        html = f"""
            <!DOCTYPE html>
            <html>
            <head><title></title></head>
            <body><script>window.location.href = '{url}';</script></body>
            </html>
        """
        # No redirection code
        code = 200
        return html, code

    @staticmethod
    def _respond_auth_success_and_close(
        group_id: int | None,
        chat_id: int | None,
    ) -> RouteResponse:
        """Redirect user to the given URL.

        Args:
            group_id (int | None): Bot group id.
            chat_id (int | None): Chat id of message to the bot.

        Returns:
            RouteResponse: Server HTTP response.
        """
        target = f'c{chat_id}' if chat_id else group_id and f'-{group_id}'
        select_chat = f'?sel={target}' if target else ''
        html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Authorized successfully</title></head>
            <body>
            <p><font size="30">You may close this window.</font></p>
            <script>
                if (window.opener) {{
                    // Close window or WebView
                    window.close();
                }} else {{
                    // Redirect user back to chat
                    window.location.href = 'vk://vk.com/im{select_chat}';
                }}
            </script>
            </body>
            </html>
        """
        code = 200
        return html, code

    @staticmethod
    def _respond_auth_error(status_code: int, text: str) -> RouteResponse:
        """Show authorization error message to user.

        Args:
            status_code (int): HTTP error code.
            text (str): HTTP error message text.

        Returns:
            RouteResponse: Server HTTP response.
        """
        html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Authorization failed</title></head>
            <body><p>Authorization error: {status_code} - {text}</p></body>
            </html>
        """
        code = 401
        return html, code

    @staticmethod
    def _respond_invalid_state() -> RouteResponse:
        """Show error message about invalid state parameter to user.

        Returns:
            RouteResponse: Server HTTP response.
        """
        html = """
            <!DOCTYPE html>
            <html>
            <head><title>Authorization failed</title></head>
            <body><p>Invalid state parameter value.</p></body>
            </html>
        """
        code = 400
        return html, code
