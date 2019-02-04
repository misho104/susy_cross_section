"""Interpolators of cross-section data."""

from __future__ import absolute_import, division, print_function  # py2

import logging
import sys
from typing import (Any, Callable, List, Mapping, Sequence,  # noqa: F401
                    Tuple, Union, cast)

import numpy
import pandas  # noqa: F401
import scipy.interpolate

from susy_cross_section.axes_wrapper import AxesWrapper
from susy_cross_section.cross_section_table import CrossSectionTable

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

InterpolationType = Callable[[Sequence[float]], float]


class InterpolationWithUncertainties:
    """An interpolation result of values accompanied by uncertainties."""

    def __init__(self, central, central_plus_unc, central_minus_unc, param_names=None):
        # type: (InterpolationType, InterpolationType, InterpolationType, List[str])->None
        self._f0 = central
        self._fp = central_plus_unc
        self._fm = central_minus_unc
        self.param_index = {name: i for i, name in enumerate(param_names or [])}  # type: Mapping[str, int]

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

    def _interpret_args(self, *args, **kwargs):
        # type: (float, float)->Sequence[float]
        if not kwargs:
            return args
        tmp = list(args)   # type: List[Union[float, None]]
        for key, value in kwargs.items():
            index = self.param_index[key]
            if index >= len(tmp):
                tmp.extend([None for i in range(index + 1 - len(tmp))])
            tmp[index] = value
        if any(v is None for v in tmp):
            raise ValueError('insufficient arguments: %s, %s.', args, kwargs)
        return cast(Sequence[float], tmp)

    def f0(self, *a, **kw):
        # type: (float, float)->float
        """Return the fitted value of central value."""
        return self._f0(self._interpret_args(*a, **kw))

    def fp(self, *a, **kw):
        # type: (float, float)->float
        """Return the fitted value of central value."""
        return self._fp(self._interpret_args(*a, **kw))

    def fm(self, *a, **kw):
        # type: (float, float)->float
        """Return the fitted value of central value."""
        return self._fm(self._interpret_args(*a, **kw))

    def tuple_at(self, *a, **kw):
        # type: (float, float)->Tuple[float, float, float]
        """Return the tuple (central, +unc, -unc) at the fit point."""
        args = self._interpret_args(*a, **kw)
        return self.f0(*args), self.unc_p_at(*args), self.unc_m_at(*args)

    def unc_p_at(self, *a, **kw):
        # type: (float, float)->float
        """Return the fitted value of positive uncertainty."""
        args = self._interpret_args(*a, **kw)
        return self.fp(*args) - self.f0(*args)

    def unc_m_at(self, *a, **kw):
        # type: (float, float)->float
        """Return the fitted (negative) value of negative uncertainty."""
        args = self._interpret_args(*a, **kw)
        return -(self.f0(*args) - self.fm(*args))


class AbstractInterpolator:
    """Abstract class for interpolators of values with 1sigma uncertainties.

    Actual interpolators, inheriting this abstract class, will perform
    interpolation of pandas data frame.
    """

    def interpolate(self, xs_table, name='xsec'):
        # type: (CrossSectionTable, str)->InterpolationWithUncertainties
        """Interpolate the values accompanied by uncertainties."""
        df = xs_table.data[name]
        return InterpolationWithUncertainties(
            self._interpolate(df['value']),
            self._interpolate(df['value'] + df['unc+']),
            self._interpolate(df['value'] - abs(df['unc-'])),
            param_names=df.index.names)

    def _interpolate(self, df):
        # type: (pandas.DataFrame)->InterpolationType
        raise NotImplementedError


class Scipy1dInterpolator(AbstractInterpolator):
    """Interpolator for values with uncertainty based on Scipy interp1d."""

    def __init__(self, kind=None, axes=None):
        # type: (str, str)->None
        self.kind = (kind or 'linear').lower()  # type: str
        self.wrapper = {
            'linear': AxesWrapper(['linear'], 'linear', 'linear'),
            'log': AxesWrapper(['linear'], 'log', 'exp'),
            'loglinear': AxesWrapper(['log'], 'linear', 'linear'),
            'loglog': AxesWrapper(['log'], 'log', 'exp'),
        }[axes or 'linear']  # type: AxesWrapper

    def _interpolate(self, df):
        # type: (pandas.DataFrame)->InterpolationType
        if self.kind not in ['linear', 'cubic']:
            logging.info('Non-standard interpolation method is specified.')
        if df.index.nlevels != 1:
            raise ValueError('Scipy1dInterpolator not handle multiindex data.')

        x_list = [self.wrapper.wx[0](x) for x in df.index.to_numpy()]   # array(n_points)
        y_list = [self.wrapper.wy(y) for y in df.to_numpy()]            # array(n_points)

        if self.kind == 'cubic':
            # we should specify the "natural" boundary condition for cross-section fitting.
            fit = scipy.interpolate.CubicSpline(x_list, y_list, bc_type='natural', extrapolate=False)
        else:
            fit = scipy.interpolate.interp1d(x_list, y_list, self.kind)

        # now `fit` is float->float; we should convert it to Tuple[float]->float.

        def _fit(x, f=fit):  # noqa: B008
            # type: (Sequence[float], Callable[[float], float])->float
            return f(*x)

        return self.wrapper.correct(_fit)


class ScipyRegularGridInterpolator(AbstractInterpolator):
    """Interpolator based on Scipy RegularGridInterpolator."""

    def __init__(self, param_axes, value_axis):
        # type: (Sequence[str], str)->None
        self.wrapper = AxesWrapper(param_axes, value_axis)

    def _interpolate(self, df):
        # type: (pandas.DataFrame)->InterpolationType
        np = df.index.nlevels
        if len(self.wrapper.wx) != np:
            raise ValueError('Interpolator accepts %d-parameters but %d-parameter data is given.',
                             len(self.wrapper.wx), np)
        x0 = df.index.levels   # arrays of grid "ticks"
        x = [w(axis) for w, axis in zip(self.wrapper.wx, x0)]
        y = df.apply(self.wrapper.wy).unstack().values
        # as RegularGridInterpolator `fit` works as:
        #     fit([700, 700])  ->  [0.7],   we have to correct the returning value.

        def fit(x, fit=scipy.interpolate.RegularGridInterpolator(x, y)):  # noqa: B008
            # type: (Sequence[float], Any)->float
            return cast(float, fit(x)[0])

        return self.wrapper.correct(fit)
