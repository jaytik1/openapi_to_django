"""Unit test classes for urls.py functions."""

from pathlib import Path

import pytest
from django.template import Context

from openapi_to_django import urls
from openapi_to_django.exceptions import ParameterError
from openapi_to_django.openapi import PathData
from openapi_to_django.urls import DjangoPath


class TestGenerateUrlsContext:
    """Test functions for the generate_urls_context() method."""

    @pytest.mark.parametrize(
        ["paths_data", "result_paths"],
        [
            # one path
            (
                [PathData(openapi_path="/example", path_params={})],
                [DjangoPath(url="example", view_name="example")],
            ),
            (
                [PathData(openapi_path="/example/{id}", path_params={"id": "int"})],
                [DjangoPath(url="example/<int:id>", view_name="example_id")],
            ),
            (
                [
                    PathData(
                        openapi_path="/example/{id}/{username}",
                        path_params={"id": "int", "username": "str"},
                    )
                ],
                [DjangoPath(url="example/<int:id>/<str:username>", view_name="example_id_username")],
            ),
            # multiple paths
            (
                [
                    PathData(openapi_path="/example", path_params={}),
                    PathData(openapi_path="/index", path_params={}),
                    PathData(openapi_path="/forum", path_params={}),
                ],
                [
                    DjangoPath(url="example", view_name="example"),
                    DjangoPath(url="index", view_name="index"),
                    DjangoPath(url="forum", view_name="forum"),
                ],
            ),
            (
                [
                    PathData(openapi_path="/example", path_params={}),
                    PathData(openapi_path="/example/{id}", path_params={"id": "int"}),
                ],
                [
                    DjangoPath(url="example", view_name="example"),
                    DjangoPath(url="example/<int:id>", view_name="example_id"),
                ],
            ),
            (
                [
                    PathData(openapi_path="/index/{username}", path_params={"username": "str"}),
                    PathData(
                        openapi_path="/example/{id}/{username}", path_params={"id": "int", "username": "str"}
                    ),
                ],
                [
                    DjangoPath(url="index/<str:username>", view_name="index_username"),
                    DjangoPath(url="example/<int:id>/<str:username>", view_name="example_id_username"),
                ],
            ),
        ],
    )
    def test_valid_paths_data(self, paths_data, result_paths):
        expected_result = Context(
            {
                "paths": result_paths,
                "urls_exists": False,
                "views_name": "views",
                "views_import": "import views",
            }
        )
        assert urls.generate_urls_context(paths_data, Path("urls.py"), Path("views.py")) == expected_result

    @pytest.mark.parametrize(
        "paths_data",
        [
            ([PathData(openapi_path="/example/{id}", path_params={})]),
            (
                [
                    PathData(openapi_path="/example", path_params={}),
                    PathData(openapi_path="/example/{id}/{username}", path_params={"id": "int"}),
                ]
            ),
            (
                [
                    PathData(openapi_path="/example/{id}/{username}", path_params={"username": "str"}),
                    PathData(openapi_path="/example", path_params={}),
                ]
            ),
            (
                [
                    PathData(
                        openapi_path="/example/{id}/{username}",
                        path_params={"id": "int", "username": "str"},
                    ),
                    PathData(openapi_path="/index/{username}", path_params={}),
                    PathData(openapi_path="/forum", path_params={}),
                ]
            ),
        ],
    )
    def test_missing_params(self, paths_data):
        with pytest.raises(ParameterError):
            urls.generate_urls_context(paths_data, Path("urls.py"), Path("views.py"))


class TestGetUrlFromPath:
    """Test functions for the get_url_from_path() method."""

    @pytest.mark.parametrize(
        ["path", "result"],
        [
            ("/", ""),  # no tokens
            ("/example", "example"),  # one token
            ("/example/profile", "example/profile"),  # two tokens
        ],
    )
    def test_no_params(self, path, result):
        """Test URLs without any path parameters."""
        assert urls.get_url_from_path(path, {}) == result

    @pytest.mark.parametrize(
        ["path", "path_params", "result"],
        [
            # one parameter
            ("/{id}", {"id": "int"}, "<int:id>"),
            ("/example/{id}", {"id": "int"}, "example/<int:id>"),
            # two parameters
            ("/{username}/blog/{id}", {"username": "str", "id": "int"}, "<str:username>/blog/<int:id>"),
        ],
    )
    def test_valid_params(self, path, path_params, result):
        """Test URLs with valid path parameters."""
        assert urls.get_url_from_path(path, path_params) == result

    @pytest.mark.parametrize(
        ["path", "path_params", "result"],
        [
            # one extra parameter
            ("/example", {"id": "int"}, "example"),
            ("/{username}/blog", {"username": "str", "id": "int"}, "<str:username>/blog"),
            # two extra parameters
            ("/example", {"username": "str", "id": "int"}, "example"),
        ],
    )
    def test_extra_params(self, path, path_params, result):
        """Test URLs with extra path parameters which the function ignores."""
        assert urls.get_url_from_path(path, path_params) == result

    @pytest.mark.parametrize(
        ["path", "path_params"],
        [
            # one missing parameter
            ("/{id}", {}),
            ("/{username}/blog/{id}", {"username": "str"}),
            # two missing parameters
            ("/{username}/blog/{id}", {}),
        ],
    )
    def test_missing_params(self, path, path_params):
        """Test URLs with undefined path parameters."""
        with pytest.raises(ParameterError):
            urls.get_url_from_path(path, path_params)
