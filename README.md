# OpenAPI to Django

Built in [![Python 3.11.2](https://img.shields.io/badge/Python-3.11.2-3c78a9)](https://www.python.org/downloads/release/python-3112/) for [![OpenAPI 3.0.3](https://img.shields.io/badge/OpenAPI-3.0.3-85ea2d)](https://spec.openapis.org/oas/v3.0.3.html) under [![MIT License](https://img.shields.io/badge/License-MIT-orange)](https://opensource.org/license/mit).

## Overview

This is a Python project designed to convert OpenAPI specifications to skeleton Django projects.

While popular tools like [FastAPI](https://github.com/fastapi/fastapi) can generate OpenAPI specs from Python code (which is itself very useful), there are fewer available to do the inverse, generating a backend server from an OpenAPI spec document. OpenAPITools' [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator) supports generating server stubs from OpenAPI specifications, but it currently doesn't support Django (as of 8th Jan 2025), so I decided I'd give it a go!

## Features

- The repo exists!

## Future Work

- CI support to ensure Django code always matches the OpenAPI specification
- Update to support OpenAPI v3.1.1
