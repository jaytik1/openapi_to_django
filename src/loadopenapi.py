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
class PathData:
    """Data about an OpenAPI path."""

    openapi_path: str  # path URL as stored in the OpenAPI document
    path_params: Mapping[str, str]  # dict of path parameters and their Django types


@dataclass
class DjangoPath:
    """Data required to create a Django path in urls.py."""

    url: str  # URL of the path, including any path parameters
    view_name: str  # name of the path's corresponding function in views.py


@dataclass
class DjangoView:
    """Data required to create a Django view function in views.py."""

    view_name: str  # name of the function in views.py
    params: Mapping[str, str]  # dict of view parameters and their types


class Command(BaseCommand):
    help = "Generate Django code by loading a specified OpenAPI document"

    def add_arguments(self, parser):
        """Add command line arguments for the command.

        Args:
            parser: Command line argument parser where the arguments are stored.
        """
        parser.add_argument("openapi_file", help="file path of the OpenAPI document")
        parser.add_argument(
            "-t",
            "--file-type",
            help="file type of the OpenAPI document",
            choices=[FileType.JSON.value, FileType.YAML.value],
            required=False,
        )

        # arguments for rendering the Django urls.py file
        parser.add_argument(
            "--urls-template",
            help="template file for rendering Django paths in urls.py",
            required=True,
        )
        parser.add_argument(
            "--urls-target",
            help="file where the generated Django URL paths should be written",
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
        """Handle the loadopenapi command when it is run.
        Validate command line arguments, then run the necessary functions.

        Raises:
            CommandError: Something went wrong when running the command.
        """
        openapi_path = Path(options.pop("openapi_file")).resolve()
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

        # determine the file type of the OpenAPI document
        file_type = options.pop("file_type")

        if file_type:
            # set file type to the manually specified one if given
            openapi_file_type = file_type
        else:
            # attempts to identify a file type from the file extension
            if openapi_path.suffix in JSON_EXTENSIONS:
                openapi_file_type = FileType.JSON.value
            elif openapi_path.suffix in YAML_EXTENSIONS:
                openapi_file_type = FileType.YAML.value

        # attempt to parse the file according to the determined file type
        if openapi_file_type == FileType.JSON.value:
            with open(openapi_path, "r") as json_file:
                openapi = json.load(json_file)
        elif openapi_file_type == FileType.YAML.value:
            with open(openapi_path, "r") as yaml_file:
                openapi = yaml.safe_load(yaml_file)
        else:
            raise CommandError(
                "OpenAPI file type not determined, use --file-type to specify"
            )

        paths_data = self.get_paths_data(openapi)

        self.write_urls_file(
            paths_data, urls_target_path, urls_template_path, views_target_path
        )
        self.write_views_file(paths_data, views_target_path, views_template_path)

    def get_paths_data(
        self: Self, openapi: Mapping[str, Any] | list[Any]
    ) -> list[PathData]:
        """Gets required data for all paths in an OpenAPI document.

        Args:
            openapi: Python representation of an OpenAPI document.

        Returns:
            List of PathData objects gathered from the OpenAPI document.
        """
        paths_data = []

        for path_name, path_content in openapi["paths"].items():
            path_params = {}

            # get path parameters from the path object
            if "parameters" in path_content:
                self.parse_path_params(path_content["parameters"], path_params)

            # get path parameters from each of the path's operation objects
            for operation_content in path_content.values():
                if "parameters" in operation_content:
                    self.parse_path_params(operation_content["parameters"], path_params)

            # convert each of the parameter types from OpenAPI to Django
            django_path_params = {
                param_name: self.openapi_to_django_type(param_type)
                for (param_name, param_type) in path_params.items()
            }

            paths_data.append(PathData(path_name, django_path_params))

        return paths_data

    def write_urls_file(
        self: Self,
        paths_data: list[PathData],
        urls_target_path: Path,
        urls_template_path: Path,
        views_target_path: Path,
    ):
        """Render and write a Django urls.py file.

        Args:
            paths_data: Data about each path in the OpenAPI document.
            urls_target_path: Path where the urls.py file should be written.
            urls_template_path: Path of the urls.py template file.
            views_target_path: Path where the views.py file should be written.
        """
        # generate DjangoPath objects for each path
        paths = [self.get_django_path(path_data) for path_data in paths_data]

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

    def write_views_file(
        self: Self,
        paths_data: list[PathData],
        views_target_path: Path,
        views_template_path: Path,
    ):
        """Render and write a Django views.py file.

        Args:
            paths_data: Data about each path in the OpenAPI document.
            views_target_path: Path where the views.py file should be written.
            views_template_path: Path of the views.py template file.
        """
        views = [self.get_django_view(path_data) for path_data in paths_data]

        with open(views_template_path, "r") as views_template_file:
            views_template_string = views_template_file.read()

        # convert the views.py template file content to a renderable Template object
        views_template = Engine().from_string(views_template_string)

        views_context = Context(
            {"views": views, "views_exists": views_target_path.is_file()},
            autoescape=False,
        )
        rendered_views = views_template.render(views_context)

        with open(views_target_path, "a") as views_file:
            views_file.write(rendered_views)

        print(f"Wrote generated view functions to {views_target_path}.")

    def parse_path_params(
        self: Self,
        params_list: list[Mapping[str, Any]],
        current_params: Mapping[str, str],
    ):
        """
        Parse a list of OpenAPI parameter obejcts to get their names and types.
        Ignores any parameters which aren't path parameters.

        Args:
            params_list: List of OpenAPI parameter objects.
            current_params: Existing mapping of parameters to types,
            which is checked for conflicts and used to store new path parameters.

        Raises:
            Exception: There is a conflicting path parameter (same name but different type).
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

    def openapi_to_django_type(self: Self, param_type: str) -> str:
        """Convert an OpenAPI type to its equivalent Django type.

        Args:
            param_type: Name of the OpenAPI type to be converted.

        Returns:
            Name of the equivalent Django type, or a default type if not found.
        """
        # maps the OpenAPI path parameter types to Django path parameter types
        OPENAPI_DJANGO_TYPE_MAP = {"number": "int", "integer": "int", "string": "str"}
        DEFAULT_DJANGO_TYPE = "str"

        return (
            OPENAPI_DJANGO_TYPE_MAP[param_type]
            if param_type in OPENAPI_DJANGO_TYPE_MAP
            else DEFAULT_DJANGO_TYPE
        )

    def get_django_path(self: Self, path_data: PathData) -> DjangoPath:
        """Generate a DjangoPath dataclass object from a path.

        Args:
            path_data: Data about the given path.

        Returns:
            A DjangoPath object representing the given path.
        """
        url = self.get_url_from_path(path_data.openapi_path, path_data.path_params)
        view_name = self.get_view_from_path(path_data.openapi_path)

        return DjangoPath(url, view_name)

    def generate_views_import(self: Self, urls_path: Path, views_path: Path) -> str:
        """Generate an import statement for the views file, to be used in the URLs file.

        Args:
            urls_path: Path object for the URLs file.
            views_path: Path object for the views file.

        Returns:
            Import statement for the views file relative to the URLs file.
        """
        urls_parts = list(urls_path.parts)
        views_parts = list(views_path.parts)

        # discard the common parent directories for both paths
        while (
            len(urls_parts) > 0
            and len(views_parts) > 0
            and urls_parts[0] == views_parts[0]
        ):
            urls_parts.pop(0)
            views_parts.pop(0)

        if len(urls_parts) == 1 and len(views_parts) == 1:
            # urls and views are in the same directory
            import_statement = f"import {views_path.stem}"
        elif len(urls_parts) < len(views_parts):
            # views is in a deeper directory than urls
            import_statement = (
                f"from {'.'.join(views_parts[:-1])} import {views_path.stem}"
            )
        elif len(urls_parts) >= len(views_parts):
            # urls is in an equal-depth or deeper directory than views
            import_statement = f"from {views_path.parent.stem} import {views_path.stem}"

        return import_statement

    def get_django_view(self: Self, path_data: PathData) -> DjangoView:
        """Generate a DjangoView dataclass object from a path.

        Args:
            path_data: Data about the given path.

        Returns:
            A DjangoView object representing the given path.
        """
        view_name = self.get_view_from_path(path_data.openapi_path)

        return DjangoView(view_name, path_data.path_params)

    def get_url_from_path(self: Self, path: str, path_params: Mapping[str, str]) -> str:
        """Generate a Django path URL from an OpenAPI path.

        Args:
            path: OpenAPI path string to be used.

        Returns:
            The Django URL corresponding to the OpenAPI path.
        """
        tokens = self.get_tokens_from_path(path)

        url_tokens = []

        for token in tokens:
            # get the parameter name inside the braces
            # e.g. gets "id" from "{id}"
            extract_parameter = re.compile("(?<=\{)(.+)(?=\})")
            parameter_list = extract_parameter.findall(token)

            # continue if the current token isn't a path parameter
            if len(parameter_list) != 1:
                url_tokens.append(token)
                continue

            param_name = parameter_list[0]

            if param_name not in path_params:
                raise Exception(
                    f"Error generating URL: parameter name {param_name} not defined!"
                )

            param_type = path_params[param_name]
            url_tokens.append(f"<{param_type}:{param_name}>")

        return "/".join(url_tokens)  # generate the Django path URL

    def get_view_from_path(self: Self, path: str) -> str:
        """Generate a Django views.py function name from an OpenAPI path.

        Args:
            path: OpenAPI path string to be used.

        Returns:
            The name of a views function corresponding to the OpenAPI path.
        """
        tokens = self.get_tokens_from_path(path)

        # remove braces from the path tokens name to generate the view name
        view_tokens = [re.sub("[\{\}]", "", token) for token in tokens]

        return "_".join(view_tokens)  # generate the views.py function name

    def get_tokens_from_path(self: Self, path: str) -> list[str]:
        """Splits a URL path by its slashes (/) to get each of its tokens.
        (e.g. "/example/{id}" should get split into tokens ["example", "{id}"])

        Args:
            path: URL path to be split.

        Returns:
            A list of tokens present in the given path.
        """
        split_slash = re.compile("(?<=\/)([^\/]+)")
        tokens = split_slash.findall(path)
        return tokens


if __name__ == "__main__":
    print("error: tried to run loadopenapi.py directly")
    print("Copy this file to the directory 'management/commands/' in a Django app.")
    print("Then, run the command using 'python3 manage.py loadopenapi'.")
