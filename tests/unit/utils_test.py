from pathlib import Path

import pytest

from openapi_to_django import utils


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


class TestGenerateRelativeImport:
    """Test functions for the generate_relative_import() method."""

    importing_module = "example1"
    imported_module = "example2"

    @pytest.mark.parametrize(
        ["importing_path", "imported_path"],
        [
            (Path(importing_module), Path(imported_module)),  # current directory
            (Path("..", importing_module), Path("..", imported_module)),  # parent directory
            (Path("examples", importing_module), Path("examples", imported_module)),  # child directory
        ],
    )
    def test_same_directory(self, importing_path, imported_path):
        result = utils.generate_relative_import(importing_path, imported_path)
        assert result == f"import {self.imported_module}"

    def test_parent_directory(self):
        """Import a module from a parent directory."""
        importing_path = Path("examples", "importing", self.importing_module)
        imported_path = Path("examples", self.imported_module)

        result = utils.generate_relative_import(importing_path, imported_path)
        assert result == f"from examples import {self.imported_module}"

    def test_child_directory(self):
        """Import a module from a child directory."""
        importing_path = Path("examples", self.importing_module)
        imported_path = Path("examples", "imported", self.imported_module)

        result = utils.generate_relative_import(importing_path, imported_path)
        assert result == f"from imported import {self.imported_module}"

    def test_same_module(self):
        importing_path = imported_path = Path("module")

        with pytest.raises(ValueError):
            utils.generate_relative_import(importing_path, imported_path)
