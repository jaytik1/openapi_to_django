"""Argument parsers used by the OpenAPI to Django tools."""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Self

from openapi_to_django.definitions import FileType


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

        # default target values are set here as they require the values of other arguments

        if parsed_args.urls_target is None:
            parsed_args.urls_target = Path(parsed_args.project_name, parsed_args.project_name, "urls.py")

        parsed_args.urls_target = Path(parsed_args.urls_target).resolve()

        if parsed_args.views_target is None:
            parsed_args.views_target = Path(parsed_args.project_name, parsed_args.app_name, "views.py")

        parsed_args.views_target = Path(parsed_args.views_target).resolve()

        return parsed_args
