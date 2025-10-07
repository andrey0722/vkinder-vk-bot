"""Program configuration parameters.

This module defines all external program parameters which affect
program operation.
"""

from pydantic import ValidationError
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

ConfigError = ValidationError
"""Error while reading program configuration."""


class Config(BaseSettings):
    """Project external parameters loaded from the environment.

    See .env.example file for variable description.
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    vk_token: str = 'vk1.a.VK_EXAMPLE_TOKEN'
    """VK community access token."""
