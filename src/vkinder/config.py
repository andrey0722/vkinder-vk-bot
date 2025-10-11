"""Program configuration parameters.

This module defines all external program parameters which affect
program operation.
"""

from pydantic import Field
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from .exceptions import VkinderError
from .log import get_logger


class ConfigError(VkinderError):
    """Error while reading program configuration."""


class ConfigBase(BaseSettings):
    """Base class for other settings classes."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    def __init__(self):
        """Initialize a config object.

        Raises:
            ConfigError: Error while reading program configuration.
        """
        try:
            super().__init__()
        except ValidationError as e:
            logger = get_logger(self)
            logger.critical('Read config error: %s', e)
            raise ConfigError(e) from e


class VkConfig(ConfigBase):
    """External parameters for VK API connection loaded from the environment.

    See .env.example file for variable description.
    """

    vk_community_token: str = 'vk1.a.VK_EXAMPLE_TOKEN'
    """VK community access token."""

    vk_user_token: str = 'vk1.a.VK_EXAMPLE_TOKEN'
    """VK user access token."""


class DatabaseConfig(ConfigBase):
    """External parameters for DB connection loaded from the environment.

    See .env.example file for variable description.
    """

    driver: str = Field(alias='DB_DRIVER', default='postgresql+psycopg2')
    """Database driver name to use when connecting to DB."""

    host: str = Field(alias='DB_HOST', default='localhost')
    """DB hostname or IP address."""

    port: int = Field(alias='DB_PORT', default=5432)
    """DB port number."""

    database: str = Field(alias='DB_NAME', default='vkinder_vk_bot')
    """Name of existing database."""

    user: str = Field(alias='DB_USER', default='postgres')
    """Database user name with rights to create tables in `database`."""

    password: str = Field(alias='DB_PASS', default='postgres')
    """Password for the `user`."""

    clear_data: bool = False
    """Delete all data on start.

    `True` to delete all existing bot data on launch (fresh start).
    `False` to keep existing data and use it in operation.
    """
