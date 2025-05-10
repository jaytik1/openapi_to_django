"""Definitions of constants and enums used by OpenAPI to Django."""

from enum import Enum


class FileType(Enum):
    """Store consistent identifiers for OpenAPI file types."""

    JSON = "json"
    YAML = "yaml"
