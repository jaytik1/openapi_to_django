"""
Command line tool to load an OpenAPI document into a new Django project.

Create a new Django project and app, then load a given OpenAPI document into the new project.
"""

from argparse import ArgumentError, ArgumentParser, Namespace
from pathlib import Path

from django.core.management import call_command
from django.template import Engine
from prance import ResolvingParser

from openapi_to_django.openapi import get_paths_data
from openapi_to_django.urls import generate_urls_context
from openapi_to_django.views import generate_views_context

PROJECT_MODE = "projects"
FILE_MODE = "files"


def main() -> None:
    """Load a given OpenAPI document with an ArgumentParser and generate Django code."""
    parser = create_parser()
    args = validate_args(parser.parse_args())

    if args.mode == PROJECT_MODE:
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
    openapi = ResolvingParser(args.openapi_file.as_uri()).specification
    paths_data = get_paths_data(openapi)
    print(f"Loaded OpenAPI document {args.openapi_file}.")

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


def create_parser() -> ArgumentParser:
    """
    Create the ArgumentParser used by the openapi_to_django command.

    Two subparsers are created and linked to the main parser.
    The projects subparser is used to create new Django projects.
    The files subparser is used to just create the generated files.

    Returns:
        ArgumentParser to be used by the command line tool.
    """
    template_dir = Path(__file__).parent / "templates"

    # parser containing arguments present in all subparsers
    base_parser = ArgumentParser(add_help=False)

    base_parser.add_argument("openapi_file", help="file path of the OpenAPI document")
    base_parser.add_argument(
        "--urls-template",
        help="custom template file for rendering urls.py",
        default=template_dir / "urls.py-tpl",
    )
    base_parser.add_argument(
        "--views-template",
        help="custom template file for rendering views.py",
        default=template_dir / "views.py-tpl",
    )

    # main parser used to store the subparsers
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="mode")

    # subparser for generating Django projects
    project_mode_parser = subparsers.add_parser(PROJECT_MODE, parents=[base_parser])

    project_mode_parser.add_argument(
        "-p",
        "--project-name",
        help="name of the Django project being created",
        default="openapi_django",
    )
    project_mode_parser.add_argument(
        "-a",
        "--app-name",
        help="name of the Django app being created",
        default="openapi_django_app",
    )
    project_mode_parser.add_argument(
        "--project-template",
        help="custom template folder for the Django project",
        default=template_dir / "project_template",
    )
    project_mode_parser.add_argument(
        "--app-template",
        help="custom template folder for the Django app",
        default=template_dir / "app_template",
    )

    # subparser for generating just files
    file_mode_parser = subparsers.add_parser(FILE_MODE, parents=[base_parser])

    file_mode_parser.add_argument(
        "-u",
        "--urls-target",
        help="file where the generated Django URL paths should be written",
        default=Path("urls.py"),
    )
    file_mode_parser.add_argument(
        "-v",
        "--views-target",
        help="file where the generated Django view functions should be written",
        default=Path("views.py"),
    )

    return parser


def validate_args(parsed_args: Namespace) -> Namespace:  # ignore
    """
    Validate that the given command line arguments are valid.

    Mainly used to check that given files actually exist.
    Updates path arguments to be the Path type rather than the Action type.

    Args:
        parsed_args: Parsed arguments obtained from the ArgumentParser.

    Raises:
        ArgumentError: One of the command line arguments was invalid.

    Returns:
        Validated and updated arguments.
    """
    parsed_args.openapi_file = Path(parsed_args.openapi_file).resolve()
    if not parsed_args.openapi_file.is_file():
        msg = f"OpenAPI file {parsed_args.openapi_file} does not exist"
        raise ArgumentError(None, msg)

    parsed_args.urls_template = Path(parsed_args.urls_template).resolve()
    if not parsed_args.urls_template.is_file():
        msg = f"urls.py template file {parsed_args.urls_template} does not exist"
        raise ArgumentError(None, msg)

    parsed_args.views_template = Path(parsed_args.views_template).resolve()
    if not parsed_args.views_template.is_file():
        msg = f"views.py template file {parsed_args.views_template} does not exist"
        raise ArgumentError(None, msg)

    if parsed_args.mode == PROJECT_MODE:
        parsed_args.urls_target = Path(
            parsed_args.project_name,
            parsed_args.project_name,
            "urls.py",
        ).resolve()
        parsed_args.views_target = Path(
            parsed_args.project_name,
            parsed_args.app_name,
            "views.py",
        ).resolve()
    elif parsed_args.mode == FILE_MODE:
        parsed_args.urls_target = Path(parsed_args.urls_target).resolve()
        parsed_args.views_target = Path(parsed_args.views_target).resolve()

    return parsed_args


if __name__ == "__main__":
    main()
