"""Classes for annotations to a table.

====================== ================================================
CrossSectionAttributes represents physical property of cross section.
Table                  extends `BaseTable` to handle cross-section
                       specific attributes
File                   extends `BaseFile` to carry `Table` objects.
====================== ================================================
"""

from __future__ import absolute_import, division, print_function  # py2

import logging
import pathlib
import sys
from typing import (  # noqa: F401
    Any,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    SupportsFloat,
    Tuple,
    Union,
    cast,
)

import pandas  # noqa: F401

from susy_cross_section.base.info import FileInfo
from susy_cross_section.base.table import BaseFile, BaseTable

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class CrossSectionAttributes(object):
    """Stores physical attributes of a cross section table.

    These information is intended to be handled by program codes, so the
    content should be neat, clear, and ready to be standardized.

    Attributes
    ----------
    processes: list of str
        The processes included in the cross section values. MadGraph5 syntax is
        recommended. Definiteness should be best respected.
    collider: str
        The type of collider, e.g., ``"pp"``, ``"e+e-"``.
    ecm: str
        The initial collision energy with unit.
    order: str
        The order of the cross-section calculation.
    pdf_name: str
        The name of PDF used in calculation.

        The `LHAPDF's set name <https://lhapdf.hepforge.org/pdfsets>`_ is
        recommended.
    """

    def __init__(self, processes="", collider="", ecm="", order="", pdf_name=""):
        # type: (Union[str, List[str]], str, str, str, str)->None
        if not processes:
            self.processes = []  # type: List[str]
        elif isinstance(processes, str):
            self.processes = [processes]
        else:
            self.processes = processes
        self.collider = collider  # type: str
        self.ecm = ecm  # type: str            # because it is always with units
        self.order = order  # type: str
        self.pdf_name = pdf_name  # type: str

    def validate(self):
        # type: ()->None
        """Validate the content.

        Type is also strictly checked in order to validate info files.

        Raises
        ------
        TypeError
            If any attributes are invalid type of instance.
        ValueError
            If any attributes have invalid content.
        """
        for attr, typ in [
            ("processes", List),
            ("collider", str),
            ("ecm", str),
            ("order", str),
            ("pdf_name", str),
        ]:
            value = getattr(self, attr)
            if not value:
                raise ValueError("attributes: %s is empty.", attr)
            if not isinstance(value, typ):
                raise TypeError("attributes: %s must be %s", attr, typ)
        if not all(isinstance(s, str) and s for s in self.processes):
            raise TypeError("attributes: processes must be a list of string.")

    def formatted_str(self):
        # type: ()->str
        """Return the formatted string.

        Returns
        -------
        str
            Dumped data.
        """
        lines = [
            "collider: {}-collider, ECM={}".format(self.collider, self.ecm),
            "calculation order: {}".format(self.order),
            "PDF: {}".format(self.pdf_name),
            "included processes:",
        ]
        for p in self.processes:
            lines.append("  " + p)
        return "\n".join(lines)


class Table(BaseTable):
    """Table object with annotations."""

    def __init__(self, obj=None, file_info=None, name=None):
        # type: (Any, Optional[FileInfo], Optional[str])->None
        if isinstance(obj, BaseTable):
            self._df = obj._df  # type: pandas.DataFrame
            self.file_info = file_info or obj.file_info  # type: Optional[FileInfo]
            self.name = name or obj.name
        elif isinstance(obj, pandas.DataFrame):
            self._df = obj
            self.file_info = file_info
            self.name = name
        else:
            self._df = pandas.DataFrame()
            self.file_info = file_info
            self.name = name

    def __str__(self):
        # type: ()->str
        """Dump the data-frame with information."""
        return "\n\n".join(
            [super(Table, self).__str__(), self.attributes.formatted_str()]
        )

    @property
    def unit(self):
        # type: ()->str
        """Return the unit of table values."""
        if self.file_info and self.name:
            return self.file_info.get_column(self.name).unit
        else:
            raise RuntimeError("No information is given for this table.")

    @property
    def attributes(self):
        # type: ()->CrossSectionAttributes
        """Return the information associated to this table."""
        if self.file_info and self.name:
            value_info = [v for v in self.file_info.values if v.column == self.name]
            if not value_info:
                raise RuntimeError("Value-info lookup failed.")
            return CrossSectionAttributes(**value_info[0].attributes)
        else:
            raise RuntimeError("No information is given for this table.")


class File(BaseFile):
    """Data of a cross section with parameters, read from a table file.

    Contents are the same as superclass but each table is extended from
    `BaseTable` to `Table` class.

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
    tables: dict(str, Table)
        The cross-section table parsed according to the annotation.
    """

    def __init__(self, table_path, info_path=None):
        # type: (Union[pathlib.Path, str], Union[pathlib.Path, str])->None
        super(File, self).__init__(table_path, info_path)
        self.tables = {k: Table(v) for k, v in self.tables.items()}
