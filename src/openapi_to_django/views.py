"""Functions and variables related to the Django views.py file."""

import re
from dataclasses import dataclass
from pathlib import Path

from django.template import Context

from openapi_to_django.exceptions import ParameterError
from openapi_to_django.openapi import PathData
from openapi_to_django.utils import extract_path_param, get_tokens_from_uri


@dataclass
class DjangoView:
    """Data required to create a Django view function in views.py."""

    view_name: str  # name of the function in views.py
    params: dict[str, str]  # dict of view parameters and their types


def generate_views_context(
    paths_data: list[PathData],
    views_target_path: Path,
) -> Context:
    """
    Generate the template context for the Django views.py file.

    Args:
        paths_data: Data about each path in the OpenAPI document.
        views_target_path: Path where the views.py file should be written.

    Returns:
        Context object to be used by the views template.
    """
    views = []

    # generate a DjangoView object for each path
    for path_data in paths_data:
        tokens = get_tokens_from_uri(path_data.openapi_path)

        # validate that each path parameter is defined
        for token in tokens:
            param = extract_path_param(token)

            if param is not None and param not in path_data.path_params:
                msg = f"Error generating view context: path parameter {param} not defined!"
                raise ParameterError(msg)

        view_name = get_view_from_path(path_data.openapi_path)
        views.append(DjangoView(view_name, path_data.path_params))

    return Context(
        {"views": views, "views_exists": views_target_path.is_file()},
        autoescape=False,
    )


def get_view_from_path(path: str) -> str:
    """
    Generate a Django views.py function name from an OpenAPI path.

    Args:
        path: OpenAPI path string to be used.

    Returns:
        The name of a views function corresponding to the OpenAPI path.
    """
    tokens = get_tokens_from_uri(path)

    # remove braces from the path tokens name to generate the view name
    view_tokens = [re.sub(r"[\{\}]", "", token) for token in tokens]

    if len(view_tokens) == 0:
        return "index"

    return "_".join(view_tokens)  # generate the views.py function name
