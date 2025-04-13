"""Definitions of constants and enums used by OpenAPI to Django."""

from enum import Enum

# maps the OpenAPI path parameter types to Django path parameter types
OPENAPI_DJANGO_TYPE_MAP = {"number": "int", "integer": "int", "string": "str"}
DEFAULT_DJANGO_TYPE = "str"

JSON_EXTENSIONS = [".json"]
YAML_EXTENSIONS = [".yaml", ".yml"]


class FileType(Enum):
    """Store consistent identifiers for OpenAPI file types."""

    JSON = "json"
    YAML = "yaml"
