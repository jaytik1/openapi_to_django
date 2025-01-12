import argparse
import os


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
        parse_yaml(args.filepath)
    elif os.path.splitext(args.filepath)[1] in YAML_EXTENSIONS:
        # parse file as YAML if the given file has a YAML extension
        parse_yaml(args.filepath)
    else:
        print("File type not determined, use -y to parse as YAML.")


def parse_yaml(filepath: str) -> None:
    print(filepath)


if __name__ == "__main__":
    main()
