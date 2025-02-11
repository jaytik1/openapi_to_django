import json
import re
import yaml
from django.core.management.base import BaseCommand, CommandError
from django.template import Context, Engine
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Self


JSON_EXTENSIONS = [".json"]
YAML_EXTENSIONS = [".yaml", ".yml"]


class FileType(Enum):
    JSON = "json"
    YAML = "yaml"


@dataclass
class DjangoPath:
    """Stores the data required to create a Django path."""

    url: str  # URL of the path, including any path parameters
    view: str  # name of the path's corresponding function in views.py
    params: Mapping[str, str]  # list of path parameters and their types


class Command(BaseCommand):
    help = "Generate Django code by loading a specified OpenAPI document"

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

        # arguments for rendering the Django urls.py file
        parser.add_argument(
            "--urls-template",
            help="template file for rendering OpenAPI endpoints in urls.py",
            required=True,
        )
        parser.add_argument(
            "--urls-target",
            help="file where the generated Django URLs should be written",
            default="urls.py",
        )

        # arguments for rendering the Django views.py file
        parser.add_argument(
            "--views-template",
            help="template file for rendering functions in views.py",
            required=True,
        )
        parser.add_argument(
            "--views-target",
            help="file where the generated Django view functions should be written",
            default="views.py",
        )

    def handle(self, **options):
        openapi_path = Path(options.pop("openapi-file")).resolve()
        if not openapi_path.is_file():
            raise CommandError(f"OpenAPI file {openapi_path} does not exist")

        urls_template_path = Path(options.pop("urls_template")).resolve()
        if not urls_template_path.is_file():
            raise CommandError(
                f"urls.py template file {urls_template_path} does not exist"
            )

        views_template_path = Path(options.pop("views_template")).resolve()
        if not views_template_path.is_file():
            raise CommandError(
                f"views.py template file {views_template_path} does not exist"
            )

        urls_target_path = Path(options.pop("urls_target")).resolve()
        if not urls_target_path.parent.is_dir():
            # create directory for the URLs target if it doesn't exist
            urls_target_path.parent.mkdir(parents=True)

        views_target_path = Path(options.pop("views_target")).resolve()
        if not views_target_path.parent.is_dir():
            # create directory for the views target if it doesn't exist
            views_target_path.parent.mkdir(parents=True)

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
            if openapi_path.suffix in JSON_EXTENSIONS:
                openapi_filetype = FileType.JSON
            elif openapi_path.suffix in YAML_EXTENSIONS:
                openapi_filetype = FileType.YAML

        # attempt to parse the file according to the determined file type
        if openapi_filetype == FileType.JSON:
            with open(openapi_path, "r") as json_file:
                openapi = json.load(json_file)
        elif openapi_filetype == FileType.YAML:
            with open(openapi_path, "r") as yaml_file:
                openapi = yaml.safe_load(yaml_file)
        else:
            raise CommandError(
                "OpenAPI file type not determined, use -j or -y to parse as JSON or YAML"
            )

        # convert OpenAPI paths to Django paths
        paths = self.openapi_to_django_paths(openapi)

        # render Django urls.py file

        with open(urls_template_path, "r") as urls_template_file:
            urls_template_string = urls_template_file.read()

        # convert the urls.py template file content to a renderable Template object
        urls_template = Engine().from_string(urls_template_string)

        views_import = self.generate_views_import(urls_target_path, views_target_path)

        urls_context = Context(
            {
                "paths": paths,
                "urls_exists": urls_target_path.is_file(),
                "views_name": views_target_path.stem,
                "views_import": views_import,
            },
            autoescape=False,
        )
        rendered_urls = urls_template.render(urls_context)

        with open(urls_target_path, "a") as urls_file:
            urls_file.write(rendered_urls)

        print(f"Loaded OpenAPI paths to {urls_target_path}.")

        # render Django views.py file

        with open(views_template_path, "r") as views_template_file:
            views_template_string = views_template_file.read()

        # convert the views.py template file content to a renderable Template object
        views_template = Engine().from_string(views_template_string)

        # generate Django view functions from the OpenAPI document
        # TODO

        views_context = Context(
            {"paths": paths, "views_exists": views_target_path.is_file()},
            autoescape=False,
        )
        rendered_views = views_template.render(views_context)

        with open(views_target_path, "a") as views_file:
            views_file.write(rendered_views)

        print(f"Wrote generated view functions to {views_target_path}.")

    def openapi_to_django_paths(
        self: Self, openapi: Mapping[str, Any] | list[Any]
    ) -> list[DjangoPath]:
        """Converts each path present in an OpenAPI document into the Django path format.

        Args:
            openapi: Python representation of an OpenAPI document.

        Returns:
            A list of DjangoPath dataclass objects to be passed to the template.

        Raises:
            Exception: Path parameter couldn't be generated.
        """

        paths = []

        for path_name, path_content in openapi["paths"].items():
            # gets all path parameters defined in the OpenAPI path object
            try:
                openapi_path_params = self.get_openapi_path_params(path_content)
            except Exception as exc:
                print(f"Couldn't get path parameters for path {path_name}: {exc}")
                continue

            # convert each of the parameter types from OpenAPI to Django
            django_path_params = {
                param_name: self.openapi_to_django_type(param_type)
                for (param_name, param_type) in openapi_path_params.items()
            }

            # splits a path by "/" to get tokens
            # e.g. gets ["example", "{id}"] from "/example/{id}"
            split_slash = re.compile("(?<=\/)([^\/]+)")
            tokens = split_slash.findall(path_name)

            # attempt to convert parameters in the OpenAPI URL to the Django format
            try:
                url_tokens = [
                    self.openapi_to_django_path_param(token, django_path_params)
                    for token in tokens
                ]
            except Exception as exc:
                print(f"Couldn't generate Django path param: {exc}")
                continue

            # remove braces from token to generate view name
            view_tokens = [re.sub("[\{\}]", "", token) for token in tokens]

            url = "/".join(url_tokens)  # generate the Django path URL
            view = "_".join(view_tokens)  # generate the views.py function name
            paths.append(DjangoPath(url, view, django_path_params))

        return paths

    def get_openapi_path_params(
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
        Raise for any conflicting parameters (same name but different type).
        Ignores any parameters which aren't path parameters.

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

        return f"<{param_type}:{param_name}>"

    def openapi_to_django_type(self: Self, param_type: str) -> str:
        """Convert an OpenAPI type to its equivalent Django type.

        Args:
            param_type: Name of the OpenAPI type to be converted.

        Returns:
            Name of the equivalent Django type, or a default type if not found.
        """
        # maps the OpenAPI path parameter types to Django path parameter types
        OPENAPI_DJANGO_TYPE_MAP = {"number": "int", "integer": "int", "string": "str"}

        # sets a default value for the type, used if it isn't recognised
        DEFAULT_DJANGO_TYPE = "str"

        return (
            OPENAPI_DJANGO_TYPE_MAP[param_type]
            if param_type in OPENAPI_DJANGO_TYPE_MAP
            else DEFAULT_DJANGO_TYPE
        )

    def generate_views_import(self: Self, urls_path: Path, views_path) -> str:
        """Generate the views file import statement so it can be used by the URLs file.

        Args:
            urls_path: Path object for the URLs file.
            views_path: Path object for the views file.

        Returns:
            Import statement for the views file relative to the URLs file.
        """
        urls_parts = urls_path.parts
        views_parts = views_path.parts

        # traverse past the common directories for both paths
        index = 0
        while urls_parts[index] == views_parts[index]:
            index += 1

        print(urls_parts[index:])
        print(views_parts[index:])

        if len(urls_parts[index:]) == len(views_parts[index:]):
            # urls and views are in the same directory
            import_statement = f"import {views_path.stem}"
        if len(urls_parts[index:]) < len(views_parts[index:]):
            # views is in a child directory of the urls file's directory
            import_statement = (
                f"from {'.'.join(views_parts[index:-1])} import {views_path.stem}"
            )
        elif len(urls_parts[index:]) > len(views_parts[index:]):
            # urls is in a child directory of the views file's directory
            num_parents = len(urls_parts[index:]) - len(views_parts[index:])

            import_statement = "import sys\n"
            import_statement += "from pathlib import Path\n"
            import_statement += "# TODO (OpenAPI to Django) consider moving views.py out of parent directory\n"
            # add the views directory to the module path so it can be imported
            import_statement += (
                f"sys.path.insert(0, str(Path(__file__).parents[{num_parents}]))\n"
            )
            import_statement += f"import {views_path.stem}"

        return import_statement
