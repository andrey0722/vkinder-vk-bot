"""This module defines basic types that stores application data."""

import dataclasses
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


class User(ModelBaseType):
    """Represents one particular user of the bot."""

    __tablename__ = 'user'

    id: Mapped[int] = orm.mapped_column(primary_key=True)
    """User unique VK ID value."""

    state: Mapped[UserState] = orm.mapped_column(
        sa.Enum(UserState, name='userstate', metadata=ModelBaseType.metadata),
        default=UserState.NEW_USER,
    )
    """Current user state."""


@dataclasses.dataclass
class InputMessage:
    """Input message data from a user to a bot."""

    user: User
    text: str
