# OpenAPI to Django

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3c78a9)](https://www.python.org/downloads/release/python-31112/) [![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1-85ea2d)](https://spec.openapis.org/oas/v3.1.1.html) [![Django 5.1](https://img.shields.io/badge/Django-5.1-0c4b33)](https://docs.djangoproject.com/en/5.1/releases/5.1.10/) [![MIT License](https://img.shields.io/badge/License-MIT-orange)](https://opensource.org/license/mit)

**Note that this project is currently a pre-release so changes are likely to occur.**

Please use the repository's [GitHub Discussions](https://github.com/jaytik1/openapi_to_django/discussions) to report bugs, suggest features and ask any questions. Adding bug reports and feature requests as GitHub Issues may be supported in the future.

## Overview

OpenAPI to Django is a Python tool used to generate Django code from OpenAPI documents.

While popular tools like [FastAPI](https://github.com/fastapi/fastapi) can generate OpenAPI documents from Python code, there are fewer tools available to do the opposite, generating a backend server from an OpenAPI document. OpenAPITools' [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator) includes generating server stubs from OpenAPI documents, but it currently doesn't support Django (as of 30th May 2025), so I decided I'd give it a go!

## Setup

### Installing with pipx

Use `pipx install openapi_to_django` to install OpenAPI to Django from PyPI. Instructions for installing `pipx` can be found [here](https://packaging.python.org/en/latest/guides/installing-stand-alone-command-line-tools/).

### Building from Source

The package can also be built from source. This requires Poetry to be installed, use `pipx install poetry` or see instructions [here](https://python-poetry.org/docs/#installation).

```shell
# clone the repository
git clone git@github.com:jaytik1/openapi_to_django.git
cd openapi_to_django/

# use Poetry to install dependencies
poetry install

# build the package (output in the dist/ folder)
poetry build
```

## Using the Tool

Once installed, use the `openapi_to_django` command line tool to generate Django code. The tool requires an OpenAPI document to be specified, which can be either a JSON or YAML file, examples of which are in the `openapi/` folder. Custom templates can also be passed as inputs to be used by the tool.

Currently, Django `urls.py` and `views.py` files are generated from the specified OpenAPI document. The tool can be used in either "projects" or "files" mode which are described below.

### Projects Mode

Using "projects mode" (with the `projects` keyword) creates a full Django project with the generated files inside. Additional command line arguments for configuring the generated project can also be given. Below are examples of how projects mode can be used.

```shell
# view all arguments available in projects mode
openapi_to_django projects --help

# create a new project using the default variables
openapi_to_django projects openapi/example.openapi.json

# create a new project with specified project and app names
openapi_to_django projects openapi/example.openapi.json \
  --project-name example_project \
  --app-name example_app

# create a new project using custom templates
openapi_to_django projects openapi/example.openapi.json \
  --urls-template src/openapi_to_django/templates/urls.py-tpl \
  --views-template src/openapi_to_django/templates/views.py-tpl \
  --project-template src/openapi_to_django/templates/project_template/ \
  --app-template src/openapi_to_django/templates/app_template/
```

### Files Mode

Using "files mode" (with the `files` keyword) just outputs the generated `urls.py` and `views.py` files without creating a full Django project. The locations for these files can be specified, and if these files already exist, the generated code is appended to the end of the files. Below are examples of how files mode can be used.

```shell
# view all arguments available in files mode
openapi_to_django files --help

# generate files using the default variables
openapi_to_django files openapi/example.openapi.json

# output files to a custom location
openapi_to_django files openapi/example.openapi.json \
  --urls-target urls.py \
  --views-target views.py

# generate files using custom templates
openapi_to_django files openapi/example.openapi.json \
  --urls-template src/openapi_to_django/templates/urls.py-tpl \
  --views-template src/openapi_to_django/templates/views.py-tpl
```

## FAQs

### What are template files and how do I use them?

- Template files have the extension `.py-tpl` and can be found in the `templates/` folder
- They are used to render files in a specific way and are written in the [Django template language](https://docs.djangoproject.com/en/5.1/ref/templates/language/)
  - As well as in this project, they are used by Django's built-in `startproject` and `startapp` commands
- `urls.py-tpl` and `views.py-tpl` are the key files, as they determine how OpenAPI paths are converted to Django paths and view functions
- Custom templates can be passed to the tool using the appropriate arguments

## Licensing

- Licenses for the project can be found in `LICENSES/`
- `LICENSE.txt`: This repository is distributed under the [MIT License](https://opensource.org/license/mit).
- `LICENSE_DJANGO.txt`: As elements of the Django source code have been used (including project and app templates, as well as some template rendering systems), the Django BSD 3-Clause License file is also included.
