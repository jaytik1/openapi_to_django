# OpenAPI to Django

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3c78a9)](https://www.python.org/downloads/release/python-31112/) [![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1-85ea2d)](https://spec.openapis.org/oas/v3.1.1.html) [![Django 5.1](https://img.shields.io/badge/Django-5.1-0c4b33)](https://docs.djangoproject.com/en/5.1/releases/5.1.10/) [![MIT License](https://img.shields.io/badge/License-MIT-orange)](https://opensource.org/license/mit)

**Note that this project is currently a pre-release and shouldn't be treated as stable.**

## Overview

This is a Python project used to generate Django code from OpenAPI documents.

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

## Generating Django Code

Once installed, use the `openapi_to_django` command line tool to generate Django code. The tool requires an OpenAPI document to be specified, which can be either a JSON or YAML file, examples of which are in the `openapi/` folder. Currently, `urls.py` and `views.py` are generated from the specified OpenAPI document when the tool is used.

Below are some examples of how the tool can be used.

```shell

```

## Features

- Generates code from an OpenAPI document for both new and existing Django projects
  - Generates Django paths in a `urls.py` file for each path in the given OpenAPI document
  - Generates corresponding functions in a `views.py` file for each OpenAPI path
- Example OpenAPI documents are provided (`openapi/example.yaml` and `openapi/example.json`)
  - Designed to cover a range of OpenAPI 3.1 features to demonstrate the project
  - Contains examples of endpoints supporting GET, PUT, POST, DELETE, OPTIONS, HEAD, PATCH and TRACE operations
  - Contains examples of each data type permitted by the specification (`null`, `boolean`, `object`, `array`, `number`, `string` and `integer`), as well as various `format` values
  - Contains components which are reused in various places in the document, including requests, responses, schemas and a basic security scheme

## FAQs

### What are template files and how do I use them?

- Template files have the extension `.py-tpl` and can be found in the `templates/` folder
- They are used by Django to render files in a specific way, and are written in the [Django template language](https://docs.djangoproject.com/en/5.1/ref/templates/language/)
  - As well as in this project, they are used by Django's built-in `startproject` and `startapp` commands
- The template files for this project are used to generate a Django project with `main.py` and generate files with the `loadopenapi` command
- `urls.py-tpl` and `views.py-tpl` are the key files, as they determine how OpenAPI paths are converted to Django paths and view functions
- If you don't like how they render, you can create your own template files and use them with `loadopenapi`'s `--urls-template` and `--views-template` arguments!

## Licensing

- Licenses for the project can be found in `LICENSES/`
- `LICENSE`: This repository is distributed under the [MIT License](https://opensource.org/license/mit).
- `LICENSE_DJANGO`: As elements of the Django source code have been used (including project and app templates, as well as some template rendering systems), the Django BSD 3-Clause License file is also included.
