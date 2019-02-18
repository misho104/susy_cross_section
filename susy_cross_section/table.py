"""Classes for annotations to a table.

====================== ================================================
CrossSectionAttributes physical property of cross section.
CrossSectionInfo       `TableInfo` with `CrossSectionAttributes`.
Table                  grid data with `CrossSectionInfo`.
====================== ================================================
"""

from __future__ import absolute_import, division, print_function  # py2

import logging
import pathlib
import sys
import textwrap
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

from susy_cross_section.base.info import TableInfo
from susy_cross_section.base.table import BaseTable

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

    def dump(self):
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


class CrossSectionInfo(TableInfo):
    """Stores annotations of a cross section table.

    Annotation for cross section tables are `TableInfo` plus one
    `CrossSectionAttributes` object.

    Attributes
    ----------
    attributes: CrossSectionAttributes
        Information provided particularly for the cross section.

        General information intended to the users should be stored in
        `!document`, while the content of `!attributes` should be neat,
        standardized, and easy-to-parse objects.
    """

    def __init__(self, attributes=None, **kw):
        # type: (CrossSectionAttributes, Any)->None
        self.attributes = (
            attributes or CrossSectionAttributes()
        )  # type: CrossSectionAttributes
        super(CrossSectionInfo, self).__init__(**kw)  # py2

    @classmethod
    def load(cls, source):
        # type: (Union[pathlib.Path, str])->CrossSectionInfo
        """Load and construct CrossSectionInfo from a json file.

        Parameters
        ----------
        source: pathlib.Path or str
            Path to the json file.

        Returns
        -------
        CrossSectionInfo
            Constructed instance.
        """
        return cast(CrossSectionInfo, super(CrossSectionInfo, cls).load(source))  # py2

    def _load(self, **kw):
        # type: (Any)->None
        """Construct CrossSectionInfo from json data.

        Raises
        ------
        KeyError
            If json data lacks value for 'attributes'.
        """
        attributes = CrossSectionAttributes(**kw["attributes"])
        del kw["attributes"]
        super(CrossSectionInfo, self)._load(**kw)  # py2
        self.attributes = attributes

    def validate(self):
        # type: ()->None
        """Validate the content.

        This method calls children's and superclass' `!validate()` method, so
        exceptions are raised from them.
        """
        super(CrossSectionInfo, self).validate()  # py2
        self.attributes.validate()

    def dump(self):
        # type: ()->str
        """Return the formatted string.

        Returns
        -------
        str
            Dumped data.
        """
        return "\n".join(
            [
                super(CrossSectionInfo, self).dump(),
                "",
                "[Cross section attributes]",
                textwrap.indent(self.attributes.dump(), prefix="  "),
            ]
        )


class Table(BaseTable):
    """Data of a cross section with parameters, read from a table file.

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
    self.
    """

    def __init__(self, table_path, info_path=None):
        # type: (Union[pathlib.Path, str], Union[pathlib.Path, str])->None
        self.table_path = pathlib.Path(table_path)  # type: pathlib.Path
        self.info_path = (
            pathlib.Path(info_path)
            if info_path
            else self.table_path.with_suffix(".info")
        )  # type: pathlib.Path

        self.info = CrossSectionInfo.load(self.info_path)  # type: TableInfo
        self.raw_data = self._read_csv(self.table_path)  # type: pandas.DataFrame

        # contents are filled in _load_data
        self.data = {}  # type: MutableMapping[str, pandas.DataFrame]
        self.units = {}  # type: MutableMapping[str, str]

        self.info.validate()  # validate annotation before actual load
        self._load_data()
        self.validate()
