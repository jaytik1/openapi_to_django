import json
import os
import yaml
from django.core.management.base import BaseCommand, CommandError
from django.template import Context, Engine
from enum import Enum
from typing import Any, Mapping, Self


JSON_EXTENSIONS = [".json"]
YAML_EXTENSIONS = [".yaml", ".yml"]


class FileType(Enum):
    JSON = "json"
    YAML = "yaml"


class Command(BaseCommand):
    help = "Load a specified OpenAPI document"

    def add_arguments(self, parser):
        parser.add_argument("openapi-file", help="OpenAPI file")

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

        # arguments for writing urls.py entries
        parser.add_argument(
            "--urls-template",
            help="template file for rendering OpenAPI endpoints in urls.py",
            default=os.path.join("..", "templates", "urls.py-tpl"),
        )
        parser.add_argument(
            "--urls-target",
            help="urls.py file where the rendered URLs should be written",
            default="urls.py",
        )

    def handle(self, **options):
        openapi_file = options.pop("openapi-file")
        openapi_path = os.path.abspath(openapi_file)

        if not os.path.exists(openapi_path):
            raise CommandError(f"OpenAPI file {openapi_file} does not exist")

        openapi_file_name, openapi_file_extension = os.path.splitext(openapi_file)
        openapi_filetype: FileType | None = None

        parse_json = options.pop("parse_json")
        parse_yaml = options.pop("parse_yaml")

        # checks if the file type has been explicitly specified first
        if parse_json:
            openapi_filetype = FileType.JSON
        elif parse_yaml:
            openapi_filetype = FileType.YAML
        else:
            # attempts to identify a file type from the file extension
            if openapi_file_extension in JSON_EXTENSIONS:
                openapi_filetype = FileType.JSON
            elif openapi_file_extension in YAML_EXTENSIONS:
                openapi_filetype = FileType.YAML

        # parse the file according to the determined file type
        if openapi_filetype == FileType.JSON:
            openapi = self.parse_json(openapi_path)
        elif openapi_filetype == FileType.YAML:
            print("bean")
            openapi = self.parse_yaml(openapi_path)
        else:
            raise CommandError(
                "OpenAPI file type not determined, use -j or -y to parse as JSON or YAML"
            )

        urls_template_argument = options.pop("urls_template")
        urls_template_path = os.path.abspath(urls_template_argument)

        if not os.path.exists(urls_template_path):
            raise CommandError(
                f"urls.py template file {urls_template_path} does not exist"
            )

        # target urls.py file doesn't need to exist already, can write to a new one
        urls_target_argument = options.pop("urls_target")
        urls_target_path = os.path.abspath(urls_target_argument)

        urls_exists = False

        if os.path.exists(urls_target_path):
            urls_exists = True

        with open(urls_template_path, "r", encoding="utf-8") as urls_template_file:
            urls_template_string = urls_template_file.read()

        # converts the urls.py template file content to a renderable Template object
        urls_template = Engine().from_string(urls_template_string)

        context = Context(
            {"tags": ["ex1", "ex2", "ex3"], "urls_exists": urls_exists},
            autoescape=False,
        )
        rendered_urls = urls_template.render(context)

        with open(urls_target_path, "a", encoding="utf-8") as urls_file:
            urls_file.write(rendered_urls)

        print("Loaded URLs.")

    # TODO make a more precise return type definition
    def parse_json(self: Self, filepath: str) -> Mapping[str, Any] | list[Any]:
        """Parse a JSON file into a Python dictionary or list.

        Args:
            filepath: Path of the JSON file to be parsed.

        Returns:
            Python dictionary or list representing the JSON file.
        """
        with open(filepath, "r") as json_file:
            try:
                return json.load(json_file)
            except json.JSONDecodeError as e:
                print(f"error: problem when reading JSON file: {e}")
            except UnicodeDecodeError as e:
                print(f"error: problem when reading JSON file: {e}")

    # TODO make a more precise return type definition
    def parse_yaml(self: Self, filepath: str) -> Mapping[str, Any] | list[Any]:
        """Parse a YAML file into a Python dictionary or list.

        Args:
            filepath: Path of the YAML file to be parsed.

        Returns:
            Python dictionary or list representing the YAML file.
        """
        with open(filepath, "r") as yaml_file:
            try:
                return yaml.safe_load(yaml_file)
            except yaml.YAMLError as e:
                print(f"error: problem when reading YAML file: {e}")
