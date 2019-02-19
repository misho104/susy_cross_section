"""Test codes."""

from __future__ import absolute_import, division, print_function  # py2

import itertools
import logging
import pathlib
import unittest

import numpy
from nose.tools import assert_almost_equals, assert_raises, eq_, ok_  # noqa: F401

from susy_cross_section.interp import Scipy1dInterpolator, ScipyGridInterpolator
from susy_cross_section.interp.axes_wrapper import AxesWrapper
from susy_cross_section.table import File

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TestInterpolator(unittest.TestCase):
    """Test codes for one-dimensional cross-section fit."""

    @staticmethod
    def _is_scalar_number(obj):
        if isinstance(obj, numpy.ndarray):
            return obj.ndim == 0
        return isinstance(obj, float) or isinstance(obj, int)

    @staticmethod
    def _assert_all_close(actual, expected, decimal=None):
        for a, e in zip(actual, expected):
            assert_almost_equals(a, e, decimal)

    def setUp(self):
        """Set up."""
        cwd = pathlib.Path(__file__).parent
        self.dirs = {
            "lhc_wg": cwd / ".." / "data" / "lhc_susy_xs_wg",
            "fastlim8": cwd / ".." / "data" / "fastlim" / "8TeV" / "NLO+NLL",
            "fastlim8mod": cwd / "data",
        }

    def test_scipy_1d_interpolator(self):
        """Verify Scipy1dInterpolator."""
        table = File(self.dirs["lhc_wg"] / "13TeVn2x1wino_cteq_pm.csv")["xsec"]
        for kind in ["linear", "akima", "spline", "pchip"]:
            for axes in ["linear", "log", "loglog", "loglinear"]:
                fit = Scipy1dInterpolator(kind, axes).interpolate(table)
                # on the grid points:
                # 300.0: 379.23, -0.47, -4.8, 0.4, 4.7 == 379.23 -18.29 +17.89
                # 325.0: 276.17, -0.44, -5.1, 0.4, 4.8 == 276.17 -14.14 +13.30
                self._assert_all_close(fit.tuple_at(300), (379.23, 17.89, -18.29), 2)
                assert_almost_equals(fit(325), 276.17, 2)
                assert_almost_equals(fit.unc_p_at(325), +13.30, 2)
                assert_almost_equals(fit.unc_m_at(325), -14.14, 2)

                # interpolation: for uncertainty, returns sensible results
                ok_(13.30 < fit.unc_p_at(312.5) < 17.89)
                ok_(14.14 < -fit.unc_m_at(312.5) < 18.29)
                if kind == "linear":
                    if axes == "linear":
                        x, y = (300 + 325) / 2, (379.23 + 276.17) / 2
                    elif axes == "loglinear":
                        x, y = (300 * 325) ** 0.5, (379.23 + 276.17) / 2
                    elif axes == "log":
                        x, y = (300 + 325) / 2, (379.23 * 276.17) ** 0.5
                    else:
                        x, y = (300 * 325) ** 0.5, (379.23 * 276.17) ** 0.5
                    assert_almost_equals(fit(x), y, 2)
                else:
                    ok_(276.17 < fit(312.5) < 379.23)

    def test_scipy_1d_interpolator_nonstandard_args(self):
        """Verify Scipy1dInterpolator accepts/refuses argument correctly."""
        table = File(self.dirs["lhc_wg"] / "13TeVn2x1wino_cteq_pm.csv")["xsec"]
        fit = Scipy1dInterpolator().interpolate(table)
        for m in ["f0", "fp", "fm", "unc_p_at", "unc_m_at", "tuple_at"]:
            test_method = getattr(fit, m)
            value = test_method(333.3)
            if m == "tuple_at":
                # the output should be (3,) array (or 3-element tuple)
                eq_(numpy.array(value).shape, (3,))
            else:
                # the output should be float or ndarray with 0-dim, not arrays.
                ok_(self._is_scalar_number(value))

            # method should accept 0-dim ndarray
            eq_(test_method(numpy.array(333.3)), value)
            # method should accept arrays
            eq_(test_method([333.3]), value)
            eq_(test_method(numpy.array([333.3])), value)
            # method should accept keyword arguments
            eq_(test_method(m_wino=333.3), value)

            # method should not accept arrays or numpy.ndarray with >0 dim.
            for bad_input in ([[333.3]], [333.3, 350]):
                with assert_raises(TypeError):
                    test_method(bad_input)
                with assert_raises(TypeError):
                    test_method(numpy.array(bad_input))
                with assert_raises(TypeError):
                    test_method(m_wino=bad_input)

    def test_scipy_grid_interpolator(self):
        """Verify ScipyGridInterpolator."""
        table = File(self.dirs["fastlim8mod"] / "sg_8TeV_NLONLL_modified.xsec")["xsec"]
        midpoint = {
            "linear": lambda x, y: (x + y) / 2,
            "log": lambda x, y: (x * y) ** 0.5,
        }
        for x1a, x2a, ya in itertools.product(["linear", "log"], repeat=3):
            for kind in ["linear", "spline"]:
                wrapper = AxesWrapper([x1a, x2a], ya)
                fit = ScipyGridInterpolator(kind, wrapper).interpolate(table)
                # on the grid points:
                # 700    1400   0.0473379597888      0.00905940683923
                # 700    1450   0.0382279746207      0.0075711349465
                # 750    1400   0.0390134257995      0.00768847466247
                # 750    1450   0.0316449395656      0.0065050745643
                self._assert_all_close(
                    fit.tuple_at(700, 1400), (0.04734, 0.00906, -0.00906), decimal=5
                )
                assert_almost_equals(fit(700, 1400), 0.04734, 5)
                assert_almost_equals(fit.unc_p_at(700, 1400), +0.00906, 5)
                assert_almost_equals(fit.unc_m_at(700, 1400), -0.00906, 5)

                # interpolation: for uncertainty, returns sensible results
                for interp_axis in (1, 2):
                    x1 = midpoint[x1a](700, 750) if interp_axis == 1 else 700
                    x2 = midpoint[x2a](1400, 1450) if interp_axis == 2 else 1400
                    y_upperend = 0.0390134 if interp_axis == 1 else 0.03822797
                    if kind == "linear":
                        assert_almost_equals(
                            fit(x1, x2), midpoint[ya](0.0473379, y_upperend), 5
                        )
                    else:
                        ok_(y_upperend < fit(x1, x2) < 0.047337959)
                    ok_(0.0075711 < fit.unc_p_at(x1, x2) < 0.0090594)
                    ok_(0.0075711 < -fit.unc_m_at(x1, x2) < 0.0090594)
                ok_(0.0316449 < fit(725, 1425) < 0.0473378)
                ok_(0.0065051 < fit.unc_p_at(725, 1425) < 0.0090594)
                ok_(0.0065051 < -fit.unc_m_at(725, 1425) < 0.0090594)

    def test_scipy_grid_interpolator_nonstandard_args(self):
        """Verify ScipyGridInterp accepts/refuses args correctly."""
        table = File(self.dirs["fastlim8mod"] / "sg_8TeV_NLONLL_modified.xsec")["xsec"]

        for kind in ["linear", "spline"]:
            fit = ScipyGridInterpolator(kind).interpolate(table)
            for m in ["f0", "fp", "fm", "unc_p_at", "unc_m_at", "tuple_at"]:
                test_method = getattr(fit, m)
                value = test_method(777, 888)
                if m == "tuple_at":
                    # the output should be (3,) array (or 3-element tuple)
                    eq_(numpy.array(value).shape, (3,))
                else:
                    # it is a scalar
                    ok_(self._is_scalar_number(value))
                # method should accept keyword arguments
                eq_(test_method(msq=777, mgl=888), value)
                eq_(test_method(mgl=888, msq=777), value)
                eq_(test_method(777, mgl=888), value)

                # method should not accept invalid arrays or numpy.ndarray with >0 dim.
                for bad_input in ([[777]], [[777, 888], [789, 890]], [777, 888, 999]):
                    with assert_raises((ValueError, TypeError, IndexError)):
                        test_method(bad_input)
                    with assert_raises((ValueError, TypeError, IndexError)):
                        test_method(numpy.array(bad_input))
                with assert_raises(TypeError):
                    test_method(777, 888, m_wino=100)
                with assert_raises(TypeError):
                    test_method(777, m_wino=100)
                with assert_raises(TypeError):
                    test_method(m_wino=100)
                with assert_raises((IndexError, TypeError)):
                    test_method()
                with assert_raises((IndexError, TypeError)):
                    test_method(777)
