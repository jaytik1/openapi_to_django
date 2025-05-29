"""Utility and file operations used by OpenAPI to Django."""

import re
from pathlib import Path


def get_tokens_from_uri(path: str) -> list[str]:
    """
    Split a URI by its slashes (/) to get each of its tokens.

    For example, "/example/{id}" should get split into tokens ["example", "{id}"].

    Args:
        path: URI to be split.

    Returns:
        A list of tokens present in the given URI.
    """
    if path[0] != "/":
        return []

    split_slash = re.compile(r"(?<=\/)([^\/]+)")
    return split_slash.findall(path)


def generate_relative_import(importing_path: Path, imported_path: Path) -> str:
    """
    Generate a relative import statement to import one file into another.

    Args:
        importing_path: Path for the file where the import statement should be used.
        imported_path: Path for the file being imported.

    Returns:
        Import statement for the imported file relative to the importing file.

    Raises:
        ValueError if the importing and imported paths are the same.
    """
    importing_path = importing_path.resolve()
    imported_path = imported_path.resolve()

    if importing_path == imported_path:
        msg = "Importing and imported paths are the same"
        raise ValueError(msg)

    importing_parts = list(importing_path.parts)
    imported_parts = list(imported_path.parts)

    # discard the common parent directories for both paths
    while len(importing_parts) > 0 and len(imported_parts) > 0 and importing_parts[0] == imported_parts[0]:
        importing_parts.pop(0)
        imported_parts.pop(0)

    if len(importing_parts) == 1 and len(imported_parts) == 1:
        # both files are in the same directory
        import_statement = f"import {imported_path.stem}"
    elif len(importing_parts) < len(imported_parts):
        # imported file is in a deeper directory than the importing file
        import_statement = f"from {'.'.join(imported_parts[:-1])} import {imported_path.stem}"
    elif len(importing_parts) >= len(imported_parts):
        # the importing file is in an equal-depth or deeper directory than the imported file
        import_statement = f"from {imported_path.parent.stem} import {imported_path.stem}"

    return import_statement


def extract_path_param(uri_token: str) -> str | None:
    """
    Extract an OpenAPI path parameter's name from a URI token.

    For example, if the token "{id}" is given, it would extract "id".

    Args:
        uri_token: URI token to be parsed.

    Returns:
        The path parameter's name if the token is an OpenAPI path parameter,
        None otherwise.
    """
    extract_parameter = re.compile(r"(?<=\{)(.+)(?=\})")
    parameter_list = extract_parameter.findall(uri_token)

    # continue if the current token isn't a path parameter
    if len(parameter_list) != 1:
        return None

    return str(parameter_list[0])
