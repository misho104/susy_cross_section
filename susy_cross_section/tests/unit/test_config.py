from __future__ import absolute_import, division, print_function  # py2

import pathlib
import unittest

import pytest

from susy_cross_section import config


class TestConfig(unittest.TestCase):
    """UnitTest for `susy_cross_section.config`."""

    package_dir = pathlib.Path(__file__).parent.parent.parent

    def test_table_paths(self):
        """Assert table_paths give paths to the files."""
        for table_key in config.table_names.keys():
            grid, info = config.table_paths(table_key)

            assert grid
            if info is None:
                info = grid.with_suffix(".info")

            assert (self.package_dir / grid).is_file
            assert (self.package_dir / info).is_file

    def test_table_paths_absolute(self):
        """Assert table_paths give absolute paths if absolute is True."""
        for table_key in config.table_names.keys():
            grid, info = config.table_paths(table_key)
            abs_grid, abs_info = config.table_paths(table_key, absolute=True)

            assert abs_grid
            assert abs_grid.is_absolute()
            assert abs_grid.resolve() == grid.resolve()

            if abs_info is None:
                assert info is None
            else:
                assert abs_info
                assert abs_info.is_absolute()
                assert abs_info.resolve() == info.resolve()

    def test_table_paths_missing(self):
        """Assert table_paths return None/none for missing keys."""
        grid, info = config.table_paths("nonexisting_table_key!!!")
        assert grid is None
        assert info is None

    def test_parse_table_values(self):
        """Assert parse_table_values handle various types of data."""
        cases = [
            ["grid_only", ("grid_only", None)],
            [("grid_only"), ("grid_only", None)],
            [("grid", None), ("grid", None)],
            [("grid", "info"), ("grid", "info")],
        ]
        for argument, expected in cases:
            assert config.parse_table_value(argument) == expected

        for argument in ["", None]:
            with pytest.raises(ValueError):
                config.parse_table_value(argument)
