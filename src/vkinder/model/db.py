"""This module defines logic of database interaction.."""

from collections.abc import Callable
import contextlib
from types import TracebackType
from typing import Self, override

import sqlalchemy as sa
from sqlalchemy import exc
from sqlalchemy import orm

from ..config import DatabaseConfig
from ..log import get_logger
from .exceptions import DatabaseError
from .exceptions import UserNotFoundError
from .log import set_sqlalchemy_debug_filter
from .types import ModelBaseType
from .types import User
from .types import UserState

type OrmSessionFactory = Callable[[], orm.Session]


class DatabaseSession(contextlib.AbstractContextManager):
    """Controls database ORM session operation."""

    def __init__(self, factory: OrmSessionFactory) -> None:
        """Initialize a session object.

        Args:
            factory (OrmSessionFactory): ORM session factory.
        """
        super().__init__()
        self._logger = get_logger(self)
        self._session = factory()

    @override
    def __enter__(self) -> Self:
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self._session.close()

    def begin(self) -> orm.SessionTransaction:
        """Begin database session transaction block.

        Returns:
            SessionTransaction: Transaction context manager.
        """
        return self._session.begin()

    def commit(self) -> None:
        """Saves pending changes into the DB.

        Raises:
            DatabaseError: DB operational error.
        """
        try:
            self._session.commit()
        except exc.SQLAlchemyError as e:
            me = _create_db_error(e)
            self._logger.error('Commit error: %s', e)
            raise me from e

    def user_exists(self, user_id: int) -> bool:
        """Checks whether the DB contains user with specified id.

        Args:
            user_id (int): User id.

        Returns:
            bool: `True` is the user exists, otherwise `False`.

        Raises:
            DatabaseError: DB operational error.
        """
        self._logger.debug('Checking if user %s exists', user_id)
        return self.get_user(user_id) is not None

    def get_user(self, user_id: int) -> User | None:
        """Extracts a user from the DB using user id.

        Args:
            user_id (int): User id.

        Returns:
            User | None: Found user object for this id if any,
                otherwise `None`.

        Raises:
            DatabaseError: DB operational error.
        """
        self._logger.debug('Extracting user %s', user_id)
        try:
            user = self._session.get(User, user_id)
        except exc.SQLAlchemyError as e:
            me = _create_db_error(e)
            self._logger.error('Get error: user=%r, error=%s', user_id, e)
            raise me from e

        if user is not None:
            self._logger.debug('User exists: %r', user)
        else:
            self._logger.debug('User %s does not exist', user_id)
        return user

    def add_user(self, user: User) -> None:
        """Adds new user into the DB.

        Input object could be modified in-place to respect current DB state.

        Args:
            user (User): User object.

        Raises:
            DatabaseError: DB operational error.
        """
        self._logger.debug('Adding user %r', user)
        try:
            self._session.add(user)
        except exc.SQLAlchemyError as e:
            me = _create_db_error(e)
            self._logger.error('Add error: user=%r, error=%s', user, e)
            raise me from e

        self._logger.debug('Added user %r', user)

    def update_user(self, user: User) -> User:
        """Updates existing user info in the DB.

        Args:
            user (User): User object.

        Returns:
            User: User object now associated with this session.

        Raises:
            UserNotFoundError: The user is not found in the DB.
            DatabaseError: DB operational error.
        """
        self._logger.debug('Updating user %r', user)
        try:
            session = self._session
            if session.get(User, user.id) is None:
                raise UserNotFoundError(user)
            result = session.merge(user)
        except exc.SQLAlchemyError as e:
            me = _create_db_error(e)
            self._logger.error('Update error: user=%r, error=%s', user, e)
            raise me from e

        self._logger.debug('Updated user %r', result)
        return result

    def add_or_update_user(self, user: User) -> User:
        """Updates existing user info in the DB or adds if absent.

        Input object could be modified in-place to respect current DB state.

        Args:
            user (User): User object.

        Returns:
            User: User object now associated with this session.

        Raises:
            DatabaseError: DB operational error.
        """
        # See if we have this user in the model
        if existing_user := self.get_user(user.id):
            # Apply user state from the model
            user.state = existing_user.state
            # Update user info, it could change since last message
            user = self.update_user(user)
        else:
            # User is now known
            user.state = UserState.NEW_USER
            self._logger.info('New user: %s', user)
            self.add_user(user)
        self.commit()
        return user

    def delete_user(self, user_id: int) -> User | None:
        """Deletes user from the DB.

        Args:
            user_id (int): User id.

        Returns:
            User | None: User object previously stored in the DB,
                if any, otherwise `None`.

        Raises:
            DatabaseError: DB operational error.
        """
        self._logger.debug('Deleting user %r', user_id)
        try:
            stmt = sa.delete(User).where(User.id == user_id).returning(User)
            user = self._session.scalar(stmt)
        except exc.SQLAlchemyError as e:
            me = _create_db_error(e)
            self._logger.error('Delete error: user=%r, error=%s', user_id, e)
            raise me from e

        if user is not None:
            self._logger.debug('User deleted %r', user)
        else:
            self._logger.warning('No user %s, cannot delete', user_id)
        return user


class Database:
    """Stores data in database persistently."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize database model object.

        Args:
            config (DatabaseConfig): DB connection parameters.

        Raises:
            ModelError: Model creation error.
        """
        super().__init__()
        self._logger = get_logger(self)
        self._engine = self._create_engine(config)
        self._session_factory = self._create_session_factory()
        self._test_db_connection()
        if config.clear_data:
            self._drop_tables()
        self._create_tables()

    def create_session(self) -> DatabaseSession:
        """Create session to interact with objects in the database.

        Returns:
            Session: Session object.
        """
        return DatabaseSession(self._session_factory)

    def _create_tables(self) -> None:
        """Internal helper to create tables for all entities in the DB.

        Raises:
            DatabaseError: DB operational error.
        """
        try:
            self._logger.debug('Creating tables')
            ModelBaseType.metadata.create_all(self._engine)
        except exc.SQLAlchemyError as e:
            me = _create_db_error(e)
            self._logger.critical('Create tables error: %s', e)
            raise me from e

    def _drop_tables(self) -> None:
        """Internal helper to delete tables for all entities in the DB.

        Raises:
            DatabaseError: DB operational error.
        """
        try:
            self._logger.debug('Deleting tables')
            ModelBaseType.metadata.drop_all(self._engine)
        except exc.SQLAlchemyError as e:
            me = _create_db_error(e)
            self._logger.critical('Delete tables error: %s', e)
            raise me from e

    def _create_dsn(self, config: DatabaseConfig) -> sa.URL:
        """Internal helper to form and return a DSN from `DatabaseConfig`.

        Args:
            config (DatabaseConfig): DB connection parameters.

        Returns:
            URL: DSN URL for the database connection.
        """
        return sa.URL.create(
            drivername=config.driver,
            host=config.host,
            port=config.port,
            database=config.database,
            username=config.user,
            password=config.password,
        )

    def _create_engine(self, config: DatabaseConfig) -> sa.Engine:
        """Internal helper to create and return DB engine object.

        Args:
            config (DatabaseConfig): DB connection parameters.

        Returns:
            Engine: DB engine object.
        """
        engine = sa.create_engine(self._create_dsn(config))
        set_sqlalchemy_debug_filter(engine)
        return engine

    def _create_session_factory(self) -> OrmSessionFactory:
        """Internal helper that creates and returns ORM session factory.

        Creates ORM session factory with required parameters
        which creates session objects to perform DB operations.

        Returns:
            SessionFactory: ORM session factory.
        """
        return orm.sessionmaker(
            bind=self._engine,
            autoflush=False,
            expire_on_commit=False,
        )

    def _test_db_connection(self) -> None:
        """Internal helper to create a test connection to the DB.

        Raises:
            DatabaseError: Failed to connect to DB.
        """
        try:
            with self._engine.connect():
                self._logger.info('DB connection is OK')
        except exc.SQLAlchemyError as e:
            me = _create_db_error(e)
            self._logger.critical('DB connection error: %s', e)
            raise me from e


def _create_db_error(e: exc.SQLAlchemyError) -> DatabaseError:
    """Internal helper to create model exception from underlying library.

    Args:
        e (SQLAlchemyError): Underlying library exception.

    Returns:
        DatabaseError: Database exception.
    """
    # Monkey patch the exception to avoid messages like this:
    # Background on this error at: https://sqlalche.me/e/XX/YYYY
    e.code = None
    return DatabaseError(e)
