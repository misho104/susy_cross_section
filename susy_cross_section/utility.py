"""Utility functions and classes."""

from __future__ import absolute_import, division, print_function  # py2

import sys
from typing import List, Mapping, MutableMapping, Optional, Union  # noqa: F401

import numpy

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821


class Unit:
    """A class to handle units of physical values.

    This class handles units associated to physical values. Units can be
    multiplied, inverted, or converted. A new instance is equivalent to the
    product of `!*args`; each argument can be a str, a Unit, or a float (as a
    numerical factor).

    Parameters
    ----------
    *args: float, str, or Unit
        Factors of the new instance.
    """

    definitions = {
        '': [1],
        '%': [0.01],
        'pb': [1000, 'fb'],
    }  # type: Mapping[str, List[Union[float, str]]]
    """:typ:`dict[str, list of (float or str)]`: The replacement rules of units.

    This dictionary defines the replacement rules for unit conversion.
    Each key should be replaced with the product of its values."""

    def __init__(self, *args):
        # type: (Union[float, str, Unit])->None
        self._factor = 1   # type: float
        self._units = {}   # type: MutableMapping[str, int]
        for u in args:
            self.__imul__(u)

    def inverse(self):
        # type: ()->Unit
        """Return an inverted unit.

        Returns
        -------
        Unit
            The inverted unit of `!self`.
        """
        result = Unit()
        result._factor = 1 / self._factor
        result._units = {k: -v for k, v in self._units.items()}
        return result

    def __imul__(self, other):
        # type: (Union[float, str, Unit])->None
        """Multiply by another unit.

        Parameters
        ----------
        other: float, str, or Unit
            Another unit as a multiplier.
        """
        if isinstance(other, Unit):
            self._factor *= other._factor
            for k, v in other._units.items():
                self._units[k] = self._units.get(k, 0) + v
        else:
            if isinstance(other, str):
                base_units = self.definitions.get(other, [other])
            else:
                base_units = [other]
            for b in base_units:
                if isinstance(b, str):
                    self._units[b] = self._units.get(b, 0) + 1
                else:
                    try:
                        self._factor *= float(b)
                    except ValueError:
                        raise TypeError('invalid unit: %s', other)

    def __mul__(self, other):
        # type: (Union[float, str, Unit])->Unit
        """Return products of two units.

        Parameters
        ----------
        other: float, str, or Unit
            Another unit as a multiplier.

        Returns
        -------
        Unit
            The product.
        """
        return Unit(self, other)

    def __truediv__(self, other):
        # type: (Union[float, str, Unit])->Unit
        """Return division of two units.

        Parameters
        ----------
        other: float, str, or Unit
            Another unit as a divider.

        Returns
        -------
        Unit
            The quotient.
        """
        return Unit(self, Unit(other).inverse())

    def __float__(self):
        # type: ()->float
        """Evaluate as a float value if this is a dimension-less unit.

        Returns
        -------
        float
            The number corresponding to this dimension-less unit.

        Raises
        ------
        ValueError
            If not dimension-less unit.
        """
        if any(v != 0 for v in self._units.values()):
            raise ValueError('Unit conversion error: %s, %s', self._units, self._factor)
        return float(self._factor)


def value_format(value, unc_p, unc_m, unit=None):
    # type: (float, float, float, Optional[str])->str
    """Format the value with uncertainty (and with unit)."""
    delta = min(abs(unc_p), abs(unc_m))
    if delta == 0:
        value_str = '{:g} +0 -0'.format(value)
        return '({}) {}'.format(value_str, unit) if unit else value_str
    else:
        v_order = int(numpy.log10(value))
        if abs(v_order) > 3:
            digits = max(int(-numpy.log10(delta / value) - 0.005) + 2, 3)
            v, p, m = value / 10**v_order, unc_p / 10**v_order, abs(unc_m) / 10**v_order
            f = '{{:.{}f}}'.format(digits)
            value_str = '({} +{} -{})'.format(f, f, f).format(v, p, m) + '*1e{}'.format(v_order)
            return '{} {}'.format(value_str, unit) if unit else value_str
        else:
            digits = max(int(-numpy.log10(delta) - 0.005) + (1 if delta > 1 else 2), 0)
            f = '{{:{}}}'.format('.{}f'.format(digits))
            value_str = '{} +{} -{}'.format(f, f, f).format(value, unc_p, abs(unc_m))
            return '({}) {}'.format(value_str, unit) if unit else value_str
