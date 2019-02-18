"""Tables representing values with asymmetric uncertainties.

This module provides a class to handle CSV-like table data representing values
with asymmetric uncertainties. Such tables are provided in various format; for
example, the uncertainty may be relative or absolute, or with multiple sources.
The class :class:`BaseTable` interprets such tables based on `TableInfo`
annotations.
"""

from __future__ import absolute_import, division, print_function  # py2

import json
import logging
import pathlib  # noqa: F401
import sys
from typing import (  # noqa: F401
    Any,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Union,
)

import pandas

from susy_cross_section.base.info import TableInfo
from susy_cross_section.utility import Unit

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821
    JSONDecodeError = Exception
else:
    JSONDecodeError = json.decoder.JSONDecodeError


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class BaseTable(object):
    """Table data with information.

    A table object has two main attributes: `!info` (:typ:`TableInfo`) as the
    annotation and `!data` (:typ:`dict` of :typ:`pandas.DataFrame`) as the data
    tables.

    Arguments
    ---------
    table_path: str or pathlib.Path
        Path to the csv data file.
    info_path: str or pathlib.Path, optional
        Path to the corresponding info file.

        If unspecified, `!table_path` with suffix changed to ``".info"`` is
        used.

    Attributes
    ----------
    table_path: pathlib.Path
        Path to the csv data file.
    info_path: pathlib.Path
        Path to the info file.
    raw_data: pandas.DataFrame
        the content of `!table_path`.
    info: TableInfo
        the content of `!info_path`.
    data: dict(str, pandas.DataFrame)
        The table parsed according to the annotation.

        Keys are the name of data, and values are `pandas.DataFrame` objects.
        Each DataFrame object is indexed according to the parameter specified
        in `!info` and has exactly three value-columns: ``"value"``,
        ``"unc+"``, and ``"unc-"``, which stores the central value and
        positive- and negative- directed **absolute** uncertainty,
        respectively. The content of ``"unc-"`` is non-positive.
    units: dict(str, Utility.Unit)
        The unit of values.

        Note that ``"value"``, ``"unc+"``, and ``"unc-"`` have the same unit.
    """

    def __init__(self, table_path, info_path=None):
        # type: (Union[pathlib.Path, str], Union[pathlib.Path, str])->None
        self.table_path = pathlib.Path(table_path)  # type: pathlib.Path
        self.info_path = pathlib.Path(
            info_path if info_path else self.table_path.with_suffix(".info")
        )  # type: pathlib.Path

        self.info = TableInfo.load(self.info_path)  # type: TableInfo
        self.raw_data = self._read_csv(self.table_path)  # type: pandas.DataFrame

        # contents are filled in _load_data
        self.data = {}  # type: MutableMapping[str, pandas.DataFrame]
        self.units = {}  # type: MutableMapping[str, str]

        self.info.validate()  # validate annotation before actual load
        self._load_data()
        self.validate()

    def _read_csv(self, path):
        # type: (pathlib.Path)->pandas.DataFrame
        """Read a csv file and return the content.

        Internally, call :meth:`pandas.read_csv()` with `!reader_options`.
        """
        reader_options = {
            "skiprows": [0],
            "names": [c.name for c in self.info.columns],
        }  # default values
        reader_options.update(self.info.reader_options)
        return pandas.read_csv(path, **reader_options)

    def _load_data(self):
        # type: ()->None
        """Load and prepare data from the specified paths."""
        self.data = {}  # type: MutableMapping[str, pandas.DataFrame]
        self.units = {}  # type: MutableMapping[str, str]
        for value_info in self.info.values:
            name = value_info.column
            value_unit = self.info.get_column(name).unit
            parameters = self.info.parameters
            data = self.raw_data.copy()

            # set index by the quantized values
            for p in parameters:
                data[p.column] = (data[p.column] / p.granularity).apply(round) * p.granularity
            data.set_index([p.column for p in parameters], inplace=True)

            # define functions to apply to DataFrame to get uncertainty.
            unc_p_factors = self._uncertainty_factors(Unit(value_unit), value_info.unc_p)
            unc_m_factors = self._uncertainty_factors(Unit(value_unit), value_info.unc_m)

            def unc_p(row,
                      name=name,
                      unc_sources=value_info.unc_p,
                      factors=unc_p_factors):
                # type: (Any, str, Mapping[str, str], Mapping[str, float])->float
                return self._combine_uncertainties(row, name, unc_sources, factors)

            def unc_m(row,
                      name=name,
                      unc_sources=value_info.unc_m,
                      factors=unc_m_factors):
                # type: (Any, str, Mapping[str, str], Mapping[str, float])->float
                return self._combine_uncertainties(row, name, unc_sources, factors)

            self.data[name] = pandas.DataFrame()
            self.data[name]["value"] = data[name]
            self.data[name]["unc+"] = data.apply(unc_p, axis=1)
            self.data[name]["unc-"] = data.apply(unc_m, axis=1)
            self.units[name] = value_unit

    def _uncertainty_factors(self, value_unit, uncertainty_info):
        # type: (Unit, Mapping[str, str])->Mapping[str, float]
        """Return the factor of uncertainty column relative to value column."""
        factors = {}
        for source_name, source_type in uncertainty_info.items():
            unc_unit = Unit(self.info.get_column(source_name).unit)
            if source_type == "relative":
                unc_unit *= value_unit
            # unc / unc_unit == "number in the table"
            # we want to get "unc / value_unit" = "number in the table"  * unc_unit / value_unit
            factors[source_name] = float(unc_unit / value_unit)
        return factors

    @staticmethod
    def _combine_uncertainties(row, value_name, unc_sources, factors):
        # type: (Any, str, Mapping[str, str], Mapping[str, float])->float
        """Return absolute combined uncertainty."""
        uncertainties = []
        for source_name, source_type in unc_sources.items():
            uncertainties.append(row[source_name] * factors[source_name] * (
                row[value_name] if source_type == "relative" else 1
            ))
        return sum(x**2 for x in uncertainties) ** 0.5

    def validate(self):
        # type: ()->None
        """Validate the Table data."""
        for key, data in self.data.items():
            duplication = data.index[data.index.duplicated()]
            for d in duplication:
                raise ValueError("Found duplicated entries: %s, %s", key, d)
                if len(duplication) > 5:
                    raise ValueError("Maybe parameter granularity is set too large?")

    # ------------------ #
    # accessor functions #
    # ------------------ #

    def __getitem__(self, key):
        # type: (str)->pandas.DataFrame
        """Return the specied table data.

        Arguments
        ---------
        key: str
            One of The key of the data to return.

        Returns
        -------
        pandas.DataFrame
            One of the data tables specified by :ar:`key`.
        """
        return self.data[key]

    def dump(self, keys=None):
        # type: (Optional[List[str]])->str
        """Return the dumped string of the data tables.

        Arguments
        ---------
        keys: list of str, optional
            if specified, specified data are only dumped.

        Returns
        -------
        str
            Dumped data.
        """
        results = []  # type: List[str]
        line = "-" * 72
        keys_to_show = self.data.keys() if keys is None else keys
        for k in keys_to_show:
            results.append(line)
            results.append('DATA "{}" (unit: {})'.format(k, self.units[k]))
            results.append(line)
            results.append(self.data[k].__str__())  # py2
            results.append("")
        return "\n".join(results)
