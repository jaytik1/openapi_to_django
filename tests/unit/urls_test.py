import pytest

from openapi_to_django import urls
from openapi_to_django.exceptions import ParameterError


def test_generate_urls_context():
    pass


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
