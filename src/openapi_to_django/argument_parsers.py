"""Argument parsers used by the OpenAPI to Django tools."""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Self

import openapi_to_django
from openapi_to_django.definitions import FileType


class BaseArgumentParser(ArgumentParser):
    """
    Base argument parser which includes the arguments common across each OpenAPI to Django tool.

    Automatically add arguments such as the path to the OpenAPI file and paths to Django templates.
    """

    # default paths to template files and directories
    TEMPLATE_DIR: Path
    URLS_TEMPLATE_PATH: Path
    VIEWS_TEMPLATE_PATH: Path

    def __init__(self: Self, **kwargs: Any) -> None:
        """Create the arguments used by the OpenAPI to Django command line tools."""
        super().__init__(**kwargs)

        self.TEMPLATE_DIR = Path(openapi_to_django.__file__).parent / "templates"
        self.URLS_TEMPLATE_PATH = self.TEMPLATE_DIR / "urls.py-tpl"
        self.VIEWS_TEMPLATE_PATH = self.TEMPLATE_DIR / "views.py-tpl"

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
            default=self.URLS_TEMPLATE_PATH,
        )
        self.add_argument(
            "--urls-target",
            help="file where the generated Django URL paths should be written",
            default="urls.py",
        )

        # arguments for rendering the Django views.py file
        self.add_argument(
            "--views-template",
            help="template file for rendering functions in views.py",
            default=self.VIEWS_TEMPLATE_PATH,
        )
        self.add_argument(
            "--views-target",
            help="file where the generated Django view functions should be written",
            default="views.py",
        )

    def parse_args(self: Self, **kwargs: Any) -> Namespace:  # type: ignore
        """
        Parse arguments and perform necessary validation checks.

        Args:
            **kwargs: Keyword arguments to be passed to the overridden method in ArgumentParser.

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

        parsed_args.urls_target = Path(parsed_args.urls_target).resolve()
        if not parsed_args.urls_target.parent.is_dir():
            # create directory for the URLs target if it doesn't exist
            parsed_args.urls_target.parent.mkdir(parents=True)

        parsed_args.views_target = Path(parsed_args.views_target).resolve()
        if not parsed_args.views_target.parent.is_dir():
            # create directory for the views target if it doesn't exist
            parsed_args.views_target.parent.mkdir(parents=True)

        return parsed_args


class CommandLineArgumentParser(BaseArgumentParser):
    """
    Argument parser used specifically by the OpenAPI to Django command line utility.

    Extends the base argument parser used by each OpenAPI to Django tool.
    Includes additional arguments for setting up a new Django project.
    """

    # default names and paths for Django projects and apps
    PROJECT_NAME: str
    APP_NAME: str
    PROJECT_TEMPLATE_PATH: Path
    APP_TEMPLATE_PATH: Path

    def __init__(self: Self, **kwargs: Any) -> None:
        """Create the arguments used by the OpenAPI to Django command line tool."""
        super().__init__(**kwargs)

        self.PROJECT_NAME = "openapi_django"
        self.APP_NAME = self.PROJECT_NAME + "_app"
        self.PROJECT_TEMPLATE_PATH = self.TEMPLATE_DIR / "project_template"
        self.APP_TEMPLATE_PATH = self.TEMPLATE_DIR / "app_template"

        # arguments for setting up a new Django project
        self.add_argument(
            "-p",
            "--project-name",
            help="name of the Django project being created",
            default=self.PROJECT_NAME,
        )
        self.add_argument(
            "--project-template",
            help="template folder for the Django project",
            default=self.PROJECT_TEMPLATE_PATH,
        )

        # arguments for setting up a new Django app
        self.add_argument(
            "-a",
            "--app-name",
            help="name of the Django app being created",
            default=self.APP_NAME,
        )
        self.add_argument(
            "--app-template",
            help="template folder for the Django app",
            default=self.APP_TEMPLATE_PATH,
        )
