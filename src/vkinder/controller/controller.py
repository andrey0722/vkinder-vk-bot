"""This module implements main logic of the bot and message handling."""

from collections.abc import Callable
from collections.abc import Iterator
from queue import Empty
from queue import Queue
from typing import Final, cast

from vkinder.config import AuthConfig
from vkinder.config import VkConfig
from vkinder.log import get_logger
from vkinder.model import AuthRecord
from vkinder.model import Database
from vkinder.model import DatabaseSession
from vkinder.model import ModelError
from vkinder.model import StateManager
from vkinder.shared_types import InputMessage
from vkinder.shared_types import Response
from vkinder.shared_types import UserAuthData
from vkinder.view import normalize_menu_command
from vkinder.view import render_messages
from vkinder.view.strings import Command

from .auth_service import AuthService
from .vk_service import Event
from .vk_service import VkService
from .vk_service import VkServiceError

type MessageHandler = Callable[
    [DatabaseSession, InputMessage],
    Iterator[Response],
]


class Controller:
    """Handles user messages and responds to user."""

    def __init__(
        self,
        db: Database,
        vk_config: VkConfig,
        auth_config: AuthConfig,
    ) -> None:
        """Initialize a controller object.

        Args:
            db (Database): Database object.
            vk_config (VkConfig): VK API config.
            auth_config (AuthConfig): VK ID auth config.
        """
        self._logger = get_logger(self)
        self._db = db
        self._vk = VkService(vk_config)
        self._auth_queue = Queue[AuthRecord]()
        group_id = self._vk.get_group_id()
        self._auth = AuthService(auth_config, self._auth_queue, group_id)
        self._state_manager = StateManager(self._vk, self._auth)

        self._COMMAND_MAP: Final[dict[Command, MessageHandler]] = {
            Command.START: self._state_manager.start_main_menu,
        }
        self._DEFAULT_HANDLER: Final = self._state_manager.respond

    def close(self) -> None:
        """Close all services."""
        self._vk.close()
        self._auth.close()

    def start_message_loop(self) -> None:
        """Process all incoming messages and keep running until stopped."""
        # Allow users to perform authorization
        self._auth.start_auth_server()
        while True:
            # Check new messages
            for message in self._vk.check_messages():
                # process auth data between messages
                self.process_auth_queue()
                try:
                    self.handle_message(message)
                except (ModelError, VkServiceError):
                    self._logger.error(
                        'Failed to handle message from %d',
                        message.user_id,
                    )
            # Process new authorization data if no new messages
            self.process_auth_queue()

    def process_auth_queue(self) -> None:
        """Process all new user authorization data records."""
        while not self._auth_queue.empty():
            try:
                auth_data = self._auth_queue.get_nowait()
            except Empty:
                break
            self.handle_auth_record(auth_data)

    def handle_auth_record(self, record: AuthRecord) -> None:
        """Store user authorization data for further use.

        Args:
            record (AuthRecord): User authorization data.
        """
        self._logger.info('Auth record for user %d', record.user_id)
        with self._db.create_session() as session, session.begin():
            auth_data = UserAuthData(**record.asdict())
            session.save_auth_data(auth_data)

    def handle_message(self, event: Event) -> None:
        """Process incoming message event and send response to user.

        Args:
            event (Event): VK message event.
        """
        user_id = cast(int, event.user_id)
        text = event.text
        vk = self._vk

        self._logger.info('Handling message from user %d: [%s]', user_id, text)

        handler = self._get_command_handler(text)
        with self._db.create_session() as session:
            message = self._event_to_message(session, event)

            # Sequence of messages from the state machine
            responses = handler(session, message)

            # Squash all messages from handler to small number of messages
            messages = render_messages(message.user, responses)
            for message in messages:
                try:
                    vk.send(message)
                except VkServiceError:
                    self._logger.error(
                        'Error when sending message to user %d',
                        user_id,
                    )

    def _get_command_handler(self, text: str) -> MessageHandler:
        text = text.lower().strip()
        for command in Command:
            if text in command:
                return self._COMMAND_MAP[command]
        return self._DEFAULT_HANDLER

    def _event_to_message(
        self,
        session: DatabaseSession,
        event: Event,
    ) -> InputMessage:
        """Internal helper that extracts all required data from VK event.

        Args:
            session (DatabaseSession): Session object.
            event (Event): Event from VK service.

        Returns:
            InputMessage: Message object.
        """
        user_id = cast(int, event.user_id)
        chat_id = cast(int, event.chat_id) if event.from_chat else None
        user = self._vk.get_user_profile(user_id)
        with session.begin():
            user = session.save_user(user)
            progress = session.get_user_progress(user)
        text = normalize_menu_command(event.text)
        return InputMessage(user, text, progress, chat_id)
