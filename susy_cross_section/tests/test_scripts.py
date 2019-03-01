"""Test codes."""

from __future__ import absolute_import, division, print_function  # py2

import logging
import pathlib
import unittest

from click.testing import CliRunner
from nose.tools import assert_almost_equals, eq_, ok_, raises  # noqa: F401

from susy_cross_section import scripts

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TestScripts(unittest.TestCase):
    """Test codes for command-line scripts."""

    def setUp(self):
        """Set up."""
        self.data_dir = pathlib.Path(__file__).parent / "data"
        self.runner = CliRunner()

    def test_get(self):
        """Assert that command_get runs without error."""
        result = {}
        for mass in [300, 350]:
            result[mass] = self.runner.invoke(
                scripts.get, ["13TeV.slepslep.ll", mass.__str__()]
            )  # py2
            if result[mass].exit_code:
                logger.debug("%s", result[mass].__dict__)
            eq_(result[mass].exit_code, 0)
        eq_(result[300].output.strip(), "(4.43 +0.19 -0.24) fb")
        eq_(result[350].output.strip(), "(2.33 +0.11 -0.14) fb")

    def test_get_simple(self):
        """Assert that command_get returns sensible interpolation results."""
        result = {}
        output = {}
        for mass in [450, 458, 475]:
            result[mass] = self.runner.invoke(
                scripts.get, ["-1", "13TeV.n2x1+-.wino", mass.__str__()]
            )  # py2
            output[mass] = [float(x) for x in result[mass].output.strip().split(" ")]
            logger.debug("Exit code %s: %s", result[mass].exit_code, output[mass])
            eq_(result[mass].exit_code, 0)
            eq_(len(output[mass]), 3)
        assert_almost_equals(output[450][0], 73.4361)
        assert_almost_equals(output[450][1], 6.2389)
        assert_almost_equals(output[450][2], -6.2389)
        assert_almost_equals(output[475][0], 58.0811)
        assert_almost_equals(output[475][1], 5.05005)
        assert_almost_equals(output[475][2], -5.05005)

        assert output[450][0] > output[458][0] > output[475][0]
        assert output[450][1] > output[458][1] > output[475][1]
        assert output[450][2] < output[458][2] < output[475][2]
