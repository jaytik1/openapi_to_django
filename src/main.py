import argparse
import datetime
import json
import os
import subprocess
import yaml
from enum import Enum
from pathlib import Path
from typing import Any, Mapping
from django.core.management import call_command
from django.core.management.base import CommandError

INDENT_SPACES = 2
JSON_EXTENSIONS = [".json"]
YAML_EXTENSIONS = [".yaml", ".yml"]

DEFAULT_PROJECT_NAME = "openapi_django"
DEFAULT_APP_NAME = DEFAULT_PROJECT_NAME + "_app"


class FileType(Enum):
    JSON = "json"
    YAML = "yaml"


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("filepath", help="file path of the OpenAPI document")
    parser.add_argument(
        "-c",
        "--convert",
        help="convert the given file from YAML to JSON or vice versa",
        action="store_true",
    )

    # arguments for setting up Django
    parser.add_argument(
        "-p",
        "--project-name",
        help="name of the Django project being created",
        default=DEFAULT_PROJECT_NAME,
    )
    parser.add_argument(
        "-a",
        "--app-name",
        help="name of the Django app being created",
        default=DEFAULT_APP_NAME,
    )

    # arguments for specifying the OpenAPI document file type
    group_filetype = parser.add_argument_group(
        "specify filetype", "Specify the filetype of the given file."
    )
    exclusive_group_filetype = group_filetype.add_mutually_exclusive_group()
    exclusive_group_filetype.add_argument(
        "-j",
        "--parse-json",
        help="specify that the given file should be parsed as JSON",
        action="store_true",
    )
    exclusive_group_filetype.add_argument(
        "-y",
        "--parse-yaml",
        help="specify that the given file should be parsed as YAML",
        action="store_true",
    )

    args = parser.parse_args()

    file_name, file_extension = os.path.splitext(args.filepath)
    filetype: FileType | None = None

    # checks if the file type has been explicitly specified first
    if args.parse_json:
        filetype = FileType.JSON
    elif args.parse_yaml:
        filetype = FileType.YAML
    else:
        # attempts to identify a file type from the file extension
        if file_extension in JSON_EXTENSIONS:
            filetype = FileType.JSON
        elif file_extension in YAML_EXTENSIONS:
            filetype = FileType.YAML

    # parse the file according to the determined file type
    if filetype == FileType.JSON:
        openapi = parse_json(args.filepath)
    elif filetype == FileType.YAML:
        openapi = parse_yaml(args.filepath)
    else:
        parser.print_help()
        print("error: file type not determined, use -j or -y to parse as JSON or YAML")
        return

    if args.convert:
        # write to a YAML or JSON file with the same file name as the input
        if filetype == FileType.JSON:
            write_yaml(openapi, file_name + YAML_EXTENSIONS[0])
        elif filetype == FileType.YAML:
            write_json(openapi, file_name + JSON_EXTENSIONS[0])

    # attempt to create a new Django project
    try:
        call_command("startproject", args.project_name)
    except CommandError as e:
        print(f"error: something went wrong when creating the Django project: {e}")
        return

    # attempt to create a new app in the new Django project
    app_directory = os.path.join(args.project_name, args.app_name)

    try:
        os.mkdir(app_directory)
    except FileExistsError:
        print("error: app folder could not be made as it already exists")
        return
    except FileNotFoundError:
        print(
            "error: app folder could not be made as its parent directory doesn't exist"
        )
        return

    try:
        call_command("startapp", args.app_name, app_directory)
    except CommandError as e:
        print(f"error: something went wrong when creating the Django app: {e}")
        return

    print(openapi)


# TODO make a more precise return type definition
def parse_json(filepath: str) -> Mapping[str, Any] | list[Any]:
    """Parse a JSON file into a Python dictionary or list.

    Args:
        filepath: Path of the JSON file to be parsed.

    Returns:
        Python dictionary or list representing the JSON file.
    """
    try:
        with open(filepath, "r") as json_file:
            try:
                return json.load(json_file)
            except json.JSONDecodeError as e:
                print(f"error: problem when reading JSON file: {e}")
            except UnicodeDecodeError as e:
                print(f"error: problem when reading JSON file: {e}")
    except FileNotFoundError:
        print(f"error: file {filepath} not found")


# TODO make a more precise return type definition
def parse_yaml(filepath: str) -> Mapping[str, Any] | list[Any]:
    """Parse a YAML file into a Python dictionary or list.

    Args:
        filepath: Path of the YAML file to be parsed.

    Returns:
        Python dictionary or list representing the YAML file.
    """
    try:
        with open(filepath, "r") as yaml_file:
            try:
                return yaml.safe_load(yaml_file)
            except yaml.YAMLError as e:
                print(f"error: problem when reading YAML file: {e}")
    except FileNotFoundError:
        print(f"error: file {filepath} not found")


# TODO make a more precise data type definition
def write_json(
    data: Mapping[str, Any] | list[Any], filepath: str = "file.json"
) -> None:
    """Take an object, convert it to JSON and save it to a JSON file.

    Args:
        data: Python dictionary or list data to be saved as JSON.
        filepath: Path of the JSON file that should be written.

    Raises:
        OSError: Attempted to overwrite an existing file.
        TypeError: Given data is not JSON serialisable.
    """
    filepath_object = Path(filepath)

    if filepath_object.exists():
        raise OSError(f"File already exists at given filepath: {filepath}.")

    with open(filepath_object, "w") as json_file:
        try:
            json.dump(data, json_file, indent=INDENT_SPACES, default=json_handle_value)
        except TypeError as e:
            # delete partially-written file if there is an error
            filepath_object.unlink()
            raise TypeError(e)


def json_handle_value(value: Any) -> str:
    """Attempt to convert a non-serialisable value into a JSON serialisable one.

    Args:
        value: Non-serialisable value to be converted.

    Raises:
        TypeError: Given value is not possible to be JSON serialisable.

    Returns:
        Value in a JSON serialisable form.
    """
    if isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
        # converts date and datetime objects to an ISO 8601 string
        return value.isoformat()
    else:
        raise TypeError(f"Value {value} is not JSON serialisable.")


# TODO make a more precise data type definition
def write_yaml(
    data: Mapping[str, Any] | list[Any], filepath: str = "file.yaml"
) -> None:
    """Take an object, convert it to YAML and save it to a YAML file.

    Args:
        data: Python dictionary or list data to be saved as YAML.
        filepath: Path of the YAML file that should be written.

    Raises:
        OSError: Attempted to overwrite an existing file.
    """
    filepath_object = Path(filepath)

    if filepath_object.exists():
        raise OSError(f"File already exists at given filepath: {filepath}.")

    with open(filepath_object, "w") as yaml_file:
        yaml.dump(data, yaml_file, indent=INDENT_SPACES, sort_keys=False)


if __name__ == "__main__":
    main()
