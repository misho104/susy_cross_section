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
from typing import Any, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union

from numpy import log10

from susy_cross_section.config import table_paths

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821
    FileNotFoundError = OSError  # noqa: A001, F821


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

PathLike = Union[str, pathlib.Path]
TypeSpecType = Optional[Union[type, Sequence[type]]]


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


def value_format(value, unc_p, unc_m, unit=None, relative=False):
    # type: (float, float, float, Optional[str], bool)->str
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
    relative: bool
        Whether to show the uncertainties in relative.

    Returns
    -------
    str
        Formatted string describing the given value.
    """
    delta = min(abs(unc_p), abs(unc_m))
    suffix = " {}".format(unit) if unit else ""  # will be appended to the body.

    if relative:
        return "{:g}{} +{:.2%} -{:.2%}".format(
            value, suffix, unc_p / value, abs(unc_m) / value
        )

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
    # type: (PathLike, Optional[PathLike])->Tuple[pathlib.Path, pathlib.Path]
    """Return paths to data file and info file.

    Parameters
    ----------
    data_name: pathlib.Path or str
        Path to grid-data file or a table name predefined in configuration.

        If a file with :ar:`data_name` is found, the file is used. Otherwise,
        :ar:`data_name` must be a pre-defined table key, or raises KeyError.
    info_path: pathlib.Path or str, optional
        Path to info file, which overrides the default setting.

        The default setting is the grid-file path with suffix changed to
        ".info".

    Returns
    -------
    Tuple[pathlib.Path, pathlib.Path]
        Paths to data file and info file; absolute if preconfigured.

    Raises
    ------
    FileNotFoundError
        If one of the specified files is not found.
    """
    # check preconfigured grid- and info-paths
    if isinstance(data_name, pathlib.Path):
        # if path is specified, do not see the configuration.
        configured_grid, configured_info = None, None
        specified_grid = data_name
        specified_info = pathlib.Path(info_path) if info_path else None
    else:
        # here abs path should be calculated for configured (but not for specified)
        configured_grid, configured_info = table_paths(data_name, absolute=True)
        specified_grid = pathlib.Path(data_name)
        specified_info = pathlib.Path(info_path) if info_path else None

    def check_file(path, err_message, err_info=None):
        # type: (pathlib.Path, str, Optional[Sequence[str]])->None
        if not path.is_file():
            logger.critical(err_message, path.__str__())
            for i in err_info or []:
                logger.info(i)
            raise FileNotFoundError(path.__str__())

    if specified_grid.is_file():  # use specified path.
        if configured_grid:
            # warn if the same key found in config.
            logger.warning(
                "The file %s is used, ignoring the predefined table %s.",
                specified_grid.absolute().__str__(),
                data_name,
            )
        specified_info = specified_info or specified_grid.with_suffix(".info")
        check_file(
            specified_info,
            "Info file %s not found.",
            (
                "It seems that you specified a wrong path for info file."
                if info_path
                else "If info-file has a different name, it must be specified."
            ),
        )
        return specified_grid, specified_info

    elif configured_grid:
        # check grid-file
        check_file(
            configured_grid,
            "The preconfigured grid file %s not found.",
            ["Maybe the susy-cross-section package is broken?"],
        )
        # check info-file; if specified, use it.
        if specified_info:
            check_file(specified_info, "The specified info file %s not found.")
            return configured_grid, specified_info
        configured_info = configured_info or configured_grid.with_suffix(".info")
        check_file(
            configured_info,
            "The preconfigured info file %s not found.",
            ["Maybe the susy-cross-section package is broken?"],
        )
        return configured_grid, configured_info

    else:
        # grid file not found.
        logger.critical('The grid file for "%s" not found.', data_name.__str__())
        logger.info("For a preconfigured table, double-check the key of the table.")
        logger.info("If you specified a file-path, verify it exists as a file.")
        raise FileNotFoundError(data_name.__str__())


class TypeCheck:
    """Singleton class for methods to type assertion."""

    @staticmethod
    def is_list(obj, element_type=None):
        # type: (Any, TypeSpecType)->bool
        """Return if obj is a list with elements of specified type.

        Arguments
        ---------
        obj:
            object to test.
        element_type: type or list of type, optional
            Allowed types for elements.

        Returns
        -------
        bool:
            Validation result.
        """
        if isinstance(obj, str) or not isinstance(obj, Sequence):
            return False
        if element_type is not None:
            types = element_type if isinstance(element_type, list) else [element_type]
            for item in obj:
                if not any(isinstance(item, t) for t in types):
                    return False
        return True

    @staticmethod
    def is_dict(obj, key_type=None, value_type=None):
        # type: (Any, TypeSpecType, TypeSpecType)->bool
        """Return if obj is a dict with keys/values of specified type.

        Arguments
        ---------
        obj:
            object to test.
        key_type: type or list of type, optional
            Allowed types for keys.
        key_type: type or list of type, optional
            Allowed types for values.

        Returns
        -------
        bool:
            Validation result.
        """
        if not isinstance(obj, Mapping):
            return False

        kt = vt = None
        if key_type:
            kt = key_type if isinstance(key_type, list) else [key_type]
        if value_type:
            vt = value_type if isinstance(value_type, list) else [value_type]

        for k, v in obj.items():
            if kt and not any(isinstance(k, t) for t in kt):
                return False
            if vt and not any(isinstance(v, t) for t in vt):
                return False
        return True
