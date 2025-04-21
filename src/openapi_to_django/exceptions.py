"""Custom exceptions used by OpenAPI to Django."""


class ParameterError(Exception):
    """Error related to OpenAPI parameters."""

    pass


class ReferenceObjectError(Exception):
    """Error related to OpenAPI reference objects."""

    pass
