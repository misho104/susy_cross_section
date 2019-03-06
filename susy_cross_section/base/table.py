"""Tables representing values with asymmetric uncertainties.

This module provides a class to handle CSV-like table data representing values
with asymmetric uncertainties. Such tables are provided in various format; for
example, the uncertainty may be relative or absolute, or with multiple sources.
The class :class:`BaseFile` interprets such tables based on `FileInfo`
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
    cast,
)

import pandas

from susy_cross_section.base.info import FileInfo
from susy_cross_section.utility import Unit

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821
    JSONDecodeError = Exception
else:
    JSONDecodeError = json.decoder.JSONDecodeError


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class BaseTable(object):
    """Table object with annotations.

    This is a wrapper class of :class:`pandas.DataFrame`. Any methods except
    for read/write of `!file` are delegated to the DataFrame object.

    Attributes
    ----------
    file: BaseFile, optional
        File object containing this table.
    name: str, optional
        Name of this table.

        This is provided so that `ValueInfo` can be obtained from `!file`.
    """

    def __init__(self, obj=None, file=None, name=None):
        # type:(pandas.DataFrame, Optional[BaseFile], Optional[str])->None
        if isinstance(obj, pandas.DataFrame):
            self._df = obj  # type: pandas.DataFrame
        else:
            self._df = pandas.DataFrame()
        self.file = file  # type: Optional[BaseFile]
        self.name = name  # type: Optional[str]

    def __getattr__(self, name):
        # type: (str)->Any
        """Fall-back method to delegate any operations to the DataFrame."""
        return self._df.__getattr__(name)

    def __setitem__(self, name, obj):
        # type: (str, Any)->Any
        """Perform DataFrame.__setitem__."""
        return self._df.__setitem__(name, obj)

    def __getitem__(self, name):
        # type: (str)->Any
        """Perform DataFrame.__getitem__."""
        return self._df.__getitem__(name)

    def __str__(self):
        # type: ()->str
        """Dump the data-frame."""
        return cast(str, self._df.__str__())


class BaseFile(object):
    """File with table data-sets and annotations.

    An instance has two main attributes: `!info` (:typ:`FileInfo`) as the
    annotation and `!tables` (:typ:`dict` of :typ:`BaseTable`) as the data
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
    info: FileInfo
        the content of `!info_path`.
    tables: dict(str, BaseTable)
        The table parsed according to the annotation.

        Each value is practically a `pandas.DataFrame` object and indexed
        according to the parameter specified in `!info`, having exactly three
        value-columns: ``"value"``, ``"unc+"``, and ``"unc-"`` for the central
        value and positive- and negative- directed **absolute** uncertainty,
        respectively. The content of ``"unc-"`` is non-positive.
    """

    def __init__(self, table_path, info_path=None):
        # type: (Union[pathlib.Path, str], Union[pathlib.Path, str])->None
        self.table_path = pathlib.Path(table_path)  # type: pathlib.Path
        self.info_path = pathlib.Path(
            info_path if info_path else self.table_path.with_suffix(".info")
        )  # type: pathlib.Path

        self.info = FileInfo.load(self.info_path)  # type: FileInfo
        self.raw_data = self._read_csv(self.table_path)  # type: pandas.DataFrame

        # validate annotation before actual load
        self.info.validate()
        # and do actual loading
        self.tables = self._parse_data()  # type: MutableMapping[str, BaseTable]
        self.validate()

    def _read_csv(self, path):
        # type: (pathlib.Path)->pandas.DataFrame
        """Read a csv file and return the content.

        Internally, call `pandas.read_csv` with `!reader_options`.
        """
        reader_options = {
            "skiprows": [0],
            "names": [c.name for c in self.info.columns],
        }  # default values
        reader_options.update(self.info.reader_options)
        return pandas.read_csv(path, **reader_options)

    def _parse_data(self):
        # type: ()->MutableMapping[str, BaseTable]
        """Load and prepare data from the specified paths."""
        tables = {}  # type: MutableMapping[str, BaseTable]
        for value_info in self.info.values:
            name = value_info.column
            value_unit = self.info.get_column(name).unit
            parameters = self.info.parameters
            data = self.raw_data.copy()

            # set index by the quantized values
            def quantize(data_frame, granularity):
                # type: (pandas.DataFrame, float)->pandas.DataFrame
                return (data_frame / granularity).apply(round) * granularity

            for p in parameters:
                if p.granularity:
                    data[p.column] = quantize(data[p.column], p.granularity)

            data.set_index([p.column for p in parameters], inplace=True)

            # define functions to apply to DataFrame to get uncertainty.
            up_factors = self._uncertainty_factors(Unit(value_unit), value_info.unc_p)
            um_factors = self._uncertainty_factors(Unit(value_unit), value_info.unc_m)

            def unc_p(row, name=name, unc_sources=value_info.unc_p, factors=up_factors):
                # type: (Any, str, Mapping[str, str], Mapping[str, float])->float
                return self._combine_uncertainties(row, name, unc_sources, factors)

            def unc_m(row, name=name, unc_sources=value_info.unc_m, factors=um_factors):
                # type: (Any, str, Mapping[str, str], Mapping[str, float])->float
                return self._combine_uncertainties(row, name, unc_sources, factors)

            tables[name] = BaseTable(file=self, name=name)
            tables[name]["value"] = data[name]
            tables[name]["unc+"] = data.apply(unc_p, axis=1)
            tables[name]["unc-"] = data.apply(unc_m, axis=1)
        return tables

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
        for name, typ in unc_sources.items():
            if typ == "relative":
                uncertainties.append(row[name] * factors[name] * row[value_name])
            elif typ == "absolute":
                uncertainties.append(row[name] * factors[name])
            else:
                raise ValueError(typ)

        return sum(x ** 2 for x in uncertainties) ** 0.5

    def validate(self):
        # type: ()->None
        """Validate the Table data."""
        for key, table in self.tables.items():
            duplication = table.index[table.index.duplicated()]
            for d in duplication:
                raise ValueError("Found duplicated entries: %s, %s", key, d)
                if len(duplication) > 5:
                    raise ValueError("Maybe parameter granularity is set too large?")

    # ------------------ #
    # accessor functions #
    # ------------------ #

    def __getitem__(self, key):
        # type: (str)->BaseTable
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
        return self.tables[key]

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
        keys_to_show = self.tables.keys() if keys is None else keys
        for k in keys_to_show:
            results.append(line)
            results.append('TABLE "{}" (unit: {})'.format(k, self.tables[k].unit))
            results.append(line)
            results.append(self.tables[k].__str__())  # py2
            results.append("")

        results.append(line)
        for k, v in self.info.document.items():
            results.append("{}: {}".format(k, v))
        results.append(line)
        return "\n".join(results)
