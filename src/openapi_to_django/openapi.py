"""Functions and variables related to OpenAPI documents."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias

import yaml
from django.core.management.base import CommandError

from openapi_to_django.definitions import (
    DEFAULT_DJANGO_TYPE,
    JSON_EXTENSIONS,
    OPENAPI_DJANGO_TYPE_MAP,
    YAML_EXTENSIONS,
    FileType,
)
from openapi_to_django.exceptions import ParameterError, ReferenceObjectError
from openapi_to_django.utils import get_tokens_from_uri

OpenApi: TypeAlias = dict[str, Any]


@dataclass
class PathData:
    """Data about an OpenAPI path."""

    openapi_path: str  # path URL as stored in the OpenAPI document
    path_params: dict[str, str]  # dict of path parameters and their Django types


def read_openapi_file(file_type: str | None, openapi_path: Path) -> Any:
    """
    Read an OpenAPI document from a given file.

    Determine the file type of the document and parse accordingly,
    then resolve any reference objects in the OpenAPI document.

    Args:
        file_type: Optional specifier for the OpenAPI document file type.
        openapi_path: File path to the OpenAPI document.

    Raises:
        CommandError: File type of the OpenAPI docuemnt couldn't be determined.

    Returns:
        OpenAPI document in its Python representation.
    """
    if file_type:
        # set file type to the manually specified one if given
        openapi_file_type = file_type
    # attempts to identify a file type from the file extension
    elif openapi_path.suffix in JSON_EXTENSIONS:
        openapi_file_type = FileType.JSON.value
    elif openapi_path.suffix in YAML_EXTENSIONS:
        openapi_file_type = FileType.YAML.value

    # attempt to parse the file according to the determined file type
    if openapi_file_type == FileType.JSON.value:
        with openapi_path.open() as json_file:
            openapi = json.load(json_file)
    elif openapi_file_type == FileType.YAML.value:
        with openapi_path.open() as yaml_file:
            openapi = yaml.safe_load(yaml_file)
    else:
        msg = "OpenAPI file type not determined, use --file-type to specify"
        raise CommandError(msg)

    # resolve all reference objects in the OpenAPI document
    return resolve_ref_objects(openapi, openapi)


def get_paths_data(openapi: OpenApi) -> list[PathData]:
    """
    Get required data for all paths in an OpenAPI document.

    Args:
        openapi: Python representation of an OpenAPI document.

    Returns:
        List of PathData objects gathered from the OpenAPI document.
    """
    paths_data = []

    for path_name, path_content in openapi["paths"].items():
        path_params: dict[str, str] = {}

        # get path parameters from the path object
        if "parameters" in path_content:
            parse_path_params(path_content["parameters"], path_params)

        # get path parameters from each of the path's operation objects
        for operation_content in path_content.values():
            if "parameters" in operation_content:
                parse_path_params(operation_content["parameters"], path_params)

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
) -> None:
    """
    Parse a list of OpenAPI parameter objects to get their names and types.

    Ignores any parameters which aren't path parameters.

    Args:
        params_list: List of OpenAPI parameter objects.
        current_params: Existing mapping of parameters to types,
        which is checked for conflicts and used to store new path parameters.

    Raises:
        ParameterError: There is a conflicting path parameter (same name but different type).
    """
    for parameter in params_list:
        if parameter["in"] != "path":
            # ignore non-path parameters
            continue

        param_name = parameter["name"]
        param_type = parameter["schema"]["type"]

        if param_name not in current_params:
            current_params[param_name] = param_type
        elif current_params[param_name] != param_type:
            msg = f"Conflicting parameter type: {param_name}"
            raise ParameterError(msg)


def resolve_ref_objects(current: Any, base_dict: dict[str, Any]) -> Any:
    """
    Recursively resolve all reference objects (if any) inside a given variable.

    Args:
        current: Current variable to be resolved.
        base_dict: Dictionary containing the referenced URIs.

    Raises:
        ReferenceObjectError: Reference object format is invalid or its target doesn't exist.

    Returns:
        The object with all reference objects inside resolved.
    """
    # return the current variable if isn't a dictionary or a list (base case)
    if not isinstance(current, dict) and not isinstance(current, list):
        return current

    # resolve all items in the list
    if isinstance(current, list):
        return [resolve_ref_objects(item, base_dict) for item in current]

    # resolve each dictionary value if the dictionary doesn't contain a ref
    if "$ref" not in current:
        return {key: resolve_ref_objects(val, base_dict) for key, val in current.items()}

    # raise an exception if the dictionary contains other data as well as a ref
    if len(current) != 1:
        msg = f"Dictionary contains other data as well as a reference object: {current}"
        raise ReferenceObjectError(msg)

    ref_uri = current["$ref"]

    # references to parts of the same document must start with #
    if ref_uri[0] != "#":
        msg = f"Reference object URI doesn't start with '#': {current}"
        raise ReferenceObjectError(msg)

    tokens = get_tokens_from_uri(ref_uri)

    try:
        result = traverse_nested_dictionary(base_dict, tokens)
    except KeyError as e:
        msg = f"Reference object location doesn't exist! {current}"
        raise ReferenceObjectError(msg) from e

    return resolve_ref_objects(result, base_dict)


def traverse_nested_dictionary(dictionary: dict, keys: list[str]) -> dict:
    """
    Recursively traverse a nested dictionary using a list of keys.

    Args:
        dictionary: Dictionary to be traversed.
        keys: List of keys that should exist in the nested dictionary.

    Raises:
        KeyError: A given key wasn't found in its nested dict.

    Returns:
        The final key's value in its nested dict.
    """
    if len(keys) == 0:
        return dictionary

    key = keys.pop(0)

    if key not in dictionary:
        msg = f"Key {key} not found in dictionary {dictionary}."
        raise KeyError(msg)

    return traverse_nested_dictionary(dictionary[key], keys)
