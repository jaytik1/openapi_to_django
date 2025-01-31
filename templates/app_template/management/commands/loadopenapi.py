import json
import os
import re
import yaml
from django.core.management.base import BaseCommand, CommandError
from django.template import Context, Engine
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Self


JSON_EXTENSIONS = [".json"]
YAML_EXTENSIONS = [".yaml", ".yml"]

# maps the OpenAPI parameter types to Django parameter types
OPENAPI_DJANGO_PATH_MAP = {"number": "int", "integer": "int", "string": "str"}
DEFAULT_DJANGO_PATH_TYPE = "str"


class FileType(Enum):
    JSON = "json"
    YAML = "yaml"


@dataclass
class Url:
    """Stores URL data in a structured way."""

    path: str
    view: str  # name of the URL's function in views.py


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

        urls_target_argument = options.pop("urls_target")
        urls_target_path = os.path.abspath(urls_target_argument)

        # target urls.py file doesn't need to exist already, can write to a new one
        urls_exists = os.path.exists(urls_target_path)

        with open(urls_template_path, "r", encoding="utf-8") as urls_template_file:
            urls_template_string = urls_template_file.read()

        # convert the urls.py template file content to a renderable Template object
        urls_template = Engine().from_string(urls_template_string)

        # convert OpenAPI URLs to Django URLs
        urls = self.openapi_to_django_urls(openapi)

        context = Context(
            {"urls": urls, "urls_exists": urls_exists},
            autoescape=False,
        )
        rendered_urls = urls_template.render(context)

        with open(urls_target_path, "a", encoding="utf-8") as urls_file:
            urls_file.write(rendered_urls)

        print("Loaded URLs.")

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

    def openapi_to_django_urls(
        self: Self, openapi: Mapping[str, Any] | list[Any]
    ) -> list[Url]:
        """Converts each URL present in an OpenAPI document into the Django URL format.

        Args:
            openapi: Python representation of an OpenAPI document.

        Returns:
            A list of Url dataclass objects to be passed to the template.

        Raises:
            Exception: Path parameter couldn't be generated.
        """

        urls = []

        for path_name, path_content in openapi["paths"].items():
            # gets all path parameters defined in the OpenAPI endpoint
            try:
                endpoint_params = self.get_endpoint_path_params(path_content)
            except Exception as exc:
                print(f"Couldn't get path parameters for path {path_name}: {exc}")
                continue

            # splits a path by "/" to get tokens
            # e.g. gets ["example", "{id}"] from "/example/{id}"
            split_slash = re.compile("(?<=\/)([^\/]+)")
            tokens = split_slash.findall(path_name)

            # attempt to convert path params to the Django format
            try:
                path_tokens = [
                    self.openapi_to_django_path_param(token, endpoint_params)
                    for token in tokens
                ]
            except Exception as exc:
                print(f"Couldn't generate Django path param: {exc}")
                continue

            # remove braces from token to generate view name
            view_tokens = [re.sub("[\{\}]", "", token) for token in tokens]

            path = "/".join(path_tokens)  # generate the Django path URL
            view = "_".join(view_tokens)  # generate the views.py function name
            urls.append(Url(path, view))

        return urls

    def get_endpoint_path_params(
        self: Self, endpoint: Mapping[str, Any]
    ) -> Mapping[str, str]:
        """Get all path parameters contained in an OpenAPI endpoint.

        Args:
            endpoint: OpenAPI endpoint object to be parsed.

        Returns:
            A dictionary mapping path parameter names to their types.

        Raises:
            Exception: There is a conflicting path parameter.
            KeyError: A required key doesn't exist.
        """
        params = {}

        # get path parameters from the path object
        if "parameters" in endpoint:
            self.parse_path_params(endpoint["parameters"], params)

        # get path parameters from each of the path's operation objects
        for operation_content in endpoint.values():
            if "parameters" in operation_content:
                self.parse_path_params(operation_content["parameters"], params)

        return params

    def parse_path_params(
        self: Self,
        params_list: list[Mapping[str, Any]],
        current_params: Mapping[str, str],
    ) -> None:
        """
        Parse a list of OpenAPI parameter obejcts to get their names and types.
        Catch any conflicting parameters (same name but different type).

        Args:
            params_list: List of OpenAPI parameter objects.
            current_params: A reference to an existing mapping of parameters to types.

        Raises:
            Exception: Raised if there is a conflicting path parameter.
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
                raise Exception(f"Conflicting parameter type: {param_name}")

    def openapi_to_django_path_param(
        self: Self, token: str, current_params: Mapping[str, str]
    ):
        """
        Convert an OpenAPI path parameter to a Django path parameter.
        For example, converts "{id}" to "<int:id>".

        Args:
            token: OpenAPI path parameter or other path token.
            current_params: List of path parameter definitions from the OpenAPI document.

        Raises:
            Exception: A path parameter type isn't defined in the OpenAPI document.

        Returns:
            Parameter in the Django path parameter URL format,
            or the given token if it isn't a path parameter.
        """
        # attempts to extract parameter name from the token
        # e.g. gets ["id"] from "{id}"
        extract_parameter = re.compile("(?<=\{)(.+)(?=\})")
        parameter_list = extract_parameter.findall(token)

        # return if the current token isn't a path parameter
        if len(parameter_list) != 1:
            return token

        param_name = parameter_list[0]

        if param_name not in current_params:
            raise Exception(f"Parameter name {param_name} not defined!")

        param_type = current_params[param_name]

        # convert the OpenAPI type to a Django type
        if param_type in OPENAPI_DJANGO_PATH_MAP:
            param_type = OPENAPI_DJANGO_PATH_MAP[param_type]
        else:
            param_type = DEFAULT_DJANGO_PATH_TYPE

        return f"<{param_type}:{param_name}>"
