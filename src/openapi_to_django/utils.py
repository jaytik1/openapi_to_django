"""UTILITY AND FILE OPERATIONS. SPLIT IN THE FUTURE."""

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
    split_slash = re.compile(r"(?<=\/)([^\/]+)")
    return split_slash.findall(path)
