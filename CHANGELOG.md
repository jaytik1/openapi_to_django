# Changelog

OpenAPI to Django changelog.

The format of this document follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Version numbers adhere to [Semantic Versioning 2.0.0](https://semver.org/), with corresponding Git tags being prepended with "v". Breaking changes are in bold and start with "[BREAKING]". 

## [0.1.0] - 2025-06-18

### Added

- Generate Django `urls.py` and `views.py` files containing all paths in an OpenAPI document (PR #21, issue #17)
- `openapi_to_django` command line tool
  - `projects` mode to generate files inside a new Django project (PR #19, issue #18)
  - `files` mode to only output the `urls.py` and `views.py` files (PR #37, issue #36)
- Validate and resolve given OpenAPI files using [Prance](https://github.com/RonnyPfannschmidt/prance) (PR #34, issue #14, issue #20, issue #23)
- Example YAML OpenAPI document `openapi/example.openapi.yaml` (PR #7, issue #2)
- Example JSON OpenAPI document `openapi/example.openapi.json` (PR #11, issue #3)
- GitHub Actions workflow to perform Pytest unit tests on all components of the program (PR #35, issue #29)
- GitHub Actions workflow to perform type hint checking with mypy (PR #25, issue #24)
- GitHub Actions workflow to perform linting with Ruff (PR #28, issue #26)
- GitHub Actions workflow to create a GitHub Release draft whenever a tag is pushed (PR #42, issue #40)
- GitHub Actions workflow to automatically publish the package to PyPI when a GitHub Release is published (PR #41, issue #39)

[0.1.0]: https://github.com/jaytik1/openapi_to_django/releases/v0.1.0
