"""
Command line tool to load an OpenAPI document into a new Django project.

Create a new Django project and app, then load a given OpenAPI document into the new project.
"""

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Self

import yaml
from django.core.management import call_command
from django.template import Engine

from openapi_to_django.definitions import FileType
from openapi_to_django.openapi import get_paths_data, resolve_ref_objects
from openapi_to_django.urls import generate_urls_context
from openapi_to_django.views import generate_views_context


class CustomArgumentParser(ArgumentParser):
    """
    Argument parser used by the OpenAPI to Django tool.

    Contains arguments such as the path to the OpenAPI file and paths to Django templates.
    """

    TEMPLATE_DIR: Path

    def __init__(self: Self, **kwargs: Any) -> None:
        """Create the arguments used by the OpenAPI to Django command line tools."""
        super().__init__(**kwargs)

        self.TEMPLATE_DIR = Path(__file__).parent / "templates"

        self.add_argument("openapi_file", help="file path of the OpenAPI document")
        self.add_argument(
            "-t",
            "--file-type",
            help="(optional) file type of the OpenAPI document",
            choices=[FileType.JSON.value, FileType.YAML.value],
            required=False,
        )

        # arguments for rendering the Django urls.py file
        self.add_argument(
            "--urls-template",
            help="template file for rendering Django paths in urls.py",
            default=self.TEMPLATE_DIR / "urls.py-tpl",
        )
        self.add_argument(
            "--urls-target",
            help="file where the generated Django URL paths should be written",
        )

        # arguments for rendering the Django views.py file
        self.add_argument(
            "--views-template",
            help="template file for rendering functions in views.py",
            default=self.TEMPLATE_DIR / "views.py-tpl",
        )
        self.add_argument(
            "--views-target",
            help="file where the generated Django view functions should be written",
        )

        # arguments for setting up a new Django project
        self.add_argument(
            "-p",
            "--project-name",
            help="name of the Django project being created",
            default="openapi_django",
        )
        self.add_argument(
            "--project-template",
            help="template folder for the Django project",
            default=self.TEMPLATE_DIR / "project_template",
        )

        # arguments for setting up a new Django app
        self.add_argument(
            "-a",
            "--app-name",
            help="name of the Django app being created",
            default="openapi_django_app",
        )
        self.add_argument(
            "--app-template",
            help="template folder for the Django app",
            default=self.TEMPLATE_DIR / "app_template",
        )

    def parse_args(self: Self, **kwargs: Any) -> Namespace:  # type: ignore
        """
        Parse arguments and perform necessary validation checks. Convert file paths to Path objects when necessary.

        Returns:
            Namespace object containing the parsed and validated arguments.
        """
        parsed_args: Namespace = super().parse_args(**kwargs)

        parsed_args.openapi_file = Path(parsed_args.openapi_file).resolve()
        if not parsed_args.openapi_file.is_file():
            msg = f"OpenAPI file {parsed_args.openapi_file} does not exist"
            self.error(msg)

        parsed_args.urls_template = Path(parsed_args.urls_template).resolve()
        if not parsed_args.urls_template.is_file():
            msg = f"urls.py template file {parsed_args.urls_template} does not exist"
            self.error(msg)

        parsed_args.views_template = Path(parsed_args.views_template).resolve()
        if not parsed_args.views_template.is_file():
            msg = f"views.py template file {parsed_args.views_template} does not exist"
            self.error(msg)

        # default values are set here as they require the values of other arguments

        if parsed_args.file_type is None:
            # attempts to identify a file type from the OpenAPI file extension
            if parsed_args.openapi_file.suffix == ".json":
                parsed_args.file_type = FileType.JSON.value
            elif parsed_args.openapi_file.suffix in [".yaml", ".yml"]:
                parsed_args.file_type = FileType.YAML.value

        if parsed_args.urls_target is None:
            parsed_args.urls_target = Path(parsed_args.project_name, parsed_args.project_name, "urls.py")

        parsed_args.urls_target = Path(parsed_args.urls_target).resolve()

        if parsed_args.views_target is None:
            parsed_args.views_target = Path(parsed_args.project_name, parsed_args.app_name, "views.py")

        parsed_args.views_target = Path(parsed_args.views_target).resolve()

        return parsed_args


def main() -> None:
    """Load a given OpenAPI document into a new Django project and app."""
    parser = CustomArgumentParser()
    args = parser.parse_args()

    # attempt to create a new Django project
    call_command("startproject", args.project_name, template=str(args.project_template))
    print(f"Created Django project {args.project_name}.")

    # attempt to create a new app in the new Django project
    app_directory = Path(args.project_name, args.app_name)
    app_directory.mkdir(parents=True)

    call_command(
        "startapp",
        args.app_name,
        app_directory,
        template=str(args.app_template),
    )
    print(f"Created Django app {args.app_name} in directory {app_directory}.")

    # load the OpenAPI document
    print(f"Loading OpenAPI document {args.openapi_file}...")

    # parse the OpenAPI file according to the determined file type
    if args.file_type == FileType.JSON.value:
        with args.openapi_file.open() as json_file:
            openapi = json.load(json_file)
    elif args.file_type == FileType.YAML.value:
        with args.openapi_file.open() as yaml_file:
            openapi = yaml.safe_load(yaml_file)
    else:
        msg = "OpenAPI file type not determined, use --file-type to specify"
        raise ValueError(msg)

    openapi = resolve_ref_objects(openapi, openapi)
    paths_data = get_paths_data(openapi)

    # render and write the URLs file
    urls_context = generate_urls_context(paths_data, args.urls_target, args.views_target)

    with args.urls_template.open() as urls_template_file:
        urls_template = Engine().from_string(urls_template_file.read())

    with args.urls_target.open("a") as target_file:
        target_file.write(urls_template.render(urls_context))

    print(f"Loaded Django URL paths to {args.urls_target}.")

    # render and write the views file
    views_context = generate_views_context(paths_data, args.views_target)

    with args.views_template.open() as views_template_file:
        views_template = Engine().from_string(views_template_file.read())

    with args.views_target.open("a") as target_file:
        target_file.write(views_template.render(views_context))

    print(f"Loaded Django views to {args.views_target}.")

    print("OpenAPI to Django setup complete.")


if __name__ == "__main__":
    main()
