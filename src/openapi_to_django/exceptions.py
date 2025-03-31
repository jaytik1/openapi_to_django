"""Custom exceptions used by OpenAPI to Django."""


class ParameterError(Exception):
    """Use for errors relating to OpenAPI parameters."""

    pass


class ReferenceObjectError(Exception):
    """Use for errors relating to OpenAPI reference objects."""

    pass
