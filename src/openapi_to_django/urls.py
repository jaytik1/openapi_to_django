"""Functions and variables related to the Django urls.py file."""

from dataclasses import dataclass
from pathlib import Path

from django.template import Context

from openapi_to_django.exceptions import ParameterError
from openapi_to_django.openapi import PathData
from openapi_to_django.utils import extract_path_param, generate_relative_import, get_tokens_from_uri
from openapi_to_django.views import get_view_from_path


@dataclass
class DjangoPath:
    """Data required to create a Django path in urls.py."""

    url: str  # URL of the path, including any path parameters
    view_name: str  # name of the path's corresponding function in views.py


def generate_urls_context(
    paths_data: list[PathData],
    urls_target_path: Path,
    views_target_path: Path,
) -> Context:
    """
    Generate the template context for the Django urls.py file.

    Args:
        paths_data: Data about each path in the OpenAPI document.
        urls_target_path: Path where the urls.py file should be written.
        views_target_path: Path where the views.py file should be written.

    Returns:
        Context object to be used by the URLs template.
    """
    paths = []

    # generate a DjangoPath object for each path
    for path_data in paths_data:
        url = get_url_from_path(path_data.openapi_path, path_data.path_params)
        view_name = get_view_from_path(path_data.openapi_path)
        paths.append(DjangoPath(url, view_name))

    views_import = generate_relative_import(urls_target_path, views_target_path)

    return Context(
        {
            "paths": paths,
            "urls_exists": urls_target_path.is_file(),
            "views_name": views_target_path.stem,
            "views_import": views_import,
        },
        autoescape=False,
    )


def get_url_from_path(path: str, path_params: dict[str, str]) -> str:
    """
    Generate a Django path URL from an OpenAPI path.

    Args:
        path: OpenAPI path string to be used.
        path_params: Mapping of a path parameter's name to its type.

    Raises:
        ParameterError: Parameter name isn't defined.

    Returns:
        The Django URL corresponding to the OpenAPI path.
    """
    tokens = get_tokens_from_uri(path)

    url_tokens = []

    for token in tokens:
        param = extract_path_param(token)

        # continue if the current token isn't a path parameter
        if param is None:
            url_tokens.append(token)
            continue

        if param not in path_params:
            msg = f"Error generating URL: path parameter {param} not defined!"
            raise ParameterError(msg)

        param_type = path_params[param]
        url_tokens.append(f"<{param_type}:{param}>")

    return "/".join(url_tokens)  # generate the Django path URL
