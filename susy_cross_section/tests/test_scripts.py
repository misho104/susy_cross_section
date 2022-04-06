"""Test codes."""

from __future__ import absolute_import, division, print_function  # py2

import logging
import os
import pathlib
import unittest

from click.testing import CliRunner
import pytest

from susy_cross_section import scripts

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TestScripts(unittest.TestCase):
    """Test codes for command-line scripts."""

    def assert_success(self, runner_return):
        """Assert the runner has done with exit_code==0."""
        # log if not success
        if runner_return.exit_code:
            logger.debug("%s", runner_return.__dict__)
        # assert success
        assert runner_return.exit_code == 0

    def setUp(self):
        """Set up."""
        self.data_dir = pathlib.Path(__file__).parent / "data"
        self.runner = CliRunner()

    def test_main(self):
        """Check the main command is successfully executed."""
        ret = self.runner.invoke(scripts.main)
        self.assert_success(ret)

    def test_list(self):
        """Assert behavior of LIST command."""
        full = self.runner.invoke(scripts.cmd_list)
        self.assert_success(full)
        full_lines = full.output.splitlines()

        all = self.runner.invoke(scripts.cmd_list, ["--all"])
        self.assert_success(all)
        all_lines = all.output.splitlines()

        # without --all option, only named tables are shown.
        for line in full_lines:
            assert not line.startswith("\t")

        # with --all option, tables with no name are also shown.
        assert len(all_lines) >= len(full_lines)
        for line in full_lines:
            assert line in all_lines

        # if arguments are given, lines with the arguments are shown.
        expected = [
            line
            for line in full_lines
            if ("8tev" in line.lower() and "cteq" in line.lower())
        ]
        actual = self.runner.invoke(scripts.cmd_list, ["8TeV", "CTEQ"])
        self.assert_success(actual)

        actual_lines = actual.output.splitlines()
        assert len(actual_lines) == len(expected)
        for line in actual_lines:
            assert line in expected

    def test_list_fullpath(self):
        """Assert behavior of LIST command with --full option."""
        original_dir = os.getcwd()
        os.chdir("./docs")  # move to any directory
        full = self.runner.invoke(scripts.cmd_list, ["--full"])
        self.assert_success(full)
        all_lines = full.output.splitlines()
        for line in all_lines:
            print(line)
            _, path = line.split("\t")
            assert os.path.exists(path)
        os.chdir(original_dir)

    def test_show(self):
        r = self.runner.invoke(scripts.show, ["13TeV.ss10"])
        self.assert_success(r)

    def test_get(self):
        """Assert that command_get runs without error."""
        result = {}
        for mass in [300, 350]:
            result[mass] = self.runner.invoke(
                scripts.get, ["13TeV.slepslep.ll", mass.__str__()]
            )  # py2
            self.assert_success(result[mass])
        assert result[300].output.strip() == "(0.004508 +0.000099 -0.000095) pb"
        assert result[350].output.strip() == "(0.002378 +0.000062 -0.000058) pb"

    def test_get_two_args(self):
        """Test get command for two-argument case."""
        ret = self.runner.invoke(scripts.get, ["13TeV.ss10", "600", "700"])
        self.assert_success(ret)
        assert ret.output.strip() == "(4.84 +0.17 -0.22) pb"

    def test_get_invalid_args(self):
        """Test get command for insufficient / excessive arguments."""
        cases = [
            ["13TeV.slepslep.ll"],
            ["13TeV.slepslep.ll", "800", "800"],
            ["13TeV.slepslep.ll", "800", "800", "800"],
            ["13TeV.ss10"],
            ["13TeV.ss10", "800"],
            ["13TeV.ss10", "800", "800", "800"],
        ]
        for case in cases:
            ret = self.runner.invoke(scripts.get, case)
            assert ret.exit_code != 0

    def test_get_with_table_names(self):
        """Assert that command_get correctly parse --name option."""
        cases = [
            ["13TeV.gg.decoup", "xsec_lo", "2000", "(0.00036 +0.00015 -0.00011) pb"],
            ["13TeV.gg.decoup", "xsec_nlo", "2000", "(0.00063 +0.00015 -0.00015) pb"],
            ["13TeV.gg.decoup", "xsec", "2000", "(0.00101 +0.00019 -0.00020) pb"],
        ]
        for table, name, mass, expected in cases:
            ret = self.runner.invoke(scripts.get, [table, "--name=" + name, mass])
            self.assert_success(ret)
            assert ret.output.strip() == expected

    def test_get_with_invlaid_table_names(self):
        """Assert that command_get complains for nonexisting table name."""
        ret = self.runner.invoke(
            scripts.get, ["13TeV.gg", "--name=INVAL1D", "2000", "800"]
        )
        assert ret.exit_code != 0

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
            assert result[mass].exit_code == 0
            assert len(output[mass]) == 3
        assert output[450][0] == pytest.approx(73.4361, abs=0.0001)
        assert output[450][1] == pytest.approx(6.2389, abs=0.0001)
        assert output[450][2] == pytest.approx(-6.2389, abs=0.0001)
        assert output[475][0] == pytest.approx(58.0811, abs=0.0001)
        assert output[475][1] == pytest.approx(5.05005, abs=0.00001)
        assert output[475][2] == pytest.approx(-5.05005, abs=0.00001)

        assert output[450][0] > output[458][0] > output[475][0]
        assert output[450][1] > output[458][1] > output[475][1]
        assert output[450][2] < output[458][2] < output[475][2]
