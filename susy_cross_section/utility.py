"""Utility functions and classes."""

from __future__ import absolute_import, division, print_function  # py2

import sys
from typing import List, Mapping, MutableMapping, Optional, Union  # noqa: F401

import numpy

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821


class Unit:
    """The unit of a physical value.

    The constructor must be called with units, where units must be str.
    """

    definitions = {
        '': [1],
        '%': [0.01],
        'pb': [1000, 'fb'],
    }  # type: Mapping[Union[float, str], List[Union[float, str]]]

    def __init__(self, *args):
        # type: (Union[float, str, Unit])->None
        self.factor = 1   # type: float
        self.units = {}   # type: MutableMapping[str, int]
        for u in args:
            if isinstance(u, Unit):
                self.factor *= u.factor
                for k, v in u.units.items():
                    self.units[k] = self.units.get(k, 0) + v
            else:
                base_units = self.definitions.get(u, [u])
                for b in base_units:
                    if isinstance(b, str):
                        self.units[b] = self.units.get(b, 0) + 1
                    else:
                        try:
                            self.factor *= float(b)
                        except ValueError:
                            raise TypeError('invalid unit: %s', u)

    def invert(self):
        # type: ()->Unit
        """Return an inverted unit."""
        result = Unit()
        result.factor = 1 / self.factor
        result.units = {k: -v for k, v in self.units.items()}
        return result

    def __mul__(self, other):
        # type: (Union[float, str, Unit])->Unit
        """Return products of two units."""
        return Unit(self, other)

    def __truediv__(self, other):
        # type: (Union[float, str, Unit])->Unit
        """Return division of two units."""
        return self * Unit(other).invert()

    def __float__(self):
        # type: ()->float
        """Return factor if it is without units."""
        if any(v != 0 for v in self.units.values()):
            raise ValueError('Unit conversion error: %s, %s', self.units, self.factor)
        return float(self.factor)


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
