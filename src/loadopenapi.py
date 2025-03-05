import json
import re
import yaml
from django.core.management.base import BaseCommand, CommandError
from django.template import Context, Engine
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Self


# maps the OpenAPI path parameter types to Django path parameter types
OPENAPI_DJANGO_TYPE_MAP = {"number": "int", "integer": "int", "string": "str"}
DEFAULT_DJANGO_TYPE = "str"

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

    openapi: Mapping[str, Any] | None = None

    def add_arguments(self, parser):
        """Add command line arguments for the command.

        Args:
            parser: Command line argument parser where the arguments are stored.
        """
        parser.add_argument("openapi_file", help="file path of the OpenAPI document")
        parser.add_argument(
            "-t",
            "--file-type",
            help="file type of the OpenAPI document (not required, the program will attempt to estimate the file type if not provided)",
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
        """
        Handle the loadopenapi command when it is run.
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

        # resolve all reference objects in the OpenAPI document
        self.openapi = self.resolve_ref_objects(openapi, openapi)

        paths_data = self.get_paths_data(self.openapi)

        # render and write the URLs file
        urls_context = self.generate_urls_context(
            paths_data, urls_target_path, views_target_path
        )
        self.write_file_from_template(
            urls_target_path, urls_template_path, urls_context
        )
        print(f"Loaded Django URL paths to {urls_target_path}.")

        # render and write the views file
        views_context = self.generate_views_context(paths_data, views_target_path)
        self.write_file_from_template(
            views_target_path, views_template_path, views_context
        )
        print(f"Loaded Django views to {views_target_path}.")

    def resolve_ref_objects(self: Self, current: Any, base_dict: dict) -> Any:
        """Recursively resolve all reference objects (if any) inside an given variable.

        Args:
            current: Current variable to be resolved.
            base_object: Dictionary checked to resolve the referenced URIs.

        Raises:
            Exception: Reference object format is invalid or target doesn't exist.

        Returns:
            The object with all reference objects inside resolved.
        """
        # return the current variable if isn't a dictionary or a list (base case)
        if not isinstance(current, dict) and not isinstance(current, list):
            return current

        # resolve all items in the list
        if isinstance(current, list):
            return [self.resolve_ref_objects(item, base_dict) for item in current]

        # resolve each dictionary value if the dictionary doesn't contain a ref
        if "$ref" not in current:
            return {
                key: self.resolve_ref_objects(val, base_dict)
                for key, val in current.items()
            }

        # raise an exception if the dictionary contains other data as well as a ref
        if len(current) != 1:
            raise Exception(
                f"Dictionary contains other data as well as a reference object: {current}"
            )

        uri = current["$ref"]

        # references to parts of the same document must start with #
        if uri[0] != "#":
            raise Exception(f"Reference object URI doesn't start with '#': {current}")

        tokens = self.get_tokens_from_uri(uri)
        result = self.traverse_nested_dictionary(base_dict, tokens)

        if result is None:
            raise Exception(f"Reference object location doesn't exist! {current}")

        return self.resolve_ref_objects(result, base_dict)

    def get_paths_data(self: Self, openapi: Mapping[str, Any]) -> list[PathData]:
        """Get required data for all paths in an OpenAPI document.

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
                param_name: OPENAPI_DJANGO_TYPE_MAP.get(param_type, DEFAULT_DJANGO_TYPE)
                for (param_name, param_type) in path_params.items()
            }

            paths_data.append(PathData(path_name, django_path_params))

        return paths_data

    def generate_urls_context(
        self: Self,
        paths_data: list[PathData],
        urls_target_path: Path,
        views_target_path: Path,
    ) -> Context:
        """Generate the template context for the Django urls.py file.

        Args:
            paths_data: Data about each path in the OpenAPI document.
            urls_target_path: Path where the urls.py file should be written.
            views_target_path: Path where the views.py file should be written.

        Returns:
            Context object to be used by the URLs template.
        """
        paths = []

        # generate a DjangoPath object for each path
        for path_data in paths_data:
            url = self.get_url_from_path(path_data.openapi_path, path_data.path_params)
            view_name = self.get_view_from_path(path_data.openapi_path)
            paths.append(DjangoPath(url, view_name))

        views_import = self.generate_views_import(urls_target_path, views_target_path)

        return Context(
            {
                "paths": paths,
                "urls_exists": urls_target_path.is_file(),
                "views_name": views_target_path.stem,
                "views_import": views_import,
            },
            autoescape=False,
        )

    def generate_views_context(
        self: Self,
        paths_data: list[PathData],
        views_target_path: Path,
    ) -> Context:
        """Generate the template context for the Django views.py file.

        Args:
            paths_data: Data about each path in the OpenAPI document.
            views_target_path: Path where the views.py file should be written.

        Returns:
            Context object to be used by the views template.
        """
        views = []

        # generate a DjangoView object for each path
        for path_data in paths_data:
            view_name = self.get_view_from_path(path_data.openapi_path)
            views.append(DjangoView(view_name, path_data.path_params))

        return Context(
            {"views": views, "views_exists": views_target_path.is_file()},
            autoescape=False,
        )

    def write_file_from_template(
        self: Self, target_path: Path, template_path: Path, context: Context
    ):
        """Render a template and its context and write to a specified file path.

        Args:
            target_path: Path where the rendered content should be written.
            template_path: Path to the template.
            context: Context to be used by the template.
        """
        with open(template_path, "r") as template_file:
            template_string = template_file.read()

        # convert the template file content to a renderable Template object
        template = Engine().from_string(template_string)

        rendered_file = template.render(context)

        with open(target_path, "a") as target_file:
            target_file.write(rendered_file)

    def get_tokens_from_uri(self: Self, path: str) -> list[str]:
        """
        Split a URI by its slashes (/) to get each of its tokens.
        (e.g. "/example/{id}" should get split into tokens ["example", "{id}"])

        Args:
            path: URI to be split.

        Returns:
            A list of tokens present in the given URI.
        """
        split_slash = re.compile("(?<=\/)([^\/]+)")
        tokens = split_slash.findall(path)
        return tokens

    def traverse_nested_dictionary(
        self: Self, dictionary: dict, keys: list[str]
    ) -> dict | None:
        """Recursively traverse a nested dictionary using a list of keys.

        Args:
            dictionary: Dictionary to be traversed.
            keys: List of keys that should exist in the nested dictionary.

        Returns:
            The final key's value if it exists within the dictionary.
            None if the keys don't match the nested dictionary.
        """
        if len(keys) == 0:
            return dictionary

        key = keys.pop(0)

        if key not in dictionary:
            return None

        return self.traverse_nested_dictionary(dictionary[key], keys)

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

    def get_url_from_path(self: Self, path: str, path_params: Mapping[str, str]) -> str:
        """Generate a Django path URL from an OpenAPI path.

        Args:
            path: OpenAPI path string to be used.

        Returns:
            The Django URL corresponding to the OpenAPI path.
        """
        tokens = self.get_tokens_from_uri(path)

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
        tokens = self.get_tokens_from_uri(path)

        # remove braces from the path tokens name to generate the view name
        view_tokens = [re.sub("[\{\}]", "", token) for token in tokens]

        return "_".join(view_tokens)  # generate the views.py function name

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


if __name__ == "__main__":
    print("error: tried to run loadopenapi.py directly")
    print("Copy this file to the directory 'management/commands/' in a Django app.")
    print("Then, run the command using 'python3 manage.py loadopenapi'.")
