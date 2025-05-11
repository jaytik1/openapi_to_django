"""Unit test classes for views.py functions."""

from pathlib import Path

import pytest
from django.template import Context

from openapi_to_django import views
from openapi_to_django.exceptions import ParameterError
from openapi_to_django.openapi import PathData
from openapi_to_django.views import DjangoView


class TestGenerateViewsContext:
    """Test functions for the generate_views_context() method."""

    @pytest.mark.parametrize(
        ["paths_data", "result_views"],
        [
            # one path
            (
                [PathData(openapi_path="/example", path_params={})],
                [DjangoView(view_name="example", params={})],
            ),
            (
                [PathData(openapi_path="/example/{id}", path_params={"id": "int"})],
                [DjangoView(view_name="example_id", params={"id": "int"})],
            ),
            (
                [
                    PathData(
                        openapi_path="/example/{id}/{username}",
                        path_params={"id": "int", "username": "str"},
                    )
                ],
                [
                    DjangoView(
                        view_name="example_id_username",
                        params={"id": "int", "username": "str"},
                    )
                ],
            ),
            # multiple paths
            (
                [
                    PathData(openapi_path="/example", path_params={}),
                    PathData(openapi_path="/index", path_params={}),
                    PathData(openapi_path="/forum", path_params={}),
                ],
                [
                    DjangoView(view_name="example", params={}),
                    DjangoView(view_name="index", params={}),
                    DjangoView(view_name="forum", params={}),
                ],
            ),
            (
                [
                    PathData(openapi_path="/example", path_params={}),
                    PathData(openapi_path="/example/{id}", path_params={"id": "int"}),
                ],
                [
                    DjangoView(view_name="example", params={}),
                    DjangoView(view_name="example_id", params={"id": "int"}),
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
                    DjangoView(view_name="index_username", params={"username": "str"}),
                    DjangoView(
                        view_name="example_id_username",
                        params={"id": "int", "username": "str"},
                    ),
                ],
            ),
        ],
    )
    def test_valid_paths_data(self, paths_data, result_views):
        expected_result = Context({"views": result_views, "views_exists": False})
        assert views.generate_views_context(paths_data, Path("views.py")) == expected_result

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
            views.generate_views_context(paths_data, Path("views.py"))


class TestGetViewFromPath:
    """Test functions for the get_view_from_path() method."""

    @pytest.mark.parametrize(
        ["path", "result"],
        [
            ("/", "index"),  # no tokens (index page)
            ("/example", "example"),  # one token
            ("/example/profile", "example_profile"),  # two tokens
        ],
    )
    def test_no_params(self, path, result):
        """Test paths without any path parameters."""
        assert views.get_view_from_path(path) == result

    @pytest.mark.parametrize(
        ["path", "result"],
        [
            # one parameter
            ("/{id}", "id"),
            ("/example/{id}", "example_id"),
            # two parameters
            ("/{username}/blog/{id}", "username_blog_id"),
        ],
    )
    def test_params(self, path, result):
        """Test paths containing path parameters."""
        assert views.get_view_from_path(path) == result
