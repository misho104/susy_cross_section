"""Interpolators of cross-section data."""

from __future__ import absolute_import, division, print_function  # py2

import logging
import sys
from typing import Any, Callable, Tuple  # noqa: F401

import scipy.interpolate

import susy_cross_section.axes_wrapper as AW

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

InterpolationType = Callable[[float], float]


class InterpolationWithUncertainties:
    """An interpolation result of values accompanied by uncertainties."""

    def __init__(self, central, central_plus_unc, central_minus_unc):
        # type: (InterpolationType, InterpolationType, InterpolationType)->None
        self.f0 = central
        self.fp = central_plus_unc
        self.fm = central_minus_unc

        self.extra_p_source = lambda _x: 0    # type: Callable[[float], float]
        self.extra_m_source = lambda _x: 0    # type: Callable[[float], float]

    # py2 does not accept single kwarg after args.
    def __call__(self, *args, **kwargs):   # py2; in py3, def __call__(self, *args, unc_level=0):
        # type: (Any, float)->float
        """Return the fitted value with requested uncertainty level."""
        unc_level = kwargs.get('unc_level', 0)  # py2
        return self.f0(*args) + (
            unc_level * self.unc_p_at(*args) if unc_level > 0 else
            unc_level * abs(self.unc_m_at(*args)) if unc_level < 0 else
            0
        )

    def tuple_at(self, *args):
        # type: (Any, float)->Tuple[float, float, float]
        """Return the tuple (central, +unc, -unc) at the fit point."""
        return float(self.f0(*args)), self.unc_p_at(*args), self.unc_m_at(*args)

    def unc_p_at(self, *args):
        # type: (Any)->float
        """Return the fitted value of positive uncertainty.

        Note that this is not the positive uncertainty of the fitting.
        """
        return ((self.fp(*args) - self.f0(*args)) ** 2 + self.extra_p_source(*args) ** 2)**0.5

    def unc_m_at(self, *args):
        # type: (Any)->float
        """Return the fitted value of negative uncertainty, which is negative.

        Note that this is not the negative uncertainty of the fitting.
        """
        return -((self.f0(*args) - self.fm(*args)) ** 2 + self.extra_m_source(*args) ** 2)**0.5


class AbstractInterpolator:
    """Abstract class for interpolators of values with 1sigma uncertainties.

    Actual interpolators, inheriting this abstract class, will perform
    interpolation of pandas data frame.
    """

    def interpolate(self, df_with_unc):
        # type: (Any)->InterpolationWithUncertainties
        """Interpolate the values accompanied by uncertainties."""
        return InterpolationWithUncertainties(
            self._interpolate(df_with_unc['value']),
            self._interpolate(df_with_unc['value'] + df_with_unc['unc+']),
            self._interpolate(df_with_unc['value'] - abs(df_with_unc['unc-'])),
        )

    def _interpolate(self, df):
        # type: (Any)->InterpolationType
        return NotImplemented  # type: ignore


class Scipy1dInterpolator(AbstractInterpolator):
    """Interpolator for values with uncertainty based on Scipy interp1d."""

    def __init__(self, kind=None, axes=None):
        # type: (str, str)->None
        self.kind = (kind or 'linear').lower()
        self.wrapper = AW.one_dim_wrapper[axes or 'linear']

    def _interpolate(self, df):
        # type: (Any)->InterpolationType
        if df.index.nlevels != 1:
            raise Exception('Scipy1dInterpolator not handle multiindex data.')
        x = [self.wrapper.wx[0](x) for x in df.index.to_numpy()]   # array(n_points)
        y = [self.wrapper.wy(y) for y in df.to_numpy()]            # array(n_points)
        return self.wrapper.correct(scipy.interpolate.interp1d(x, y, self.kind))
