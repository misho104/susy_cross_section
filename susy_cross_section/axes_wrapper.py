"""Functions for axes modifications before/after fitting.

Each type of modifiers are provided as two functions: parameters-version
and value-version, or one for 'x' and the other for 'y'. The former
always returns a tuple of floats because there might be multiple
parameters, while the latter returns single float value.
"""

import sys
from typing import Callable, Sequence, TypeVar, Union, cast  # noqa: F401

import numpy

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

VT = float
FT = Callable[[VT], VT]   # note: X-wrappers are not List[Value]->List[Value] but List[Value->Value].
XT = Sequence[VT]
YT = VT
XSeqT = Sequence[XT]
YSeqT = Sequence[YT]
T = TypeVar('T')


class AxesWrapper:
    """Toolkit to modify the x- and y-axes before interpolation."""

    @staticmethod
    def identity(x):
        # type: (VT)->VT
        """Identity function."""
        return x

    @staticmethod
    def log(x):
        # type: (VT)->VT
        """Log function."""
        return cast(VT, numpy.log10(x))

    @staticmethod
    def exp(x):
        # type: (VT)->VT
        """Exp function."""
        return 10**x

    @classmethod
    def get_function(cls, name=''):
        # type: (Union[FT, str])->FT
        """Return wrapper functions from its name.

        If "" is given as `name`, returns Identity function.
        """
        if isinstance(name, str):
            return cast(FT, numpy.vectorize(getattr(cls, name or 'identity')))
        else:
            return cast(FT, numpy.vectorize(name))

    def __init__(self, wx, wy, wy_inv):
        # type: (Sequence[Union[FT, str]], Union[FT, str], Union[FT, str])->None
        self.wx = [self.get_function(i) for i in wx]   # Type: List[FT]
        self.wy = self.get_function(wy)                # type: FT
        self.wy_inv = self.get_function(wy_inv)        # type: FT

    def wx_point(self, x):
        # type: (T)->T
        """Apply the x wrappers to the points.

        For one-dimensional case, the functions should be applied also
        to a float.
        """
        if len(self.wx) == 1:
            return self.wx[0](x)  # type: ignore
        else:
            return numpy.apply_along_axis(lambda x: [fi(i) for fi, i in zip(self.wx, x)], -1, x)  # type: ignore

    def correct(self, f):
        # type: (Callable[[VT], YT])->Callable[[VT], YT]
        """Correct the fit result to follow the axis modification."""
        return lambda x: self.wy_inv(f(self.wx_point(x)))


# names according to Mathematica "plot" functions
one_dim_wrapper = {
    'linear': AxesWrapper([AxesWrapper.identity], AxesWrapper.identity, AxesWrapper.identity),
    'log': AxesWrapper([AxesWrapper.identity], AxesWrapper.log, AxesWrapper.exp),
    'loglinear': AxesWrapper([AxesWrapper.log], AxesWrapper.identity, AxesWrapper.identity),
    'loglog': AxesWrapper([AxesWrapper.log], AxesWrapper.log, AxesWrapper.exp),
}
