"""Functions for axes modifications before/after fitting.

Each type of modifiers are provided as two functions: parameters-version
and value-version, or one for 'x' and the other for 'y'. The former
always returns a tuple of floats because there might be multiple
parameters, while the latter returns single float value.
"""

import sys
from typing import Any, Callable, Mapping, Sequence, Union, cast  # noqa: F401

import numpy

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

VT = float
FT = Callable[[VT], VT]   # note: X-wrappers are not List[Value]->List[Value] but List[Value->Value].
XT = Sequence[VT]         # X-point is always a sequence, even if one-parameter.
YT = VT


def _check_seq_length(obj, n):
    # type: (Any, int)->bool
    return hasattr(obj, '__len__') and len(obj) == n and (
        obj[0].ndim == 0 if isinstance(obj[0], numpy.ndarray) else not hasattr(obj[0], '__len__')
    )


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

    function_aliases = {
        'id': 'identity',
        'linear': 'identity',
    }  # type: Mapping[str, str]

    function_inverses = {
        'identity': 'identity',
        'log': 'exp',
        'exp': 'log',
    }  # type: Mapping[str, str]

    @classmethod
    def get_function(cls, name=''):
        # type: (Union[FT, str])->FT
        """Return wrapper functions from its name.

        If "" is given as `name`, returns Identity function.
        """
        if isinstance(name, str):
            # meaningless cast because of mypy false-positive
            name = cast(str, cls.function_aliases.get(name, name) or 'identity')
            return cast(FT, numpy.vectorize(getattr(cls, name)))
        else:
            return cast(FT, numpy.vectorize(name))

    @classmethod
    def get_inverse_function(cls, name=''):
        # type: (str)->FT
        """Return the name of function to invert the wrapper."""
        name = cls.function_aliases.get(name, name) or 'identity'
        return cls.get_function(cls.function_inverses[name])

    def __init__(self, wx, wy, wy_inv=None):
        # type: (Sequence[Union[FT, str]], Union[FT, str], Union[FT, str])->None
        self.wx = [self.get_function(i) for i in wx]   # Type: List[FT]
        self.wy = self.get_function(wy)                # type: FT
        if wy_inv:
            self.wy_inv = self.get_function(wy_inv)        # type: FT
        else:
            # guess wy_inv
            if not isinstance(wy, str):
                raise TypeError('y-wrapper guess only available if specified in name.')
            self.wy_inv = self.get_inverse_function(wy)

    def wx_point(self, x_list):
        # type: (XT)->XT
        """Apply the x wrappers to the points."""
        return [w(x) for w, x in zip(self.wx, x_list)]

    def correct(self, f):
        # type: (Callable[[XT], YT])->Callable[[XT], YT]
        """Correct the fit result to follow the axis modification."""
        def _corrected_fit(x, _f=f):
            # type: (XT, Callable[[XT], YT])->YT
            if not _check_seq_length(x, len(self.wx)):
                raise TypeError('Invalid arguments for %d-dim fit: %s', len(self.wx), x)
            return self.wy_inv(f(self.wx_point(x)))

        return _corrected_fit
