r"""Interpolators of cross-section data.

:Type Aliases:

    .. py:data:: InterpType
        :annotation: (= Callable[[Sequence[float]], float])

        Type representing an interpolation function.

.. role:: data_typ(typ)
   :reftype: data

.. |InterpType| replace:: :data_typ:`InterpType`
"""

from __future__ import absolute_import, division, print_function  # py2

import logging
import re
import sys
from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple, Union, cast

import numpy
import pandas  # noqa: F401
import scipy.interpolate as sci_interp

from susy_cross_section.table import BaseTable

from .axes_wrapper import AxesWrapper

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

InterpType = Callable[[Sequence[float]], float]


class Interpolation:
    """An interpolation result for values with uncertainties.

    This class handles an interpolation of data points, where each data point
    is given with uncertainties, but does not handle uncertainties due to
    interpolation.

    In initialization, the interpolation results :ar:`f0`, :ar:`fp`, and
    :ar:`fm` should be specified as functions accepting a list of float, i.e.,
    ``f0([x1, ..., xd])`` etc. If the argument :ar:`param_names` is also
    specified, the attribute :attr:`param_index` is set, which allows users to
    call the interpolating functions with keyword arguments.

    Arguments
    ---------
    f0: |InterpType|
        Interpolating function of the central values.
    fp: |InterpType|
        Interpolating function of values with positive uncertainty added.
    fm: |InterpType|
        Interpolating function of values with negative uncertainty subtracted.
    param_names: list[str], optional
        Names of parameters.

    Attributes
    ----------
    param_index: dict(str, int)
        Dictionary to look up parameter's position from a parameter name.
    """

    def __init__(self, f0, fp, fm, param_names=None):
        # type: (InterpType, InterpType, InterpType, List[str])->None
        self._f0 = f0
        self._fp = fp
        self._fm = fm
        self.param_index = {
            name: index for index, name in enumerate(param_names or [])
        }  # type: Mapping[str, int]

    def _interpret_args(self, *args, **kwargs):
        # type: (Union[Sequence[float], float], float)->Sequence[float]
        """Interpret the argument and return a list-like of float.

        Note that strict type-check is not performed.
        """
        if len(args) == 1:  # single list, dim-1 array, or only one argument
            if isinstance(args[0], numpy.ndarray) and args[0].ndim == 1:
                xs = cast(List[float], args[0])
            elif isinstance(args[0], numpy.ndarray) and args[0].ndim == 0:
                xs = cast(List[float], [args[0]])
            elif hasattr(args[0], "__iter__"):
                xs = cast(List[float], args[0])
            else:
                xs = cast(List[float], args)
        else:
            xs = cast(List[float], args)

        if not kwargs:
            return xs

        # parse kwargs; before parsing, convert (possibly) ndarray to list.
        x_list = [x for x in xs]  # type: List[Union[float, None]]
        for key, value in kwargs.items():
            try:
                index = self.param_index[key]
                x_list += [None for _ in range(len(x_list), index + 1)]
                x_list[index] = value
            except KeyError:
                raise TypeError("Unexpected param name: %s", key)
        if any(v is None for v in x_list):
            raise TypeError("Arguments insufficient: %s, %s", args, kwargs)
        return cast(List[float], x_list)

    def f0(self, *args, **kwargs):
        # type: (float, float)->float
        r"""Return the interpolation result of central value.

        The parameters can be specified as arguments, a sequence, or as keyword
        arguments if :attr:`param_index` is set.

        Returns
        -------
        float
            interpolated central value.

        Examples
        --------
        For an interpolation with names "foo", "bar", and "baz", the following
        calls are equivalent:

        - ``f0([100, 20, -1])``
        - ``f0(100, 20, -1)``
        - ``f0(numpy.array([100, 20, -1]))``
        - ``f0(100, 20, baz=-1)``
        - ``f0(foo=100, bar=20, baz=-1)``
        - ``f0(0, 0, -1, bar=20, foo=100)``
        """
        return self._f0(self._interpret_args(*args, **kwargs))

    __call__ = f0
    """Function call is alias of :meth:`f0`."""

    def fp(self, *args, **kwargs):
        # type: (Union[Sequence[float], float], float)->float
        """Return the interpolation result of upper-fluctuated value.

        Returns
        -------
        float
            interpolated result of central value plus positive uncertainty.
        """
        return self._fp(self._interpret_args(*args, **kwargs))

    def fm(self, *args, **kwargs):
        # type: (Union[Sequence[float], float], float)->float
        """Return the interpolation result of downer-fluctuated value.

        Returns
        -------
        float
            interpolated result of central value minus negative uncertainty.
        """
        return self._fm(self._interpret_args(*args, **kwargs))

    def tuple_at(self, *args, **kwargs):
        # type: (Union[Sequence[float], float], float)->Tuple[float, float, float]
        """Return the tuple(central, +unc, -unc) at the point.

        Returns
        -------
        tuple(float, float, float)
            interpolated central value and positive and negative uncertainties.
        """
        x = self._interpret_args(*args, **kwargs)
        return self._f0(x), self.unc_p_at(*x), self.unc_m_at(*x)

    def unc_p_at(self, *args, **kwargs):
        # type: (Union[Sequence[float], float], float)->float
        """Return the interpolated value of positive uncertainty.

        This is calculated not by interpolating the positive uncertainty table
        but as a difference of the interpolation result of the central and
        upper - fluctuated values.

        Returns
        -------
        float
            interpolated result of positive uncertainty.

        Warning
        -------
        This is not the positive uncertainty of the interpolation because
        the interpolating uncertainty is not included. The same warning applies
        for: meth: `unc_m_at`.
        """
        x = self._interpret_args(*args, **kwargs)
        return self._fp(x) - self._f0(x)

    def unc_m_at(self, *args, **kwargs):
        # type: (float, float)->float
        """Return the interpolated value of negative uncertainty.

        Returns
        -------
        float
            interpolated result of negative uncertainty.
        """
        x = self._interpret_args(*args, **kwargs)
        return -(self._f0(x) - self._fm(x))


class AbstractInterpolator:
    """A base class of interpolator for values with uncertainties.

    Actual interpolator should implement :meth:`_interpolate` method, which
    accepts a `pandas.DataFrame` object with one value-column and returns an
    interpolating function (|InterpType|).
    """

    def interpolate(self, table):
        # type: (BaseTable)->Interpolation
        """Perform interpolation for values with uncertainties.

        Arguments
        ---------
        cross_section_table: File
            A cross-section data table.
        name: str
            Value name of the table to interpolate.

        Returns
        -------
        Interpolation
            The interpolation result.
        """
        return Interpolation(
            self._interpolate(table["value"]),
            self._interpolate(table["value"] + table["unc+"]),
            self._interpolate(table["value"] - abs(table["unc-"])),
            param_names=table.index.names,
        )

    def _interpolate(self, df):
        # type: (pandas.DataFrame)->InterpType
        raise NotImplementedError


class Scipy1dInterpolator(AbstractInterpolator):
    r"""Interpolator for one-dimensional data based on scipy interpolators.

    Arguments
    ---------
    kind: str
        Specifies the interpolator types.

        :linear:
            uses `scipy.interpolate.interp1d` (`!kind="linear"`), which
            performs piece-wise linear interpolation.
        :spline:
            uses `scipy.interpolate.CubicSpline`, which performs cubic-spline
            interpolation. The natural boundary condition is imposed. This is
            simple and works well if the grid is even-spaced, but is unstable
            and not recommended if not even-spaced.
        :pchip:
            uses `scipy.interpolate.PchipInterpolator`. This method is
            recommended for most cases, especially if monotonic, but not
            suitable for oscillatory data.
        :akima:
            uses `scipy.interpolate.Akima1DInterpolator`. For oscillatory data
            this is preferred to Pchip interpolation.

    axes: str
        Specifies the axes preprocess types.

        :linear:
            does no preprocess.
        :log:
            uses log-axis for values (y).
        :loglinear:
            uses log-axis for parameters (x).
        :loglog:
            uses log-axis for parameters and values.

    Warnings
    --------
    Users should notice the cons of each interpolator, e.g., "spline" and
    "akima" methods are worse for the first and last intervals or if the grid
    is not even-spaced, or "pchip" cannot capture oscillations.

    Note
    ----
    :attr:`kind` also accepts all the options for `scipy.interpolate.interp1d`,
    but they except for "cubic" are not recommended for cross-section data.
    The option "cubic" calls `scipy.interpolate.interp1d`, but it uses the
    not-a-knot boundary condition, while "spline" uses the natural condition,
    which imposes the second derivatives at the both ends to be zero.

    Note
    ----
    Polynomial interpolations (listed below) are not included because they are
    not suitable for cross-section data. They yield in globally-defined
    polynomials, but such uniformity is not necessary for our purpose and they
    suffer from so-called Runge phenomenon. If data is expected to be fit by a
    polynomial, one may use "linear" with `!axes="loglog"`.

    - `scipy.interpolate.BarycentricInterpolator`
    - `scipy.interpolate.KroghInterpolator`

    See Also
    --------
    * `MATLAB pchip - MathWorks`_
    * `Spline methods comparison`_

    .. _MATLAB pchip - MathWorks:
       https://mathworks.com/help/matlab/ref/pchip.html
    .. _Spline methods comparison:
       https://gist.github.com/misho104/46032fa730088a0cb4c2e0556c59260b
    """

    def __init__(self, kind="linear", axes="linear"):
        # type: (str, str)->None
        self.kind = kind.lower()  # type: str
        self.axes = axes.lower()  # type: str

    def _interpolate(self, df):
        # type: (pandas.DataFrame)->InterpType
        if self.axes == "linear":
            wrapper = AxesWrapper(["linear"], "linear")
        elif self.axes == "log":
            wrapper = AxesWrapper(["linear"], "log")
        elif self.axes == "loglinear":
            wrapper = AxesWrapper(["log"], "linear")
        elif self.axes == "loglog":
            wrapper = AxesWrapper(["log"], "log")
        else:
            raise ValueError("Invalid axes wrapper: %s", self.axes)

        if df.index.nlevels != 1:
            raise ValueError("Scipy1dInterpolator not handle multiindex data.")

        # axes modification; note that the wrappers are numpy.vectorize()-ed.
        xs = wrapper.wx[0](df.index.to_numpy())
        ys = wrapper.wy(df.to_numpy())

        if self.kind == "spline":
            f_bar = sci_interp.CubicSpline(xs, ys, bc_type="natural", extrapolate=False)
        elif self.kind == "pchip":
            f_bar = sci_interp.PchipInterpolator(xs, ys, extrapolate=False)
        elif self.kind == "akima":
            f_bar = sci_interp.Akima1DInterpolator(xs, ys)
            f_bar.extrapolate = False
        else:
            f_bar = sci_interp.interp1d(xs, ys, self.kind, bounds_error=True)

        # now `f_bar` is float->float; we should convert it to Tuple[float]->float.

        def _f_bar(x, f_bar=f_bar):  # noqa: B008
            # type: (Sequence[float], Callable[[float], float])->float
            return f_bar(*x)

        return wrapper.wrapped_f(_f_bar)


class ScipyGridInterpolator(AbstractInterpolator):
    r"""Interpolator for multi-dimensional structural data.

    Arguments
    ---------
    kind: str
        Specifies the interpolator types. Spline interpolators can be available
        only for two-parameter interpolations.

        :linear:
            uses `scipy.interpolate.RegularGridInterpolator` with
            method="linear", which linearly interpolates the grid mesh.
        :spline:
            alias of "spline33".
        :spline33:
            uses `scipy.interpolate.RectBivariateSpline` with order (3, 3); the
            numbers may be 1 to 5, but "spline11" is equivalent to "linear".

    axes_wrapper: AxesWrapper, optional
        Object for axes preprocess. If unspecified, no preprocess is performed.
    """

    def __init__(self, kind="linear", axes_wrapper=None):
        # type: (str, Optional[AxesWrapper])->None
        self.kind = kind.lower()  # type: str
        self.axes_wrapper = axes_wrapper  # type: Optional[AxesWrapper]

    def _interpolate(self, df):
        # type: (pandas.DataFrame)->InterpType
        try:
            xs = df.index.levels  # multiindex case
            ys = df.unstack().to_numpy()
        except AttributeError:
            xs = [df.index.values]
            ys = df.to_numpy()
        # xs: list with n_dim elements; each is a list of grid points along an axis.
        # ys: a numpy matrix with ndim = n_dim, i.e., "unstacked" tensor.

        # wrap
        if self.axes_wrapper:
            if len(self.axes_wrapper.wx) != len(xs):
                raise ValueError(
                    "Axes wrapper for %d-dim is specified for %d-dim interp.",
                    len(self.axes_wrapper.wx),
                    len(xs),
                )
            xs = [w(axis) for w, axis in zip(self.axes_wrapper.wx, xs)]
            ys = self.axes_wrapper.wy(ys)

        # call scipy
        if self.kind == "linear":
            f_bar = self._interpolate_linear(xs, ys)
        elif self.kind == "spline":
            f_bar = self._interpolate_spline(xs, ys, 3, 3)
        elif re.match(r"\Aspline[1-5][1-5]\Z", self.kind):
            kx, ky = int(self.kind[-2]), int(self.kind[-1])
            f_bar = self._interpolate_spline(xs, ys, kx, ky)
        else:
            raise ValueError("Invalid kind: %s", self.kind)

        if self.axes_wrapper:
            return self.axes_wrapper.wrapped_f(f_bar)
        else:
            return f_bar

    def _interpolate_linear(self, xs, ys):
        # type: (Any, Any)->Callable[[Sequence[float]], float]
        interp = sci_interp.RegularGridInterpolator(xs, ys, method="linear")
        interp.bounds_error = True

        def f_bar(x, _f_bar=interp):
            # type: (Sequence[float], Any)->float
            return float(_f_bar(x))

        return f_bar

    def _interpolate_spline(self, xs, ys, kx, ky):
        # type: (Any, Any, int, int)->Callable[[Sequence[float]], float]
        if len(xs) != 2:
            raise ValueError("ScipyGridInterpolator with spline is only for 2d data.")

        if numpy.isnan(ys).any():
            raise ValueError("Spline interpolation does not allow missing grid points.")
        interp = sci_interp.RectBivariateSpline(xs[0], xs[1], ys, s=0, kx=kx, ky=ky)

        def f_bar(x, _f_bar=interp):
            # type: (Sequence[float], Any)->float
            return float(_f_bar(*x))

        return f_bar


# class ScipyMultiDimensionalInterpolator(AbstractInterpolator):
#    """Interpolator for multi - dimensional non - structural data.
#
#    Among the several implementations in scipy.interpolate for multi-
#    dimensional non - structural data, "linear" (LinearNDInterpolator) and
#    "spline" (LSQBivariateSpline) are sensible for cross - section fitting.
#    """
