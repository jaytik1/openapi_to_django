import argparse
import datetime
import json
import os
import yaml
from pathlib import Path
from typing import Any, Mapping


INDENT_SPACES = 2
JSON_EXTENSIONS = [".json"]
YAML_EXTENSIONS = [".yaml", ".yml"]


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("filepath", help="file path of the OpenAPI document")
    parser.add_argument(
        "-c",
        "--convert",
        help="convert the given file from YAML to JSON or vice versa",
        action="store_true",
    )

    # arguments for specifying the file type
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

    # checks if the filetype has been explicitly specified first
    if args.parse_json:
        openapi = parse_json(args.filepath)
    elif args.parse_yaml:
        openapi = parse_yaml(args.filepath)
    else:
        # attempts to identify a filetype from the file extension
        if file_extension in JSON_EXTENSIONS:
            openapi = parse_json(args.filepath)
        elif file_extension in YAML_EXTENSIONS:
            openapi = parse_yaml(args.filepath)
        else:
            print("File type not determined, use -j or -y to parse as JSON or YAML.")
            return

    if args.convert:
        # convert YAML file to JSON file with the same file name
        write_json(openapi, file_name + JSON_EXTENSIONS[0])

    print(openapi)


# TODO make a more precise return type definition
def parse_json(filepath: str) -> Mapping[str, Any] | list[Any]:
    try:
        with open(filepath, "r") as json_file:
            try:
                return json.load(json_file)
            except json.JSONDecodeError as e:
                print(f"Error reading JSON file: {e}")
            except UnicodeDecodeError as e:
                print(f"Error reading JSON file: {e}")
    except FileNotFoundError:
        print(f"File {filepath} not found.")


# TODO make a more precise return type definition
def parse_yaml(filepath: str) -> Mapping[str, Any] | list[Any]:
    """Parse a YAML file into a Python dictionary.

    Args:
        filepath: Path of the YAML file to be parsed.

    Returns:
        Python dictionary representing the YAML file.
    """
    try:
        with open(filepath, "r") as yaml_file:
            try:
                return yaml.safe_load(yaml_file)
            except yaml.YAMLError as e:
                print(f"Error reading YAML file: {e}")
    except FileNotFoundError:
        print(f"File {filepath} not found.")


# TODO make a more precise data type definition
def write_json(data: Mapping[str, Any], filepath: str = "file.json") -> None:
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


if __name__ == "__main__":
    main()
