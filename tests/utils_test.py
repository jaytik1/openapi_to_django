from src.openapi_to_django import utils


def test_write_file_from_template():
    pass


class TestGetTokensFromUri:
    """Test functions for the get_tokens_from_uri() method."""

    def test_no_tokens(self):
        assert utils.get_tokens_from_uri("/") == []

    def test_single_token(self):
        assert utils.get_tokens_from_uri("/example") == ["example"]

    def test_multiple_tokens(self):
        assert utils.get_tokens_from_uri("/example/page") == ["example", "page"]

    def test_get_parameter_start(self):
        assert (utils.get_tokens_from_uri("/{id}/example")) == ["{id}", "example"]

    def test_get_parameter_middle(self):
        assert (utils.get_tokens_from_uri("/example/{id}/profile")) == ["example", "{id}", "profile"]

    def test_get_parameter_end(self):
        assert (utils.get_tokens_from_uri("/example/{id}")) == ["example", "{id}"]

    def test_contiguous_slashes(self):
        # TODO consider alternative behaviours
        assert (utils.get_tokens_from_uri("///example//page")) == ["example", "page"]

    def test_no_slashes(self):
        assert (utils.get_tokens_from_uri("example")) == []

    def test_no_leading_slash(self):
        assert (utils.get_tokens_from_uri("example/page")) == []


def test_generate_relative_import():
    pass
