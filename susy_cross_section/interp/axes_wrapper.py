r"""Axis preprocessor for table interpolation.

This module provides a class `AxesWrapper` for advanced interpolation. Each
type of modifiers are provided as two functions: parameters-version and value-
version, or one for 'x' and the other for 'y'. The former always returns a
tuple of floats because there might be multiple parameters, while the latter
returns single float value.

Note
----
Here we summarize interpolations with modified axes. In axis-modification
process, we modify the data points

.. math:: (x_{n1}, \dots, x_{nd}; y_n),

with :math:`d+1` functions :math:`w_1, \dots, w_d` and :math:`w_{\mathrm y}`
into

.. math:: X_{ni}=w_i(x_{ni}), \qquad Y_{n} = w_{\mathrm y}(y_n)

and derive the interpolation function :math:`\bar f` based on
:math:`({\boldsymbol X}_n; Y_n)`. Then, the interpolated result is given by

.. math::
    f({\boldsymbol x}) = w_{\mathrm y}^{-1}\Bigl(\bar f\bigl(w_1(x_1), \dots,
    w_d(x_d)\bigr)\Bigr).



:Type Aliases:

    .. py:data:: VT
        :annotation: (= float)

        Type representing elements of data points.

    .. py:data:: FT
        :annotation: (= Callable[[VT], VT])

        Type for wrapper functions :m:`w`.

    .. py:data:: XT
        :annotation: (= List[VT])

        Type for parameters :m:`x`.

    .. py:data:: YT
        :annotation: (= VT)

        Type for the value :m:`y`.

.. role:: data_typ(typ)
   :reftype: data
.. |VT| replace:: :data_typ:`VT`
.. |FT| replace:: :data_typ:`FT`
.. |XT| replace:: :data_typ:`XT`
.. |YT| replace:: :data_typ:`YT`
"""

import sys
from typing import Any, Callable, Mapping, Sequence, Union, cast  # noqa: F401

import numpy

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821

VT = float
FT = Callable[[VT], VT]
XT = Sequence[VT]  # X-point is always a sequence, even if one-parameter.
YT = VT


def _is_number(obj):
    # type: (Any)->bool
    """Return whether obj is a number (int, float, dim-0 numpy array)."""
    if isinstance(obj, numpy.ndarray):
        return bool(obj.ndim == 0 and obj.dtype.kind in "fiub")
    else:
        return isinstance(obj, float) or isinstance(obj, int)


def _is_number_sequence(obj, length):
    # type: (Any, int)->bool
    """Return whether obj is a sequence of numbers with specified length."""
    if isinstance(obj, numpy.ndarray):
        return obj.shape == (length,) and obj.dtype.kind in "fiub"
    try:
        return len(obj) == length and all(_is_number(i) for i in obj)
    except TypeError:
        return False


class AxesWrapper:
    """Toolkit to modify the x- and y- axes before interpolation.

    In initialization, one can specify wrapper functions predefined, where one
    can omit :ar:`wy_inv` argument. The following functions are predefined.

        - "identity" (or "id", "linear")
        - "log10"    (or "log")
        - "exp10"    (or "exp")

    Attributes
    ----------
    wx: *list of* |FT|
        Wrapper functions (or names) for parameters x.
    wy: |FT|
        Wrapper function for the value y.
    wy_inv: |FT|
        The inverse function of :attr:`wy`.
    """

    @staticmethod
    def identity(x):
        # type: (VT)->VT
        """Identity function as a wrapper."""
        return x

    @staticmethod
    def log10(x):
        # type: (VT)->VT
        """Log function (base 10) as a wrapper.

        Note that this is equivalent to natural-log function as a wrapper.
        """
        return cast(VT, numpy.log10(x))

    @staticmethod
    def exp10(x):
        # type: (VT)->VT
        """Exp function (base 10) as a wrapper.

        Note that this is equivalent to natural-exp function as a wrapper.
        """
        return 10 ** x

    # we use base 10 because they are equivalent and easier to debug.
    # keys include aliases, and values are the name of staticmethods.
    _predefined_function_names = {
        "identity": "identity",
        "id": "identity",
        "linear": "identity",
        "log": "log10",
        "log10": "log10",
        "exp": "exp10",
        "exp10": "exp10",
    }  # type: Mapping[str, str]

    _inverse_function_names = {
        "identity": "identity",
        "log10": "exp10",
        "exp10": "log10",
    }  # type: Mapping[str, str]

    @classmethod
    def _get_function(cls, obj):
        # type: (Union[FT, str])->FT
        """Return wrapper function.

        The argument can be a function itself or a function name. The returned
        functions are dressed by `numpy.vectorize` so that it can be applied to
        numpy objects.
        """
        if isinstance(obj, str):
            name = cls._predefined_function_names.get(obj)
            if not name:
                raise KeyError("Function %s is not predefined in AxesWrapper", obj)
            return cast(FT, numpy.vectorize(getattr(cls, name)))
        else:
            return cast(FT, numpy.vectorize(obj))

    @classmethod
    def _get_inverse_function(cls, name):
        # type: (str)->FT
        """Return the inverse function with numpy-dress."""
        name = cls._inverse_function_names[cls._predefined_function_names[name]]
        return cast(FT, numpy.vectorize(getattr(cls, name)))

    def __init__(self, wx, wy, wy_inv=None):
        # type: (Sequence[Union[FT, str]], Union[FT, str], Union[FT, str])->None
        self.wx = [self._get_function(i) for i in wx]  # Type: List[FT]
        self.wy = self._get_function(wy)  # type: FT
        if wy_inv:
            self.wy_inv = self._get_function(wy_inv)  # type: FT
        elif isinstance(wy, str):
            self.wy_inv = self._get_inverse_function(wy)  # guess wy_inv
        else:
            raise TypeError("wy_inv must be specified.")

    def wrapped_x(self, xs):
        # type: (XT)->XT
        r"""Return the parameter values after axes modification.

        Arguments
        ---------
        xs: |XT|
            Parameters in the original axes

        Returns
        -------
        XT
            Parameters in the wrapped axes.

        Note
        ----
        The argument :ar:`xs` is :math:`(x_1, x_2, \dots, x_d)`, while the
        returned value is
        :math:`(X_1, \dots, X_d) = (w_1(x_1), \dots, w_d(x_d))`.
        """
        return [w(x) for w, x in zip(self.wx, xs)]

    def wrapped_f(self, f_bar, type_check=True):
        # type: (Callable[[XT], YT], bool)->Callable[[XT], YT]
        r"""Return interpolating function for original data.

        Return the interpolating function applicable to the original data set,
        given the interpolating function in the modified axes.

        Arguments
        ---------
        f_bar: function of |XT| to |YT|
            The interpolating function in the modified axes.
        type_check: bool
            To perform type-check or not.

        Returns
        -------
        function of XT to YT
            The interpolating function in the original axes.


        Note
        ----
        The argument :ar:`f_bar` is :math:`\bar f`, which is the interpolation
        function for :math:`({\boldsymbol X}_n; Y_n)`, and this method returns
        the function :math:`f`, which is

        .. math::
            f({\boldsymbol x})
            = w_{\mathrm y}^{-1}\bigl(\bar f({\boldsymbol X})\bigr),

        where :math:`\boldsymbol X` is given by applying :meth:`wrapped_x` to
        :math:`\boldsymbol x`.
        """
        x_len = len(self.wx) if type_check else None

        def _f(x, _f_bar=f_bar, _len=x_len):
            # type: (XT, Callable[[XT], YT], Union[int, None])->YT
            if _len is not None and not _is_number_sequence(x, _len):
                raise TypeError("Invalid arguments for %d-dim fit: %s", _len, x)
            return self.wy_inv(_f_bar(self.wrapped_x(x)))

        return _f
