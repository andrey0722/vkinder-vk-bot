"""This module defines basic types that stores application data."""

import dataclasses
import datetime
import enum

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import WriteOnlyMapped
from sqlalchemy.sql import functions as func


class ModelBaseType(orm.MappedAsDataclass, orm.DeclarativeBase):
    """Base class for all types used by model."""


@enum.unique
class UserState(enum.StrEnum):
    """Current state for a particular user."""

    NEW_USER = enum.auto()
    MAIN_MENU = enum.auto()
    SEARCHING = enum.auto()
    AUTH = enum.auto()
    FAVORITE_LIST = enum.auto()


@enum.unique
class Sex(enum.IntEnum):
    """Human sex designator according to ISO/IEC 5218."""

    NOT_KNOWN = 0
    MALE = 1
    FEMALE = 2


class User(ModelBaseType):
    """Represents one particular user of the bot."""

    __tablename__ = 'user'

    id: Mapped[int] = orm.mapped_column(primary_key=True)
    """User unique VK ID value."""

    first_name: Mapped[str] = orm.mapped_column(sa.String(64))
    """User first name."""

    last_name: Mapped[str] = orm.mapped_column(sa.String(64))
    """User last name."""

    sex: Mapped[Sex] = orm.mapped_column(
        sa.Enum(Sex, name='sex', metadata=ModelBaseType.metadata),
    )
    """User specified sex."""

    birthday: Mapped[datetime.date | None] = orm.mapped_column()
    """User specified birthday."""

    birthday_raw: Mapped[str | None] = orm.mapped_column()
    """User specified birthday in raw format."""

    city_id: Mapped[int | None] = orm.mapped_column()
    """User specified city ID."""

    city: Mapped[str | None] = orm.mapped_column(sa.String(64))
    """User specified city."""

    nickname: Mapped[str | None] = orm.mapped_column(sa.String(64))
    """User nickname if any."""

    url: Mapped[str] = orm.mapped_column(sa.String(64))
    """Short link to user profile page."""

    online: bool = dataclasses.field(default=False)
    """Whether user is online right now or not."""

    state: Mapped[UserState] = orm.mapped_column(
        sa.Enum(UserState, name='userstate', metadata=ModelBaseType.metadata),
        default=UserState.NEW_USER,
    )
    """Current user state."""

    auth_data: Mapped['UserAuthData | None'] = orm.relationship(
        back_populates='user',
        cascade='all, delete-orphan',
        init=False,
        repr=False,
    )
    """User authorization data."""

    user_progress: Mapped['UserProgress | None'] = orm.relationship(
        back_populates='user',
        cascade='all, delete-orphan',
        init=False,
        repr=False,
    )
    """User authorization data."""

    favorites: WriteOnlyMapped['Favorite'] = orm.relationship(
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True,
        init=False,
        repr=False,
    )
    """User's favorite profile list."""

    @property
    def age(self) -> int | None:
        """Calculates user's age AKA number of full years since birth.

        Returns:
            int | None: User's age if birthday is specified. Otherwise `None`.
        """
        birthday = self.birthday
        if not birthday:
            return None
        today = datetime.datetime.now(tz=datetime.UTC).date()
        age = today.year - birthday.year
        if (today.month, today.day) < (birthday.month, birthday.day):
            # Birthday hasn't pass at this year
            age -= 1
        return age


class UserAuthData(ModelBaseType):
    """Holds data from user authorization."""

    __tablename__ = 'auth_data'

    user_id: Mapped[int] = orm.mapped_column(
        sa.ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True,
    )
    user: Mapped[User] = orm.relationship(
        back_populates='auth_data',
        init=False,
        repr=False,
    )
    """Bot user that owns this record."""

    access_token: Mapped[str] = orm.mapped_column(sa.String(400))
    """VK API user access token."""

    refresh_token: Mapped[str] = orm.mapped_column(sa.String(400))
    """VK ID token to refresh access token."""

    expire_time: Mapped[datetime.datetime] = orm.mapped_column(sa.DateTime)
    """Time when user access token becomes invalidated."""

    access_rights: Mapped[str] = orm.mapped_column(sa.String(400))
    """Access right set allocated to user access token."""


class UserProgress(ModelBaseType):
    """Stores user progress in different modes."""

    __tablename__ = 'user_progress'

    user_id: Mapped[int] = orm.mapped_column(
        sa.ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True,
        init=False,
    )
    user: Mapped[User] = orm.relationship(back_populates='user_progress')
    """Bot user that owns this record."""

    last_state: Mapped[UserState] = orm.mapped_column(
        default=UserState.MAIN_MENU,
    )
    """Previous user state."""

    last_found_id: Mapped[int] = orm.mapped_column(default=0)
    """Profile id displayed to the user in last search query."""

    last_fav_index: Mapped[int] = orm.mapped_column(default=0)
    """Favorite record positional index."""

    last_fav_id: Mapped[int] = orm.mapped_column(default=0)
    """Profile id that the user has added as favorite."""


class Favorite(ModelBaseType):
    """Represents one record in user's favorite profile list."""

    __tablename__ = 'favorite'

    user_id: Mapped[int] = orm.mapped_column(
        sa.ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True,
        init=False,
    )
    user: Mapped[User] = orm.relationship(back_populates='favorites')
    """Bot user that owns this record."""

    profile_id: Mapped[int] = orm.mapped_column(primary_key=True)
    """Profile id that the user has added as favorite."""

    created_at: Mapped[datetime.datetime] = orm.mapped_column(
        sa.DateTime,
        server_default=func.now(),
        init=False,
    )
    """Date and time when this record was created."""
