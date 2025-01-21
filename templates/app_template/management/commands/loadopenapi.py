import os
from django.core.management.base import BaseCommand, CommandError
from django.template import Context, Engine


class Command(BaseCommand):
    help = "Load a specified OpenAPI document"

    def add_arguments(self, parser):
        parser.add_argument("openapi-file", help="OpenAPI file")
        parser.add_argument(
            "--urls-template",
            help="template file for rendering OpenAPI endpoints in urls.py",
            default=os.path.join("..", "templates", "urls.py-tpl"),
        )
        parser.add_argument(
            "--urls-target",
            help="urls.py file where the rendered URLs should be written",
            default="urls.py",
        )

    def handle(self, **options):
        openapi_file = options.pop("openapi-file")
        openapi_path = os.path.abspath(openapi_file)

        if not os.path.exists(openapi_path):
            raise CommandError(f"OpenAPI file {openapi_file} does not exist")

        urls_template_argument = options.pop("urls_template")
        urls_template_path = os.path.abspath(urls_template_argument)

        if not os.path.exists(urls_template_path):
            raise CommandError(
                f"urls.py template file {urls_template_path} does not exist"
            )

        # target urls.py file doesn't need to exist already, can write to a new one
        urls_target_argument = options.pop("urls_target")
        urls_target_path = os.path.abspath(urls_target_argument)

        urls_exists = False

        if os.path.exists(urls_target_path):
            urls_exists = True

        with open(urls_template_path, "r", encoding="utf-8") as urls_template_file:
            urls_template_string = urls_template_file.read()

        # converts the urls.py template file content to a renderable Template object
        urls_template = Engine().from_string(urls_template_string)

        context = Context(
            {"tags": ["ex1", "ex2", "ex3"], "urls_exists": urls_exists},
            autoescape=False,
        )
        rendered_urls = urls_template.render(context)

        with open(urls_target_path, "a", encoding="utf-8") as urls_file:
            urls_file.write(rendered_urls)

        print("Loaded URLs.")
