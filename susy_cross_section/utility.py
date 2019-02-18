"""Utility functions and classes.

============== ========================================================
`Unit`         describing a physical unit.
`value_format` give human-friendly string representation of values.
`get_paths`    parse and give paths to data and info files
============== ========================================================
"""

from __future__ import absolute_import, division, print_function  # py2

import itertools
import logging
import pathlib
import sys
from typing import List, Mapping, MutableMapping, Optional, Tuple, Union  # noqa: F401

from numpy import log10

import susy_cross_section.config

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821
    FileNotFoundError = OSError  # noqa: A001, F821


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

PathLike = Union[str, pathlib.Path]


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
        "": [1],
        "%": [0.01],
        "pb": [1000, "fb"],
    }  # type: Mapping[str, List[Union[float, str]]]
    """:typ:`dict[str, list of (float or str)]`: The replacement rules of units.

    This dictionary defines the replacement rules for unit conversion.
    Each key should be replaced with the product of its values."""

    @classmethod
    def _get_base_units(cls, name):
        # type: (Union[float, str])->List[Union[float, str]]
        """Expand the unit name to the base units.

        Parameters
        ----------
        name: float or str
            The unit name to be expanded, or possibly a numerical factor.

        Returns
        -------
        list[float or str]
            Expansion result as a list of factors and base unit names.
        """
        if isinstance(name, str) and name in cls.definitions:
            nested = [cls._get_base_units(u) for u in cls.definitions[name]]
            return list(itertools.chain.from_iterable(nested))  # flatten
        else:
            return [name]

    def __init__(self, *args):
        # type: (Union[float, str, Unit])->None
        self._factor = 1  # type: float
        self._units = {}  # type: MutableMapping[str, int]
        for u in args:
            self *= u

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
        # type: (Union[float, str, Unit])->Unit
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
            for b in self._get_base_units(other):
                if isinstance(b, str):
                    self._units[b] = self._units.get(b, 0) + 1
                else:
                    try:
                        self._factor *= float(b)
                    except ValueError:
                        raise TypeError("invalid unit: %s", other)
        return self

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
            raise ValueError("Unit conversion error: %s, %s", self._units, self._factor)
        return float(self._factor)


def value_format(value, unc_p, unc_m, unit=None):
    # type: (float, float, float, Optional[str])->str
    """Return human-friendly text of an uncertainty-accompanied value.

    Parameters
    ----------
    value: float
        Central value.
    unc_p: float
        Positive-direction absolute uncertainty.
    unc_m: float
        Negative-direction absolute uncertainty.
    unit: str, optional
        Unit of the value and the uncertainties.

    Returns
    -------
    str
        Formatted string describing the given value.
    """
    delta = min(abs(unc_p), abs(unc_m))
    suffix = " {}".format(unit) if unit else ""  # will be appended to the body.

    if delta == 0:
        # without uncertainty
        body = "{:g} +0 -0".format(value)
    else:
        v_order = int(log10(value))
        if abs(v_order) > 3:
            # force to use scientific notation
            suffix = "*1e{:d}".format(v_order) + suffix
            divider = 10 ** v_order
            disp_digits = max(int(-log10(delta / value) - 0.005) + 2, 3)
        else:
            divider = 1
            disp_digits = max(int(-log10(delta) - 0.005) + (1 if delta > 1 else 2), 0)
        v_format = "{f} +{f} -{f}".format(f="{{:.{}f}}".format(disp_digits))
        body = v_format.format(value / divider, unc_p / divider, abs(unc_m / divider))
    return "({}){}".format(body, suffix) if suffix else body


def get_paths(data_name, info_path=None):
    # type: (PathLike, Optional[PathLike])->Tuple[PathLike, PathLike]
    """Return paths to data file and info file.

    Relative path is evaluted from the package directory (i.e., the directory
    having this file).

    Parameters
    ----------
    data_name: pathlib.Path or str
        Path to data file or a table name found in configuration.

        If the string is found in configuration's table_names, the configured
        paths are returned. Otherwise, :ar:`data_name` is interpreted as a path
        to the data file itself.
    info_path: pathlib.Path or str, optional
        Path to info file.

        If not given, the path to data file with suffix changed to ".info" is
        returned.

    Returns
    -------
    Tuple[pathlib.Path, pathlib.Path]
        A tuple with paths to data file and info file.

    Raises
    ------
    FileNotFoundError
        If one of the specified files are not found.
    RuntimeError
        If one of the specified files are not a file.
    """
    # Note to developers:
    # To reduce confusion, this method should be in the directory
    # where the default configuration file locates.
    info = pathlib.Path(info_path) if info_path else None
    if isinstance(data_name, pathlib.Path):
        data = data_name  # type: pathlib.Path
        error_hint = "specified file"
    else:
        configured = susy_cross_section.config.table_names.get(data_name)
        if configured:
            # configured by default
            error_hint = "configured path"
            if len(configured) == 2 and len(configured[0]) > 1:
                # if config has (data_path, info_path)
                data = pathlib.Path(configured[0])
                if info:
                    error_hint = "configured path (with modified info_path)"
                else:
                    info = pathlib.Path(configured[1])
            else:
                # if config has data_path
                assert isinstance(configured, str)
                data = pathlib.Path(configured)
        else:
            # interpret the input as path to a file.
            error_hint = "specified file"
            data = pathlib.Path(data_name)

    if not info:
        info = data.with_suffix(".info")

    # made it absolute
    pwd = pathlib.Path(__file__).parent
    abs_data = data if data.is_absolute() else pwd / data
    abs_info = info if info.is_absolute() else pwd / info

    for p in [abs_data, abs_info]:
        if not p.exists:
            logger.error(error_hint + " not found: %s", p)
            raise FileNotFoundError(p.__str__())  # py2
        if not p.is_file:
            logger.error(error_hint + " not a file: %s", p)
            raise RuntimeError("Not a file: %s", p.__str__())  # py2
    return abs_data, abs_info
