"""
Command line tool to load an OpenAPI document into a Django project.

Create a new Django project and app, then load a given OpenAPI document into the new project.
"""

import argparse
from pathlib import Path

from django.core.management import call_command

from openapi_to_django import loadopenapi
from openapi_to_django.constants import FileType

DEFAULT_PROJECT_NAME = "openapi_django"
DEFAULT_APP_NAME = DEFAULT_PROJECT_NAME + "_app"

# paths to default template files and directories
TEMPLATE_DIR = Path(__file__).parent / "templates"
PROJECT_TEMPLATE_DIR = TEMPLATE_DIR / "project_template"
APP_TEMPLATE_DIR = TEMPLATE_DIR / "app_template"
URLS_TEMPLATE_PATH = TEMPLATE_DIR / "urls.py-tpl"
VIEWS_TEMPLATE_PATH = TEMPLATE_DIR / "views.py-tpl"


def main() -> None:
    """
    Load a given OpenAPI document into a new Django project and app.

    Parse command line arguments then call the appropriate Django commands.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("openapi_file", help="file path of the OpenAPI document")
    parser.add_argument(
        "-t",
        "--file-type",
        help="file type of the OpenAPI document (not required, the program will attempt to estimate the file type if not provided)",
        choices=[FileType.JSON.value, FileType.YAML.value],
        required=False,
    )

    # arguments for setting up Django
    parser.add_argument(
        "-p",
        "--project-name",
        help="name of the Django project being created",
        default=DEFAULT_PROJECT_NAME,
    )
    parser.add_argument(
        "-a",
        "--app-name",
        help="name of the Django app being created",
        default=DEFAULT_APP_NAME,
    )

    args = parser.parse_args()

    # attempt to create a new Django project
    call_command("startproject", args.project_name, template=str(PROJECT_TEMPLATE_DIR))
    print(f"Created Django project {args.project_name}.")

    # attempt to create a new app in the new Django project
    app_directory = Path(args.project_name, args.app_name)
    app_directory.mkdir(parents=True)

    call_command(
        "startapp",
        args.app_name,
        app_directory,
        template=str(APP_TEMPLATE_DIR),
    )
    print(f"Created Django app {args.app_name} in directory {app_directory}.")

    # automatically load the OpenAPI document
    print(f"Loading OpenAPI document {args.openapi_file}...")
    load_openapi_command = loadopenapi.Command()
    call_command(
        load_openapi_command,
        args.openapi_file,
        file_type=args.file_type,
        urls_template=URLS_TEMPLATE_PATH,
        views_template=VIEWS_TEMPLATE_PATH,
        urls_target=Path(args.project_name, args.project_name, "urls.py"),
        views_target=app_directory / "views.py",
    )

    print("OpenAPI to Django setup complete.")


if __name__ == "__main__":
    main()
