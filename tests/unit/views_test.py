"""Unit test classes for views.py functions."""

import pytest

from openapi_to_django import views


def test_generate_views_context():
    pass


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
