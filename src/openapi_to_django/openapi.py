"""Functions and variables related to OpenAPI documents."""

from dataclasses import dataclass
from typing import Any, TypeAlias

from openapi_to_django.exceptions import ParameterError

OpenApi: TypeAlias = dict[str, Any]

OPENAPI_DJANGO_TYPE_MAP = {"number": "int", "integer": "int", "string": "str"}
DEFAULT_DJANGO_TYPE = "str"


@dataclass
class PathData:
    """Data about an OpenAPI path."""

    openapi_path: str  # path URL as stored in the OpenAPI document
    path_params: dict[str, str]  # dict of path parameters and their Django types


def get_paths_data(openapi: OpenApi) -> list[PathData]:
    """
    Get required data for all paths in an OpenAPI document.

    Args:
        openapi: Python representation of an OpenAPI document.

    Returns:
        List of PathData objects gathered from the OpenAPI document.
    """
    paths_data: list[PathData] = []

    if "paths" not in openapi:
        return paths_data

    for path_name, path_content in openapi["paths"].items():
        path_params: dict[str, str] = {}

        # get path parameters from the path object
        if "parameters" in path_content:
            path_params = path_params | parse_path_params(path_content["parameters"], path_params)

        # get path parameters from each of the path's operation objects
        for operation_content in path_content.values():
            if "parameters" in operation_content:
                path_params = path_params | parse_path_params(operation_content["parameters"], path_params)

        # convert each of the parameter types from OpenAPI to Django
        django_path_params = {
            param_name: OPENAPI_DJANGO_TYPE_MAP.get(param_type, DEFAULT_DJANGO_TYPE)
            for (param_name, param_type) in path_params.items()
        }

        paths_data.append(PathData(path_name, django_path_params))

    return paths_data


def parse_path_params(
    params_list: list[dict[str, Any]],
    current_params: dict[str, str],
) -> dict[str, str]:
    """
    Parse a list of OpenAPI parameter objects to get their names and types.

    Ignores any parameters which aren't path parameters.

    Args:
        params_list: List of OpenAPI parameter objects.
        current_params: Existing mapping of parameters to types,
        which is checked for conflicts.

    Returns:
        Mapping of the parameters in the given list to their types.

    Raises:
        ParameterError: There is a conflicting path parameter (same name but different type).
    """
    result_params: dict[str, str] = {}

    for parameter in params_list:
        if parameter["in"] != "path":
            # ignore non-path parameters
            continue

        param_name = parameter["name"]
        param_type = parameter["schema"]["type"]

        if param_name in result_params:
            msg = f'Path parameter "{param_name}" defined multiple times in the same scope.'
            raise ParameterError(msg)

        if param_name not in current_params:
            result_params[param_name] = param_type
        elif current_params[param_name] != param_type:
            msg = f'Conflicting types given for path parameter "{param_name}" ({param_type} vs {current_params[param_name]})'
            raise ParameterError(msg)

    return result_params
