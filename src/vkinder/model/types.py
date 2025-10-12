"""This module defines basic types that stores application data."""

import enum

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import Mapped


class ModelBaseType(orm.MappedAsDataclass, orm.DeclarativeBase):
    """Base class for all types used by model."""


@enum.unique
class UserState(enum.StrEnum):
    """Current state for a particular user."""

    NEW_USER = enum.auto()
    MAIN_MENU = enum.auto()
    SEARCHING = enum.auto()


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

    first_name: Mapped[str | None] = orm.mapped_column(
        sa.String(64),
        default=None,
    )
    """User first name."""

    last_name: Mapped[str | None] = orm.mapped_column(
        sa.String(64),
        default=None,
    )
    """User last name."""

    sex: Mapped[Sex] = orm.mapped_column(
        sa.Enum(Sex, name='sex', metadata=ModelBaseType.metadata),
        default=Sex.NOT_KNOWN,
    )
    """User specified sex."""

    birthday: Mapped[str | None] = orm.mapped_column(
        sa.String(10),
        default=None,
    )
    """User specified birthday."""

    city_id: Mapped[str | None] = orm.mapped_column(default=None)
    """User specified city ID."""

    city: Mapped[str | None] = orm.mapped_column(
        sa.String(64),
        default=None,
    )
    """User specified city."""

    state: Mapped[UserState] = orm.mapped_column(
        sa.Enum(UserState, name='userstate', metadata=ModelBaseType.metadata),
        default=UserState.NEW_USER,
    )
    """Current user state."""
