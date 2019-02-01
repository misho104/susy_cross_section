"""Interpolators of cross-section data."""

from __future__ import absolute_import, division, print_function  # py2

import logging
import sys
from typing import (Any, Callable, List, Sequence, Tuple, Union,  # noqa: F401
                    cast)

import numpy
import scipy.interpolate

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

InterpolationType = Tuple[Any, Callable[[float], float], Callable[[float], float]]


class InterpolationWithUncertainties:
    """An interpolation result of values accompanied by uncertainties."""

    def __init__(self, central, central_plus_unc, central_minus_unc):
        # type: (Interpolation, Interpolation, Interpolation)->None
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


WrapperType = Callable[[float], float]


class Interpolation:
    """An interpolation result with modified axes."""

    def __init__(self, f, x_wrapper, y_wrapper):
        # type: (Any, WrapperType, WrapperType)->None
        self.f = f                  # type: Any
        self.x_wrapper = x_wrapper  # type: WrapperType
        self.y_wrapper = y_wrapper  # type: WrapperType

    def __call__(self, x):
        # type: (float)->float
        """Return interpolation result with corrected axes."""
        return self.y_wrapper(self.f(self.x_wrapper(x)))


class AbstractInterpolator:
    """Abstract class for interpolators of values with 1sigma uncertainties.

    Actual interpolators, inheriting this abstract class, will perform
    interpolation of pandas data frame.
    """

    @staticmethod
    def dim_index(df):
        # type: (Any)->int
        """Return the dimension of dataframe index."""
        return len(df.index.names)

    @staticmethod
    def axes_wrapper(axes_type, x, y):
        # type: (str, Any, Any)->Tuple[Any, Any, Callable[[float], float], Callable[[float], float]]
        """Wrap x- and y-data to fit and return wrapped data with inverters.

        `axes_type` is the name of wrapper, and the grid data `x` and `y` are
        wrapped with it. The wrapped data of x, y, and the functions wx
        and wy to invert the wrap is returned, i.e., with fit function f,
        y_fit = wy(f(wx(x_fit))).
        """
        if axes_type == 'linear':
            return x, y, lambda a: a, lambda a: a
        elif axes_type == 'log':
            return x, numpy.log10(y), lambda a: a, lambda a: 10**a
        elif axes_type == 'loglinear':
            return numpy.log10(x), y, lambda a: float(numpy.log10(a)), lambda a: a
        elif axes_type == 'loglog':
            return numpy.log10(x), numpy.log10(y), lambda a: float(numpy.log10(a)), lambda a: 10**a
        else:
            raise ValueError('Invalid axes_type: %s', axes_type)

    def interpolate(self, df_with_unc):
        # type: (Any)->InterpolationWithUncertainties
        """Interpolate the values accompanied by uncertainties."""
        return InterpolationWithUncertainties(
            self._interpolate(df_with_unc['value']),
            self._interpolate(df_with_unc['value'] + df_with_unc['unc+']),
            self._interpolate(df_with_unc['value'] - abs(df_with_unc['unc-'])),
        )

    def _interpolate(self, df):
        # type: (Any)->Interpolation
        return NotImplemented  # type: ignore


class Scipy1dInterpolator(AbstractInterpolator):
    """Interpolator for values with uncertainty based on Scipy interp1d."""

    def __init__(self, kind=None, axes=None):
        # type: (str, str)->None
        self.kind = (kind or 'linear').lower()
        self.axes = (axes or 'linear').lower()

    def _interpolate(self, df):
        # type: (Any)->Interpolation
        if self.dim_index(df) != 1:
            raise Exception('Scipy1dInterpolator not handle multiindex data.')
        x0 = df.index.to_numpy()
        y0 = df.to_numpy()
        x, y, wx, wy = self.axes_wrapper(self.axes, x0, y0)
        return Interpolation(scipy.interpolate.interp1d(x, y, self.kind), wx, wy)
