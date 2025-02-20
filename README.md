# OpenAPI to Django

Built in [![Python 3.11.2](https://img.shields.io/badge/Python-3.11.2-3c78a9)](https://www.python.org/downloads/release/python-3112/) for [![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1-85ea2d)](https://spec.openapis.org/oas/v3.1.1.html) under [![MIT License](https://img.shields.io/badge/License-MIT-orange)](https://opensource.org/license/mit).

## Overview

This is a Python project used to generate Django files and code from OpenAPI documents.

While popular tools like [FastAPI](https://github.com/fastapi/fastapi) can generate OpenAPI documents from Python code, there are fewer tools available to do the opposite, generating a backend server from an OpenAPI document. OpenAPITools' [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator) includes generating server stubs from OpenAPI documents, but it currently doesn't support Django (as of 8th Jan 2025), so I decided I'd give it a go!

## Setup

```bash
# create a Python virtual environment
python3 -m venv .venv

# activate the virtual environment
source .venv/bin/activate   # Linux / MacOS
.venv\Scripts\activate.bat  # Windows

# install required packages
pip install -r requirements.txt
```

## Creating a New Django Project

This repository includes a helper script `src/main.py`, used for generating a new Django project and loading an OpenAPI document in one go. The commands below give some examples of how this script can be used:

```bash
# example: view all arguments for the script (START HERE)
python3 src/main.py --help

# example: create a new project with a specified project name
python3 src/main.py --project-name example_project myopenapi.json

# example: create a new project with specified project and app names, with the OpenAPI file type specified as YAML
python3 src/main.py --project-name example_project --app-name example_app --file-type yaml openapidoc
```

## Using in an Existing Django Project

The `loadopenapi.py` script be installed as a command in an existing Django project (see the FAQs below for instructions). The commands below demonstrate how the command can be used:

```bash
# example: view all arguments for the script (START HERE)
python3 manage.py loadopenapi --help

# example: load a YAML OpenAPI document using the provided templates
python3 manage.py loadopenapi \
--urls-template ../templates/urls.py-tpl --views-template ../templates/views.py-tpl \
--file-type yaml openapidoc

# example: load an OpenAPI document using the provided templates to specific locations
python3 manage.py loadopenapi \
--urls-template ../templates/urls.py-tpl --views-template ../templates/views.py-tpl \
--urls-target myproject/myproject/urls.py --views-target myproject/myapp/views.py \
openapi.json
```

## Features

- Supports loading the generated content to both new and existing Django projects
- Generates Django paths in a `urls.py` file for each path in the given OpenAPI document
- Generates corresponding functions in a `views.py` file for each OpenAPI path
- Example OpenAPI documents are provided (`openapi/example.yaml` and `openapi/example.json`)
  - Designed to cover a range of OpenAPI 3.1 features to demonstrate the project
  - Contains examples of endpoints supporting GET, PUT, POST, DELETE, OPTIONS, HEAD, PATCH and TRACE operations
  - Contains examples of each data type permitted by the specification (`null`, `boolean`, `object`, `array`, `number`, `string` and `integer`), as well as various `format` values
  - Contains components which are reused in various places in the document, including requests, responses, schemas and a basic security scheme

## FAQs

Q: *How can I install the `loadopenapi` command in my Django project? When trying to run `python3 manage.py loadopenapi`, it says "Unknown command: 'loadopenapi'".*

A:
- Make sure your Django project has an app inside (can be created with `python3 manage.py startapp <name>`)
- Make sure the Django app is included in the `INSTALLED_APPS` list in the project's `settings.py` file
- Make sure the `loadopenapi.py` file exists in the `management/commands/` directory of the Django app (create these directories if needed, then copy `loadopenapi.py` from the `src/` folder)
- You should then be able to run `python3 manage.py loadopenapi` successfully!

Q: *What are template files and how do I use them?*

A:
- Template files have the extension `.py-tpl` and can be found in the `templates/` folder
- They are used by Django to render files in a specific way, and are written in the [Django template language](https://docs.djangoproject.com/en/5.1/ref/templates/language/)
- As well as this program, they are used by Django's built-in `startproject` and `startapp` commands
- The template files for this project are used to generate a Django project with `main.py` and generate files with the `loadopenapi` command
- The `urls.py-tpl` and `views.py-tpl` are the key files, as they determine how OpenAPI paths are converted to Django paths and view functions
- If you don't like how they render, you can create your own template files and use them with `loadopenapi`'s `--urls-template` and `--views-template` arguments!

## Licensing

- This repository is distributed under the MIT license
  - See the `LICENSE` file
- As elements of the Django source code have been copied and modified (including project and app templates, as well as some template rendering), the Django 5.1.5 BSD-3 Clause LICENSE file is also included
  - See the `LICENSE_DJANGO` file
