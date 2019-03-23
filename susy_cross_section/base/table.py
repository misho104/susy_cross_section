"""Tables representing values with asymmetric uncertainties.

This module provides a class to handle CSV-like table data representing values
with asymmetric uncertainties. Such tables are provided in various format; for
example, the uncertainty may be relative or absolute, or with multiple sources.
The class :class:`BaseFile` interprets such tables based on `FileInfo`
annotations.
"""

from __future__ import absolute_import, division, print_function  # py2

import itertools
import json
import logging
import pathlib  # noqa: F401
import sys
from typing import (  # noqa: F401
    Any,
    Generic,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
    cast,
)

import pandas

from susy_cross_section.base.info import FileInfo, UncSpecType, ValueInfo
from susy_cross_section.utility import Unit

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821
    JSONDecodeError = Exception
else:
    JSONDecodeError = json.decoder.JSONDecodeError


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

PathLike = Union[pathlib.Path, str]
TableT = TypeVar("TableT", bound="BaseTable", covariant=True)


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
        # type:(pandas.DataFrame, Optional[BaseFile[BaseTable]], Optional[str])->None
        if isinstance(obj, pandas.DataFrame):
            self._df = obj  # type: pandas.DataFrame
        else:
            self._df = pandas.DataFrame()
        self.file = file  # type: Optional[BaseFile[BaseTable]]
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


class BaseFile(Generic[TableT]):
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
        # type: (Union[PathLike, BaseFile[TableT]], Optional[PathLike])->None
        if isinstance(table_path, BaseFile):
            # copy constructor
            assert info_path is None  # or invalid use of copy constructor
            self.table_path = table_path.table_path  # type: pathlib.Path
            self.info_path = table_path.info_path  # type: pathlib.Path
            self.info = table_path.info  # type: FileInfo
            self.raw_data = table_path.raw_data  # type: pandas.DataFrame
            self.tables = table_path.tables  # type: MutableMapping[str, TableT]
            return

        self.table_path = pathlib.Path(table_path)
        self.info_path = pathlib.Path(
            info_path if info_path else self.table_path.with_suffix(".info")
        )

        self.info = FileInfo.load(self.info_path)
        self.raw_data = self._read_csv(self.table_path)

        # validate annotation before actual load
        self.info.validate()
        # and do actual loading
        self.tables = self._parse_data()
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
        # type: ()->MutableMapping[str, TableT]
        """Load and prepare data from the specified paths."""
        tables = {}  # type: MutableMapping[str, TableT]

        def calc(row, unc_sources, sign):
            # type: (pandas.Series, List[UncSpecType], int)->float
            """Calculate uncertainty from a row in normalized dataframe."""
            unc_components = []  # type: List[float]
            for source, unc_type in unc_sources:  # iterate over sources
                if "signed" in unc_type.split(","):
                    # use only the correct-signed uncertainties
                    unc_candidates = [abs(row[c]) for c in source if row[c] * sign > 0]
                else:
                    unc_candidates = [abs(row[c]) for c in source]
                unc_components.append(max(unc_candidates) if unc_candidates else 0)
            return sum(i ** 2 for i in unc_components) ** 0.5

        for value_info in self.info.values:
            name = value_info.column
            data = self._prepare_normalized_data(value_info)
            tables[name] = cast(TableT, BaseTable(file=self, name=name))
            tables[name]["value"] = data[name]
            for key, row in data.iterrows():
                tables[name].loc[key, "unc+"] = calc(row, value_info.unc_p, +1)
                tables[name].loc[key, "unc-"] = calc(row, value_info.unc_m, -1)

        return tables

    def _prepare_normalized_data(self, value_info):
        # type: (ValueInfo)->pandas.DataFrame
        """Quantize parameters and normalize columns to value_info.column."""
        data = self.raw_data.copy()

        def quantize(data_frame, granularity):
            # type: (pandas.DataFrame, float)->pandas.DataFrame
            return (data_frame / granularity).apply(round) * granularity

        # set index by the quantized values
        for p in self.info.parameters:
            if p.granularity:
                data[p.column] = quantize(data[p.column], p.granularity)
        data.set_index([p.column for p in self.info.parameters], inplace=True)

        # collect columns to use
        abs_columns, rel_columns = set(), set()  # type: Set[str], Set[str]
        for unc_cols, unc_type in itertools.chain(value_info.unc_p, value_info.unc_m):
            is_relative = "relative" in unc_type.split(",")
            for c in unc_cols:
                (rel_columns if is_relative else abs_columns).add(c)
        assert abs_columns.isdisjoint(rel_columns)

        name = value_info.column
        value_unit = Unit(self.info.get_column(name).unit)
        for col in data.columns:
            if col == value_info.column:
                pass
            elif col in abs_columns:
                # unc / unc_unit == "number in the table"
                # we want to get "unc / value_unit"
                # = "number in the table" * unc_unit / value_unit
                unc_unit = Unit(self.info.get_column(col).unit)
                data[col] = data[col] * float(unc_unit / value_unit)
            elif col in rel_columns:
                unc_unit = Unit(self.info.get_column(col).unit) * value_unit
                data[col] = data[name] * data[col] * float(unc_unit / value_unit)
            else:
                data.drop(col, axis=1, inplace=True)
        return data

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
            results.append(u"{}: {}".format(k, v))
        results.append(line)
        return "\n".join(results)
