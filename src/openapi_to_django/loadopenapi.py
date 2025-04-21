"""Django command to load an OpenAPI document into an existing project."""

from argparse import ArgumentParser
from typing import Any, Self

from django.core.management.base import BaseCommand

from openapi_to_django.argument_parsers import BaseArgumentParser
from openapi_to_django.openapi import OpenApi, get_paths_data, read_openapi_file
from openapi_to_django.urls import generate_urls_context
from openapi_to_django.utils import write_file_from_template
from openapi_to_django.views import generate_views_context


class Command(BaseCommand):
    """Django command to load an OpenAPI document."""

    help = "Generate Django code by loading a specified OpenAPI document"

    openapi: OpenApi

    def create_parser(self: Self, prog_name: str, subcommand: str, **kwargs: Any) -> ArgumentParser:
        """
        Override the BaseCommand create_parser method to include the BaseArgumentParser's arguments.

        Args:
            prog_name: Program name required by the Django BaseCommand method.
            subcommand: Subcommand required by the Django BaseCommand method.
            **kwargs: Additional keyword arguments used by the ArgumentParser classes.

        Returns:
            ArgumentParser which includes both the Django BaseCommand args
            and the OpenAPI to Django BaseArgumentParser args.
        """
        django_parser = super().create_parser(prog_name, subcommand, add_help=False, **kwargs)
        parser: ArgumentParser = BaseArgumentParser(parents=[django_parser])
        return parser

    def handle(self: Self, **options: str) -> None:
        """
        Validate command line arguments and load the OpenAPI document to Django.

        Raises:
            CommandError: Something went wrong when running the command.
        """
        # obtain the required command line arguments
        openapi_path = options.pop("openapi_file")
        urls_template_path = options.pop("urls_template")
        views_template_path = options.pop("views_template")
        urls_target_path = options.pop("urls_target")
        views_target_path = options.pop("views_target")
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
