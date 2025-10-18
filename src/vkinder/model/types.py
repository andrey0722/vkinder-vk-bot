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

    last_found_id: Mapped[int| None] = orm.mapped_column(default=None)
    """Profile id displayed to the user in last search query."""

    online: bool = dataclasses.field(default=False)
    """Whether user is online right now or not."""

    state: Mapped[UserState] = orm.mapped_column(
        sa.Enum(UserState, name='userstate', metadata=ModelBaseType.metadata),
        default=UserState.NEW_USER,
    )
    """Current user state."""

    favorites: WriteOnlyMapped['Favorite'] = orm.relationship(
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True,
        init=False,
        repr=False,
    )
    """User's favorite profile list."""

    favorite_progress: Mapped['FavoriteListProgress | None'] = (
        orm.relationship(
            back_populates='user',
            cascade='all, delete-orphan',
            init=False,
            repr=False,
        )
    )
    """User progress in favorite list mode."""

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

class FavoriteListProgress(ModelBaseType):
    """Stores user progress in favorite list mode."""

    __tablename__ = 'favorite_list_progress'

    user_id: Mapped[int] = orm.mapped_column(
        sa.ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True,
        init=False,
    )
    user: Mapped[User] = orm.relationship(back_populates='favorite_progress')
    """Bot user that owns this record."""

    index: Mapped[int] = orm.mapped_column()
    """Favorite record positional index."""

    profile_id: Mapped[int] = orm.mapped_column()
    """Profile id that the user has added as favorite."""
