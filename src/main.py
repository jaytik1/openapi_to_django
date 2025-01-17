import argparse
import os
import yaml
from typing import Any, Mapping


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


if __name__ == "__main__":
    main()
