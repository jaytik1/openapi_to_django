# OpenAPI to Django

Built in [![Python 3.11.2](https://img.shields.io/badge/Python-3.11.2-3c78a9)](https://www.python.org/downloads/release/python-3112/) for [![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1-85ea2d)](https://spec.openapis.org/oas/v3.1.1.html) under [![MIT License](https://img.shields.io/badge/License-MIT-orange)](https://opensource.org/license/mit).

## Overview

This is a Python project designed to convert OpenAPI documents to skeleton Django projects.

While popular tools like [FastAPI](https://github.com/fastapi/fastapi) can generate OpenAPI documents from Python code (which is itself very useful), there are fewer available to do the inverse, generating a backend server from an OpenAPI document. OpenAPITools' [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator) includes generating server stubs from OpenAPI documents, but it currently doesn't support Django (as of 8th Jan 2025), so I decided I'd give it a go!

## Features

- Example OpenAPI documents
  - Currently just `openapi/example.yaml`, with `openapi/example.json` coming soon
  - Designed to cover a range of OpenAPI 3.0 features to demonstrate the project
  - Contains examples of endpoints supporting GET, PUT, POST, DELETE, OPTIONS, HEAD, PATCH and TRACE operations
  - Contains examples of each data type permitted by the specification (`null`, `boolean`, `object`, `array`, `number`, `string` and `integer`), as well as various `format` values
  - ...

## Future Work

*See the respository's GitHub Issues for nearby updates.*

- CI support to ensure Django code always matches the OpenAPI document
- Support multi-document OpenAPI Descriptions (OADs)
