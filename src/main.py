import argparse
import datetime
import json
import os
import yaml
from pathlib import Path
from typing import Any, Mapping


INDENT_SPACES = 2
YAML_EXTENSIONS = [".yaml", ".yml"]


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("filepath", help="file path of the OpenAPI document")
    parser.add_argument(
        "-y",
        "--parse-yaml",
        help="specify that the given file should be parsed as YAML",
        action="store_true",
    )

    args = parser.parse_args()

    if args.parse_yaml:
        openapi = parse_yaml(args.filepath)
    elif os.path.splitext(args.filepath)[1] in YAML_EXTENSIONS:
        # parse file as YAML if the given file has a YAML extension
        openapi = parse_yaml(args.filepath)
    else:
        print("File type not determined, use -y to parse as YAML.")
        return

    write_json(openapi)
    print(openapi)


# TODO make a more precise return type definition
def parse_yaml(filepath: str) -> Mapping[str, Any]:
    """Parse a YAML file into a Python dictionary.

    Args:
        filepath: Path of the YAML file to be parsed.

    Returns:
        Python dictionary representing the YAML file.
    """
    try:
        with open(filepath) as yaml_file:
            try:
                return yaml.safe_load(yaml_file)
            except yaml.YAMLError as exc:
                print(exc)
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


def json_handle_value(value: Any):
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
