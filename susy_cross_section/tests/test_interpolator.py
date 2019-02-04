"""Test codes."""

from __future__ import absolute_import, division, print_function  # py2

import itertools
import logging
import pathlib
import unittest

import numpy
from nose.tools import (assert_almost_equals, assert_raises, eq_,  # noqa: F401
                        ok_, raises)

from susy_cross_section.cross_section_table import CrossSectionTable
from susy_cross_section.interpolator import (Scipy1dInterpolator,
                                             ScipyGridInterpolator)

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
        self.dirs = {
            'lhc_wg': pathlib.Path(__file__).parent / '..' / 'data' / 'lhc_susy_xs_wg',
            'fastlim8': pathlib.Path(__file__).parent / '..' / 'data' / 'fastlim' / '8TeV' / 'NLO+NLL',
            'fastlim8mod': pathlib.Path(__file__).parent / 'data',
        }

    def test_scipy_1d_interpolator(self):
        """Verify Scipy1dInterpolator."""
        table = CrossSectionTable(self.dirs['lhc_wg'] / '13TeVn2x1wino_cteq_pm.csv')
        for kind in ['linear', 'slinear', 'quadratic', 'cubic']:
            for axes in ['linear', 'log', 'loglog', 'loglinear']:
                fit = Scipy1dInterpolator(kind=kind, axes=axes).interpolate(table, 'xsec')
                # on the grid points:
                # 300.0: 379.23, -0.47, -4.8, 0.4, 4.7 == 379.23 -18.29 +17.89
                # 325.0: 276.17, -0.44, -5.1, 0.4, 4.8 == 276.17 -14.14 +13.30
                self._assert_all_close(fit.tuple_at(300), (379.23, 17.89, -18.29), decimal=2)
                assert_almost_equals(fit(325), 276.17, 2)
                assert_almost_equals(fit.unc_p_at(325), +13.30, 2)
                assert_almost_equals(fit.unc_m_at(325), -14.14, 2)
                assert_almost_equals(fit(325, unc_level=1), 276.17 + 13.3, 2)
                assert_almost_equals(fit(325, unc_level=-1), 276.17 - 14.14, 2)
                assert_almost_equals(fit(325, unc_level=0.5), 276.17 + 13.3 * 0.5, 2)
                assert_almost_equals(fit(325, unc_level=-2), 276.17 - 14.14 * 2, 1)

                # interpolation: for uncertainty, returns sensible results
                ok_(13.30 < fit.unc_p_at(312.5) < 17.89)
                ok_(14.14 < -fit.unc_m_at(312.5) < 18.29)
                if kind == 'linear':
                    if axes == 'linear':
                        x, y = (300 + 325) / 2, (379.23 + 276.17) / 2
                    elif axes == 'loglinear':
                        x, y = (300 * 325)**0.5, (379.23 + 276.17) / 2
                    elif axes == 'log':
                        x, y = (300 + 325) / 2, (379.23 * 276.17) ** 0.5
                    else:
                        x, y = (300 * 325) ** 0.5, (379.23 * 276.17) ** 0.5
                    assert_almost_equals(fit(x), y, 2)
                else:
                    ok_(276.17 < fit(312.5) < 379.23)

    def test_scipy_1d_interpolator_nonstandard_args(self):
        """Verify Scipy1dInterpolator accepts/refuses argument correctly."""
        table = CrossSectionTable(self.dirs['lhc_wg'] / '13TeVn2x1wino_cteq_pm.csv')
        fit = Scipy1dInterpolator().interpolate(table, 'xsec')
        for m in ['f0', 'fp', 'fm', 'unc_p_at', 'unc_m_at', 'tuple_at']:
            test_method = getattr(fit, m)
            value = test_method(333.3)
            if m == 'tuple_at':
                # the output should be (3,) array (or 3-element tuple)
                eq_(numpy.array(value).shape, (3,))
                # method should accept 0-dim ndarray
                eq_(test_method(numpy.array(333.3)), value)
                # method should accept keyword arguments
                eq_(test_method(m_wino=333.3), value)
            else:
                # the output should be float or ndarray with 0-dim, not arrays.
                ok_(self._is_scalar_number(value))
                # method should accept 0-dim ndarray
                eq_(test_method(numpy.array(333.3)), value)
                # method should accept keyword arguments
                eq_(test_method(m_wino=333.3), value)

            # method should not accept arrays or numpy.ndarray with >0 dim.
            for bad_input in ([333.3], [[333.3]], [333.3, 350]):
                with assert_raises(TypeError):
                    test_method(bad_input)
                with assert_raises(TypeError):
                    test_method(numpy.array(bad_input))
                with assert_raises(TypeError):
                    test_method(m_wino=bad_input)

    def test_scipy_grid_interpolator(self):
        """Verify ScipyGridInterpolator."""
        table = CrossSectionTable(self.dirs['fastlim8mod'] / 'sg_8TeV_NLONLL_modified.xsec')
        midpoint = {
            'linear': lambda x, y: (x + y) / 2,
            'log': lambda x, y: (x * y) ** 0.5,
        }
        for x1a, x2a, ya in itertools.product(['linear', 'log'], repeat=3):
            for kind in ['linear', 'spline']:
                print(kind, x1a, x2a, ya)
                fit = ScipyGridInterpolator([x1a, x2a], ya, kind=kind).interpolate(table, 'xsec')
                # on the grid points:
                # 700    1400   0.0473379597888      0.00905940683923
                # 700    1450   0.0382279746207      0.0075711349465
                # 750    1400   0.0390134257995      0.00768847466247
                # 750    1450   0.0316449395656      0.0065050745643
                self._assert_all_close(fit.tuple_at(700, 1400), (0.04734, 0.00906, -0.00906), decimal=5)
                assert_almost_equals(fit(700, 1400), 0.04734, 5)
                assert_almost_equals(fit.unc_p_at(700, 1400), +0.00906, 5)
                assert_almost_equals(fit.unc_m_at(700, 1400), -0.00906, 5)
                assert_almost_equals(fit(700, 1400, unc_level=1), 0.04734 + 0.00906 * 1, 5)
                assert_almost_equals(fit(700, 1400, unc_level=-1), 0.04734 + 0.00906 * -1, 5)
                assert_almost_equals(fit(750, 1450, unc_level=0.5), 0.03164 + 0.00651 * 0.5, 5)
                assert_almost_equals(fit(750, 1450, unc_level=-1.5), 0.0316449 + 0.006505 * -1.5, 5)

                # interpolation: for uncertainty, returns sensible results
                for interp_axis in (1, 2):
                    x1 = midpoint[x1a](700, 750) if interp_axis == 1 else 700
                    x2 = midpoint[x2a](1400, 1450) if interp_axis == 2 else 1400
                    y_upperend = 0.0390134 if interp_axis == 1 else 0.03822797
                    if kind == 'linear':
                        assert_almost_equals(fit(x1, x2), midpoint[ya](0.0473379, y_upperend), 5)
                    else:
                        ok_(y_upperend < fit(x1, x2) < 0.047337959)
                    ok_(0.0075711 < fit.unc_p_at(x1, x2) < 0.0090594)
                    ok_(0.0075711 < -fit.unc_m_at(x1, x2) < 0.0090594)
                ok_(0.0316449 < fit(725, 1425) < 0.0473378)
                ok_(0.0065051 < fit.unc_p_at(725, 1425) < 0.0090594)
                ok_(0.0065051 < -fit.unc_m_at(725, 1425) < 0.0090594)

    def test_scipy_grid_interpolator_nonstandard_args(self):
        """Verify ScipyGridInterp accepts/refuses args correctly."""
        table = CrossSectionTable(self.dirs['fastlim8mod'] / 'sg_8TeV_NLONLL_modified.xsec')

        for kind in ['linear', 'spline']:
            fit = ScipyGridInterpolator(['id', 'id'], 'id', kind=kind).interpolate(table, 'xsec')
            for m in ['f0', 'fp', 'fm', 'unc_p_at', 'unc_m_at', 'tuple_at']:
                test_method = getattr(fit, m)
                value = test_method(777, 888)
                if m == 'tuple_at':
                    # the output should be (3,) array (or 3-element tuple)
                    eq_(numpy.array(value).shape, (3,))
                else:
                    # it is a scalar
                    ok_(self._is_scalar_number(value))
                # method should accept keyword arguments
                eq_(test_method(msq=777, mgl=888), value)
                eq_(test_method(mgl=888, msq=777), value)
                eq_(test_method(777, mgl=888), value)

                # method should not accept arrays or numpy.ndarray with >0 dim.
                for bad_input in ([777, 888], [[777]], [[777, 888], [789, 890]], [777, 888, 999]):
                    with assert_raises(TypeError):
                        test_method(bad_input)
                    with assert_raises(TypeError):
                        test_method(numpy.array(bad_input))
                with assert_raises(KeyError):
                    test_method(777, 888, m_wino=100)
                with assert_raises(KeyError):
                    test_method(777, m_wino=100)
                with assert_raises(KeyError):
                    test_method(m_wino=100)
                with assert_raises(TypeError):
                    test_method()
                with assert_raises(TypeError):
                    test_method(777)
