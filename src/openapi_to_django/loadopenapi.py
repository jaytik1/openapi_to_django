"""Django command to load an OpenAPI document into an existing project."""

from argparse import ArgumentParser
from pathlib import Path
from typing import Self

from django.core.management.base import BaseCommand, CommandError

from openapi_to_django.definitions import FileType
from openapi_to_django.openapi import OpenApi, get_paths_data, read_openapi_file
from openapi_to_django.urls import generate_urls_context
from openapi_to_django.utils import write_file_from_template
from openapi_to_django.views import generate_views_context


class Command(BaseCommand):
    """Django command to load an OpenAPI document."""

    help = "Generate Django code by loading a specified OpenAPI document"

    openapi: OpenApi

    def add_arguments(self: Self, parser: ArgumentParser) -> None:
        """
        Add command line arguments for the command.

        Args:
            parser: Argument parser for the command.
        """
        parser.add_argument("openapi_file", help="file path of the OpenAPI document")
        parser.add_argument(
            "-t",
            "--file-type",
            help="(optional) file type of the OpenAPI document",
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

    def handle(self: Self, **options: str) -> None:
        """
        Validate command line arguments and load the OpenAPI document to Django.

        Raises:
            CommandError: Something went wrong when running the command.
        """
        openapi_path = Path(options.pop("openapi_file")).resolve()
        if not openapi_path.is_file():
            msg = f"OpenAPI file {openapi_path} does not exist"
            raise CommandError(msg)

        urls_template_path = Path(options.pop("urls_template")).resolve()
        if not urls_template_path.is_file():
            msg = f"urls.py template file {urls_template_path} does not exist"
            raise CommandError(msg)

        views_template_path = Path(options.pop("views_template")).resolve()
        if not views_template_path.is_file():
            msg = f"views.py template file {views_template_path} does not exist"
            raise CommandError(msg)

        urls_target_path = Path(options.pop("urls_target")).resolve()
        if not urls_target_path.parent.is_dir():
            # create directory for the URLs target if it doesn't exist
            urls_target_path.parent.mkdir(parents=True)

        views_target_path = Path(options.pop("views_target")).resolve()
        if not views_target_path.parent.is_dir():
            # create directory for the views target if it doesn't exist
            views_target_path.parent.mkdir(parents=True)

        file_type = options.pop("file_type")

        self.openapi = read_openapi_file(file_type, openapi_path)
        paths_data = get_paths_data(self.openapi)

        # render and write the URLs file
        urls_context = generate_urls_context(paths_data, urls_target_path, views_target_path)
        write_file_from_template(urls_target_path, urls_template_path, urls_context)
        print(f"Loaded Django URL paths to {urls_target_path}.")

        # render and write the views file
        views_context = generate_views_context(paths_data, views_target_path)
        write_file_from_template(views_target_path, views_template_path, views_context)
        print(f"Loaded Django views to {views_target_path}.")


if __name__ == "__main__":
    print("error: tried to run loadopenapi.py directly")
    print("Copy this file to the directory 'management/commands/' in a Django app.")
    print("Then, run the command using 'python3 manage.py loadopenapi'.")
