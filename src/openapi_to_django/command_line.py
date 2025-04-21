"""
Command line tool to load an OpenAPI document into a new Django project.

Create a new Django project and app, then load a given OpenAPI document into the new project.
"""

from pathlib import Path

from django.core.management import call_command

from openapi_to_django import loadopenapi
from openapi_to_django.argument_parsers import CommandLineArgumentParser


def main() -> None:
    """
    Load a given OpenAPI document into a new Django project and app.

    Parse command line arguments then call the appropriate Django commands.
    """
    # create an instance of the general OpenAPI to Django argument parser
    parser = CommandLineArgumentParser()
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

    # automatically load the OpenAPI document
    print(f"Loading OpenAPI document {args.openapi_file}...")
    load_openapi_command = loadopenapi.Command()
    call_command(
        load_openapi_command,
        args.openapi_file,
        file_type=args.file_type,
        urls_template=args.urls_template,
        views_template=args.views_template,
        urls_target=Path(args.project_name, args.project_name, "urls.py"),
        views_target=app_directory / "views.py",
    )

    print("OpenAPI to Django setup complete.")


if __name__ == "__main__":
    main()
