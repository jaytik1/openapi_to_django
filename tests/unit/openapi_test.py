"""Unit test classes for urls.py functions."""

import pytest

from openapi_to_django import openapi
from openapi_to_django.exceptions import ParameterError
from openapi_to_django.openapi import PathData


class TestGetPathsData:
    """Test functions for the get_paths_data() method."""

    @pytest.mark.parametrize(
        "openapi_data",
        [{}, {"openapi": "3.1.1"}],
    )
    def test_no_paths(self, openapi_data):
        assert openapi.get_paths_data(openapi_data) == []

    @pytest.mark.parametrize(
        ["openapi_data", "result"],
        [
            (
                {"paths": {"/example": {}}},
                [PathData(openapi_path="/example", path_params={})],
            ),
            (
                {"paths": {"/example": {}, "/index": {}}},
                [
                    PathData(openapi_path="/example", path_params={}),
                    PathData(openapi_path="/index", path_params={}),
                ],
            ),
        ],
    )
    def test_paths_no_params(self, openapi_data, result):
        assert openapi.get_paths_data(openapi_data) == result

    @pytest.mark.parametrize(
        ["openapi_data", "result"],
        [
            (
                {
                    "paths": {
                        "/example/{id}": {
                            "get": {
                                "parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}]
                            }
                        }
                    }
                },
                [PathData(openapi_path="/example/{id}", path_params={"id": "int"})],
            ),
            (
                {
                    "paths": {
                        "/index": {},
                        "/example/{id}": {
                            "get": {
                                "parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}]
                            }
                        },
                    }
                },
                [
                    PathData(openapi_path="/index", path_params={}),
                    PathData(openapi_path="/example/{id}", path_params={"id": "int"}),
                ],
            ),
            (
                {
                    "paths": {
                        "/example/{id}": {
                            "get": {
                                "parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}]
                            }
                        },
                        "/users/{username}": {
                            "parameters": [{"name": "username", "in": "path", "schema": {"type": "string"}}]
                        },
                    }
                },
                [
                    PathData(openapi_path="/example/{id}", path_params={"id": "int"}),
                    PathData(openapi_path="/users/{username}", path_params={"username": "str"}),
                ],
            ),
        ],
    )
    def test_paths_valid_params(self, openapi_data, result):
        assert openapi.get_paths_data(openapi_data) == result

    @pytest.mark.parametrize(
        "openapi_data",
        [
            {
                "paths": {
                    "/example/{id}": {
                        "parameters": [{"name": "id", "in": "path", "schema": {"type": "string"}}],
                        "get": {"parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}]},
                    }
                }
            },
            {
                "paths": {
                    "/example/{id}": {
                        "get": {"parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}]},
                        "post": {"parameters": [{"name": "id", "in": "path", "schema": {"type": "string"}}]},
                    }
                }
            },
            {
                "paths": {
                    "/example/{id}": {
                        "get": {
                            "parameters": [
                                {"name": "id", "in": "path", "schema": {"type": "integer"}},
                                {"name": "id", "in": "path", "schema": {"type": "string"}},
                            ]
                        }
                    }
                }
            },
            {
                "paths": {
                    "/example/{id}": {
                        "parameters": [
                            {"name": "id", "in": "path", "schema": {"type": "integer"}},
                            {"name": "id", "in": "path", "schema": {"type": "string"}},
                        ]
                    }
                }
            },
        ],
    )
    def test_paths_conflicting_params(self, openapi_data):
        with pytest.raises(ParameterError):
            openapi.get_paths_data(openapi_data)


def test_parse_path_params():
    pass
