"""Classes to describe annotations of general-purpose tables.

This module provides annotation classes for CSV-like table data. The data is a
two-dimensional table and represents functions over a parameter space. Some
columns represent parameters and others do values. Each row represents a single
data point and corresponding value.

Two structural annotations and two semantic annotations are defined. `FileInfo`
and `ColumnInfo` are structural, which respectively annotate the whole file and
each columns. For semantics, `ParameterInfo` collects the information of
parameters, each of which is a column, and `ValueInfo` is for a value. A value
may be given by multiple columns if, for example, the value has uncertainties
or the value is given by the average of two columns.
"""

from __future__ import absolute_import, division, print_function  # py2

import itertools
import json
import logging
import pathlib  # noqa: F401
import sys
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple, Union

from susy_cross_section.utility import TypeCheck as TC

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821
    JSONDecodeError = Exception
else:
    JSONDecodeError = json.decoder.JSONDecodeError


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

UncSpecType = Tuple[List[str], str]


class ColumnInfo(object):
    """Stores information of a column.

    Instead of the :typ:`int` identifier `!index`, we use `!name` as the
    principal identifier for readability. We also annotate a column by `!unit`,
    which is :typ:`str` that is passed to `Unit()`.

    Attributes
    ----------
    index : int
        The zero-based index of column.

        The columns of a file should have valid `!index`, i.e., no overlap, no
        gap, and starting from zero.
    name : str
        The human-readable and machine-readable name of the column.

        As it is used as the identifier, it should be unique in one file.
    unit : str
        The unit of column, or empty string if the column has no unit.

        The default value is an empty str ``''``, which means the column has no
        unit. Internally this is passed to `Unit()`.

    Note
    ----
    As for now, `!unit` is restricted as a str object, but in future a float
    should be allowed to describe "x1000" etc.
    """

    def __init__(self, index, name, unit=""):
        # type: (int, str, str)->None
        self.index = index  # type: int
        self.name = name  # type: str
        self.unit = unit or ""  # type: str

    @classmethod
    def from_json(cls, json_obj):
        # type: (Any)->ColumnInfo
        """Initialize an instance from valid json data.

        Parameters
        ----------
        json_obj: Any
            a valid json object.

        Returns
        -------
        ColumnInfo
            Constructed instance.

        Raises
        ------
        ValueError
            If :ar:`json_obj` has invalid data.
        """
        try:
            obj = cls(
                index=json_obj["index"],
                name=json_obj["name"],
                unit=json_obj.get("unit", ""),
            )
        except (TypeError, AttributeError) as e:
            logger.critical("ColumnInfo.from_json caught an exception.", exc_info=e)
            raise ValueError("Invalid data passed to ColumnInfo.from_json: %s")
        except KeyError as e:
            logger.critical("ColumnInfo.from_json caught an exception.", exc_info=e)
            raise ValueError("ColumnInfo data missing: %s", e)

        for k in json_obj.keys():
            if k not in ["index", "name", "unit"]:
                logger.warning("Unknown data for ColumnInfo.from_json: %s", k)

        obj.validate()
        return obj

    def to_json(self):
        # type: ()->MutableMapping[str, Union[str, int]]
        """Serialize the object to a json data.

        Returns
        -------
        dict(str, str or int)
            The json data describing the object.
        """
        json_obj = {
            "index": self.index,
            "name": self.name,
        }  # type: MutableMapping[str, Union[str, int]]
        if self.unit:
            json_obj["unit"] = self.unit
        return json_obj

    def validate(self):
        # type: ()->None
        """Validate the content.

        Raises
        ------
        TypeError
            If any attributes are invalid type of instance.
        ValueError
            If any attributes have invalid content.
        """
        if not isinstance(self.index, int):
            raise TypeError("ColumnInfo.index must be int: %s", self.index)
        if not self.index >= 0:
            raise ValueError("ColumnInfo.index must be non-negative: %s", self.index)
        if not isinstance(self.name, str):
            raise TypeError("Col %d: `name` must be string: %s", self.index, self.name)
        if not self.name:
            raise ValueError("Column %d: `name` missing", self.index)
        if not isinstance(self.unit, str):
            raise TypeError("Col %d: `unit` must be string: %s", self.index, self.unit)


class ParameterInfo(object):
    """Stores information of a parameter.

    A parameter set defines a data point for the functions described by the
    file. A parameter set has one or more parameters, each of which
    corresponds to a column of the file. The `!column` attribute has
    :attr:`ColumnInfo.name` of the column.

    Since the parameter value is read from an ASCII file, :typ:`float` values
    might have round-off errors, which might cause grid misalignments in grid-
    based interpolations. To have the same :typ:`float` expression on the
    numbers that should be on the same grid, `!granularity` should be provided.

    Attributes
    ----------
    column: str
        Name of the column that stores this parameter.
    granularity: int or float, optional
        Assumed presicion of the parameter.

        This is used to round the parameter so that a data point should be
        exactly on the grid. Internally, a parameter is rounded to::

            round(value / granularity) * granularity

        For example, for a grid ``[10, 20, 30, 50, 70]``, it should be set to
        10 (or 5, 1, 0.1, etc.), while for ``[33.3, 50, 90]``, it should be
        0.01.
    """

    def __init__(self, column="", granularity=None):
        # type: (str, float)->None
        self.column = column  # type: str
        self.granularity = granularity or None  # type: Optional[float]

    @classmethod
    def from_json(cls, json_obj):
        # type: (Any)->ParameterInfo
        """Initialize an instance from valid json data.

        Parameters
        ----------
        json_obj: Any
            a valid json object.

        Returns
        -------
        ParameterInfo
            Constructed instance.

        Raises
        ------
        ValueError
            If :ar:`json_obj` has invalid data.
        """
        try:
            obj = cls(
                column=json_obj["column"], granularity=json_obj.get("granularity")
            )
        except (TypeError, AttributeError) as e:
            logger.critical("ParameterInfo.from_json caught an exception.", exc_info=e)
            raise ValueError("Invalid data passed to ParameterInfo.from_json: %s")
        except KeyError as e:
            logger.critical("ParameterInfo.from_json caught an exception.", exc_info=e)
            raise ValueError("ColumnInfo data missing: %s", e)

        for k in json_obj.keys():
            if k not in ["column", "granularity"]:
                logger.warning("Unknown data for ParameterInfo.from_json: %s", k)

        obj.validate()
        return obj

    def to_json(self):
        # type: ()->MutableMapping[str, Union[str, float]]
        """Serialize the object to a json data.

        Returns
        -------
        dict(str, str or float)
            The json data describing the object.
        """
        json_obj = {"column": self.column}  # type: Dict[str, Union[str, float]]
        if self.granularity:
            json_obj["granularity"] = self.granularity
        return json_obj

    def validate(self):
        # type: ()->None
        """Validate the content.

        Raises
        ------
        TypeError
            If any attributes are invalid type of instance.
        ValueError
            If any attributes have invalid content.
        """
        assert isinstance(self.column, str), "ParameterInfo.column must be string."
        assert self.column, "ParameterInfo.column is missing"
        if self.granularity is not None:
            assert hasattr(self.granularity, "__float__"), "Granularity not a number."
            assert float(self.granularity) > 0, "Negative granularity."


class ValueInfo(object):
    """Stores information of value accompanied by uncertainties.

    A value is generally composed from several columns. In current
    implementation, the central value must be given by one column, whose name
    is specified by :attr:`column`. The positive- and negative-direction
    uncertainties are specified by `!unc_p` and `!unc_m`, respectively, which
    are :typ:`dict(str, str)`.

    Attributes
    ----------
    column: str or List[str]
        Names of the column that stores this value.

        The string, or each element of the list, must match one of the
        :attr:`ColumnInfo.name` in the file. If multiple columns are specified,
        the largest value among the columns (compared in each row) is used.
    attributes: dict (str, Any)
        Physical information annotated to this value.
    unc_p : dict (str, str)
        The sources of "plus" uncertainties.

        Multiple uncertainty sources can be specified. Each key corresponds
        :attr:`ColumnInfo.name` of the source column, and each value denotes
        the "type" of the source. Currently, two types are implementend:

        - ``"relative"`` for relative uncertainty, where the unit of the column
          must be dimension-less.

        - ``"absolute"`` for absolute uncertainty, where the unit of the column
          must be the same as that of the value column up to a factor.

        - ``"absolute,signed"`` or ``"relative,signed"`` for absolute/relative
          uncertainty but using the columns with correct sign.
    unc_m : dict(str, str)
        The sources of "minus" uncertainties.

        Details are the same as `!unc_p`.
    """

    _valid_uncertainty_types = [
        "relative",
        "absolute",
        "signed,relative",
        "signed,absolute",
        "relative,signed",
        "absolute,signed",
    ]  # type: List[str]

    def __init__(
        self,
        column="",  # type: str
        attributes=None,  # type:MutableMapping[str, Any]
        unc_p=None,  # type: List[UncSpecType]
        unc_m=None,  # type: List[UncSpecType]
    ):
        # type: (...)->None
        self.column = column
        self.attributes = attributes or {}
        self.unc_p = unc_p or []
        self.unc_m = unc_m or []

    def validate(self):
        # type: ()->None
        """Validate the content."""
        assert isinstance(self.column, str), "ValueInfo.column must be string."
        assert self.column, "ValueInfo.column is missing."
        assert TC.is_dict(self.attributes, key_type=str), "attributes not dict[str]."
        for col, t in itertools.chain(self.unc_p, self.unc_m):
            assert TC.is_list(col, element_type=str)
            assert t in self._valid_uncertainty_types, "invalid unc type: %s" % t

    @classmethod
    def from_json(cls, json_obj):
        # type: (Any)->ValueInfo
        """Initialize an instance from valid json data.

        Parameters
        ----------
        json_obj: typing.Any
            a valid json object.

        Returns
        -------
        ValueInfo
            Constructed instance.

        Raises
        ------
        ValueError
            If :ar:`json_obj` has invalid data.
        """
        if not TC.is_dict(json_obj):
            raise TypeError('Entry of "values" must be a dict: %s', json_obj)
        if "column" not in json_obj:
            raise KeyError('Entry of "values" must have a key "column": %s', json_obj)

        obj = cls()
        obj.column = json_obj["column"]
        obj.attributes = json_obj.get("attributes", {})
        if ("unc" in json_obj) and ("unc+" in json_obj or "unc-" in json_obj):
            raise ValueError("Uncertainty duplicates: %s", obj.column)
        for attr_name, key_name in [("unc_p", "unc+"), ("unc_m", "unc-")]:
            unc_def = json_obj.get(key_name) or json_obj.get("unc") or None
            if unc_def is None:
                logger.warning("Uncertainty (%s) missing for %s.", key_name, obj.column)
                continue
            assert TC.is_list(unc_def, Mapping), "bad %s/%s" % (key_name, obj.column)
            try:
                unc_list = [
                    (
                        src["column"] if TC.is_list(src["column"]) else [src["column"]],
                        src["type"],
                    )
                    for src in unc_def
                ]
            except KeyError as e:
                raise ValueError("%s missing in %s (%s)", key_name, obj.column, *e.args)
            setattr(obj, attr_name, unc_list)

        if not (obj.unc_p and obj.unc_m):
            logger.warning("Value %s lacks uncertainties.", obj.column)

        return obj

    def to_json(self):
        # type: ()->MutableMapping[str, Any]
        """Serialize the object to a json data.

        Returns
        -------
        dict(str, str or float)
            The json data describing the object.
        """
        return {
            "column": self.column,
            "attributes": self.attributes,
            "unc+": [{"column": c, "type": t} for c, t in self.unc_p],
            "unc-": [{"column": c, "type": t} for c, t in self.unc_m],
        }


class FileInfo(object):
    """Stores file-wide annotations.

    A table structure is given by `!columns`, while in semantics a table
    consists of `!parameters` and `!values`. The information about them is
    stored as lists of `ColumnInfo`, `ParameterInfo`, and `ValueInfo` objects.
    In addition, `!reader_options` can be specified, which is directly passed
    to :func:`pandas.read_csv`.

    The attribute `!document` is provided just for documentation. The
    information is guaranteed not to modify any functionality of codes or
    packages, and thus can be anything.

    Developers must not use `!document` information except for displaying them.
    If one needs to interpret some information, one should extend this class to
    provide other data-storage for such information.

    Attributes
    ----------
    document : dict(Any, Any)
        Any information for documentation without physical meanings.
    columns : list of ColumnInfo
        The list of columns.
    parameters: list of ParameterInfo
        The list of parameters to define a data point.
    values: list of ValueInfo
        The list of values described in the file.
    reader_options: dict(str, Any)
        Options to read the CSV

        The values are directly passed to :func:`pandas.read_csv` as keyword
        arguments, so all the options of :func:`pandas.read_csv` are available.
    """

    def __init__(
        self,
        document=None,  # type: Mapping[Any, Any]
        columns=None,  # type: List[ColumnInfo]
        parameters=None,  # type: List[ParameterInfo]
        values=None,  # type: List[ValueInfo]
        reader_options=None,  # type: Mapping[str, Any]
    ):
        # type: (...)->None
        self.document = document or {}
        self.columns = columns or []
        self.parameters = parameters or []
        self.values = values or []
        self.reader_options = reader_options or {}

    def validate(self):
        # type: ()->None
        """Validate the content."""
        assert TC.is_dict(self.document), "document must be a dict."
        for name in ["columns", "parameters", "values"]:
            assert TC.is_list(getattr(self, name)), "FileInfo.%s must be a list" % name
            for obj in getattr(self, name):
                obj.validate()
        assert TC.is_dict(
            self.reader_options, key_type=str
        ), "reader_options must be a dict(str, Any)."

        # validate columns (`index` matches actual index, names are unique)
        names_dict = {}  # type: MutableMapping[str, bool]
        for i, col in enumerate(self.columns):
            assert col.index == i, "Mismatched column index: %d/%d" % (i, col.index)
            assert col.name not in names_dict, "Duplicated column name: " + col.name
            names_dict[col.name] = True

        # validate params and values
        for p in self.parameters:
            assert p.column in names_dict, "Unknown column name: %s" % p.column
        for v in self.values:
            assert v.column in names_dict, "Unknown column name: %s" % v.column
            for col_list, _ in itertools.chain(v.unc_p, v.unc_m):
                for c in col_list:
                    assert c in names_dict, "Unknown column name: %s" % c

    @classmethod
    def load(cls, source):
        # type: (Union[pathlib.Path, str])->FileInfo
        """Load and construct FileInfo from a json file.

        Parameters
        ----------
        source: pathlib.Path or str
            Path to the json file.

        Returns
        -------
        FileInfo
            Constructed instance.
        """
        obj = cls()
        with open(source.__str__()) as f:  # py2
            obj._load(**(json.load(f)))
        obj.validate()
        return obj

    def _load(self, **kw):
        # type: (Any)->None
        """Load and construct FileInfo from keyword arguments.

        Note that file-level "attributes" are passed to each `ValueInfo` object
        as the default values and overwritten by value-level "attributes".
        """
        self.document = kw.get("document") or {}
        self.reader_options = kw.get("reader_options") or {}
        self.columns = [
            ColumnInfo(index=i, name=c.get("name"), unit=c.get("unit"))
            for i, c in enumerate(kw.get("columns") or [])
        ]
        self.parameters = [
            ParameterInfo.from_json(p) for p in kw.get("parameters") or []
        ]
        self.values = [ValueInfo.from_json(p) for p in kw.get("values") or []]
        # re-set values.attributes using the default attributes.
        default_attributes = kw.get("attributes") or {}
        for v in self.values:
            # py2
            orig = v.attributes
            v.attributes = default_attributes.copy()
            v.attributes.update(orig)

        # emit warnings
        if not self.document:
            logger.warning("No document is given.")
        for key in kw:
            if key not in [
                "document",
                "columns",
                "parameters",
                "values",
                "reader_options",
                "attributes",
            ]:
                logger.warning('Unrecognized attribute "%s"', key)

    def get_column(self, name):
        # type: (str)->ColumnInfo
        """Return a column with specified name.

        Return `ColumnInfo` of a column with name :ar:`name`.

        Arguments
        ---------
        name
            The name of column to get.

        Returns
        -------
        ColumnInfo
            The column with name :ar:`name`.

        Raises
        ------
        KeyError
            If no column is found.
        """
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(name)

    def formatted_str(self):
        # type: ()->str
        """Return the formatted string.

        Returns
        -------
        str
            Dumped data.
        """
        results = ["[Document]"]
        for k, v in self.document.items():
            results.append(u"  {}: {}".format(k, v))  # py2
        return "\n".join(results)
