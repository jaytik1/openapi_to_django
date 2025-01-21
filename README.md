# OpenAPI to Django

Built in [![Python 3.11.2](https://img.shields.io/badge/Python-3.11.2-3c78a9)](https://www.python.org/downloads/release/python-3112/) for [![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1-85ea2d)](https://spec.openapis.org/oas/v3.1.1.html) under [![MIT License](https://img.shields.io/badge/License-MIT-orange)](https://opensource.org/license/mit).

## Overview

This is a Python project designed to convert OpenAPI documents to skeleton Django projects.

While popular tools like [FastAPI](https://github.com/fastapi/fastapi) can generate OpenAPI documents from Python code, there are fewer tools available to do the opposite, generating a backend server from an OpenAPI document. OpenAPITools' [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator) includes generating server stubs from OpenAPI documents, but it currently doesn't support Django (as of 8th Jan 2025), so I decided I'd give it a go!

## Using the Tool

### Set Up a Virtual Environment

```bash
# create a virtual environment
python3 -m venv .venv

# activate the virtual environment (Linux/MacOS)
source .venv/bin/activate

# install required packages
pip install -r requirements.txt
```

### Create a Django Project

```bash
# create a Django project with chosen project and app names
python3 src/main.py -p <project_name> -a <app_name> <openapi_file>
```

### Convert OpenAPI Document Formats

The tool can convert JSON to YAML and vice versa. It outputs a copy of the file with the same name in the same directory, but with the new file extension.

```bash
# convert a JSON OpenAPI document to YAML
python3 src/main.py --convert <openapi_json_file>

# convert a YAML OpenAPI document to JSON
python3 src/main.py -convert <openapi_yaml_file>
```

## Features

- Automatically generate a Django project
  - Can specify the project and app names being generated
  - Currently only generates the base project, will use features in the OpenAPI document in the future
- Convert OpenAPI document formats
  - Can convert OpenAPI JSON documents to YAML and vice versa
- Example OpenAPI documents
  - Same document in YAML and JSON formats (`openapi/example.yaml` and `openapi/example.json`)
  - Designed to cover a range of OpenAPI 3.1 features to demonstrate the project
  - Contains examples of endpoints supporting GET, PUT, POST, DELETE, OPTIONS, HEAD, PATCH and TRACE operations
  - Contains examples of each data type permitted by the specification (`null`, `boolean`, `object`, `array`, `number`, `string` and `integer`), as well as various `format` values
  - Contains components which are reused in various places in the document, including requests, responses, schemas and a basic security scheme

## Future Work

*See the respository's GitHub Issues for nearby updates.*

- CI support to ensure Django code always matches the OpenAPI document
- Support multi-document OpenAPI Descriptions (OADs)

## Licensing

- This repository is distributed under the MIT license
  - See the `LICENSE` file
- As elements of the Django source code have been copied and modified (including project and app templates, as well as some template rendering), the Django 5.1.5 BSD-3 Clause LICENSE file is also included
  - See the `LICENSE_DJANGO` file
