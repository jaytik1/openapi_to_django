"""
Command line tool to load an OpenAPI document into a new Django project.

Create a new Django project and app, then load a given OpenAPI document into the new project.
"""

from pathlib import Path

from django.core.management import call_command

from openapi_to_django.argument_parsers import CommandLineArgumentParser
from openapi_to_django.openapi import get_paths_data, read_openapi_file
from openapi_to_django.urls import generate_urls_context
from openapi_to_django.utils import write_file_from_template
from openapi_to_django.views import generate_views_context


def main() -> None:
    """
    Load a given OpenAPI document into a new Django project and app.

    Parse command line arguments then call the appropriate Django commands.
    """
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

    # load the OpenAPI document
    print(f"Loading OpenAPI document {args.openapi_file}...")

    urls_target = (Path(args.project_name, args.project_name, "urls.py"),)
    views_target = app_directory / "views.py"

    openapi = read_openapi_file(args.file_type, args.openapi_file)
    paths_data = get_paths_data(openapi)

    # render and write the URLs file
    urls_context = generate_urls_context(paths_data, urls_target, views_target)
    write_file_from_template(urls_target, args.urls_template, urls_context)
    print(f"Loaded Django URL paths to {urls_target}.")

    # render and write the views file
    views_context = generate_views_context(paths_data, views_target)
    write_file_from_template(views_target, args.views_template, views_context)
    print(f"Loaded Django views to {views_target}.")

    print("OpenAPI to Django setup complete.")


if __name__ == "__main__":
    main()
