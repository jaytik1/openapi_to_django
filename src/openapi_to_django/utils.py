"""Utility and file operations used by OpenAPI to Django."""

import re
from pathlib import Path

from django.template import Context, Engine


def write_file_from_template(target_path: Path, template_path: Path, context: Context) -> None:
    """
    Render a template and its context and write to a specified file path.

    Args:
        target_path: Path where the rendered content should be written.
        template_path: Path to the template.
        context: Context to be used by the template.
    """
    with template_path.open() as template_file:
        template_string = template_file.read()

    # convert the template file content to a renderable Template object
    template = Engine().from_string(template_string)

    rendered_file = template.render(context)

    with target_path.open("a") as target_file:
        target_file.write(rendered_file)


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
    if importing_path.resolve().absolute() == imported_path.resolve().absolute():
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
