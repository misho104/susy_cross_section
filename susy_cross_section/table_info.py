"""Classes to describe a general-purpose table with annotations.

This module provides classes to handle CSV-like table data, which represents
functions over a parameter space. Data is a two-dimensional
:typ:`pandas.DataFrame` object. Some columns represent parameters and others do
values. Each row represents a single data point and corresponding value.

Two structural annotations and two semantic annotations are defined.
`TableInfo` and `ColumnInfo` are structural, which respectively annotate the
whole table and each columns. For semantics, `ParameterInfo` collects the
information of parameters, each of which is a column, and `ValueInfo` is for a
value. A value may be given by multiple columns if, for example, the value has
uncertainties or the value is given by the average of two columns.

================ =========================================================
class name       description
================ =========================================================
`Table`          contains data and `TableInfo`
`TableInfo`      has table properties, `ColumnInfo`, `ParameterInfo`, and
                 `ValueInfo`
`ColumnInfo`     has properties of each column
`ParameterInfo`  annotates a column as a parameter
`ValueInfo`      defines a value from possibly-multiple columns
================ =========================================================
"""

from __future__ import absolute_import, division, print_function  # py2

import json
import logging
import pathlib  # noqa: F401
import sys
from typing import (Any, List, Mapping, MutableMapping, Optional,  # noqa: F401
                    Sequence, Union)

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

JSONDecodeError = Exception if sys.version_info[0] < 3 else json.decoder.JSONDecodeError   # py2


class ColumnInfo(object):
    """Stores information of a column.

    Instead of the :typ:`int` identifier `!index`, we use `!name` as the
    principal identifier for readability. We also annotate a column by `!unit`,
    which is :typ:`str` that is passed to `Unit()`.

    Attributes
    ----------
    index : int
        The zero-based index of column.

        The columns of a table should have valid `!index`, i.e., no overlap, no
        gap, and starting from zero.
    name : str
        The human-readable and machine-readable name of the column.

        As it is used as the identifier, it should be unique in one table.
    unit : str
        The unit of column, or empty string if the column has no unit.

        The default value is an empty str ``''``, which means the column has no
        unit. Internally this is passed to `Unit()`.

    Note
    ----
    As for now, `!unit` is restricted as a str object, but in future a float
    should be allowed to describe "x1000" etc.
    """

    def __init__(self, index, name, unit=''):
        # type: (int, str, str)->None
        self.index = index       # type: int
        self.name = name         # type: str
        self.unit = unit or ''   # type: str

    @classmethod
    def from_json(cls, json_obj):
        # type: (Any)->ColumnInfo
        """Initialize an instance from valid json data.

        Parameters
        ----------
        json_obj: Any
            a valid json object.

        Raises
        ------
        ValueError
            If :ar:`json_obj` has invalid data.
        """
        try:
            obj = cls(index=json_obj['index'],
                      name=json_obj['name'],
                      unit=json_obj.get('unit', ''))
        except (TypeError, AttributeError) as e:
            logger.error('ColumnInfo.from_json: %s', e)
            raise ValueError('Invalid data passed to ColumnInfo.from_json: %s')
        except KeyError as e:
            logger.error('ColumnInfo.from_json: %s', e)
            raise ValueError('ColumnInfo data missing: %s', e)

        for k in json_obj.keys():
            if k not in ['index', 'name', 'unit']:
                logger.warn('Unknown data for ColumnInfo.from_json: %s', k)

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
        json_obj = {'index': self.index, 'name': self.name}  # type: MutableMapping[str, Union[str, int]]
        if self.unit:
            json_obj['unit'] = self.unit
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
            raise TypeError('ColumnInfo.index must be int: %s', self.index)
        if not self.index >= 0:
            raise ValueError('ColumnInfo.index must be non-negative: %s', self.index)
        if not isinstance(self.name, str):
            raise TypeError('Column %d: `name` must be string: %s', self.index, self.name)
        if not self.name:
            raise ValueError('Column %d: `name` missing', self.index)
        if not isinstance(self.unit, str):
            raise TypeError('Column %d: `unit` must be string: %s', self.index, self.unit)


class ParameterInfo(object):
    """Stores information of a parameter.

    A parameter set defines a data point for the functions described by the
    table. A parameter set has one or more parameters, each of which
    corresponds to a column of the table. The `!column` attribute has
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

    def __init__(self, column='', granularity=None):
        # type: (str, float)->None
        self.column = column                    # type: str
        self.granularity = granularity or None  # type: Optional[float]

    @classmethod
    def from_json(cls, json_obj):
        # type: (Any)->ParameterInfo
        """Initialize an instance from valid json data.

        Parameters
        ----------
        json_obj: Any
            a valid json object.

        Raises
        ------
        ValueError
            If :ar:`json_obj` has invalid data.
        """
        try:
            obj = cls(column=json_obj['column'],
                      granularity=json_obj.get('granularity'))
        except (TypeError, AttributeError) as e:
            logger.error('ParameterInfo.from_json: %s', e)
            raise ValueError('Invalid data passed to ParameterInfo.from_json: %s')
        except KeyError as e:
            logger.error('ParameterInfo.from_json: %s', e)
            raise ValueError('ColumnInfo data missing: %s', e)

        for k in json_obj.keys():
            if k not in ['column', 'granularity']:
                logger.warn('Unknown data for ParameterInfo.from_json: %s', k)

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
        json_obj = {'column': self.column}  # type: MutableMapping[str, Union[str, float]]
        if self.granularity:
            json_obj['unit'] = self.granularity
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
        if not isinstance(self.column, str):
            raise TypeError('ParameterInfo.column must be string: %s', self.column)
        if not self.column:
            raise ValueError('ParameterInfo.column is missing')
        if self.granularity is not None:
            try:
                if not float(self.granularity) > 0:
                    raise ValueError('ParameterInfo.granularity is not positive: %s', self.granularity)
            except TypeError:
                raise TypeError('ParameterInfo.granularity is not a number: %s', self.granularity)


class ValueInfo(object):
    """Stores information of value accompanied by uncertainties.

    A value is generally composed from several columns. In current
    implementation, the central value must be given by one column, whose name
    is specified by :attr:`column`. The positive- and negative-direction
    uncertainties are specified by `!unc_p` and `!unc_m`, respectively, which
    are :typ:`dict(str, str)`.

    Attributes
    ----------
    column: str
        Name of the column that stores this value.

        This must be match one of the :attr:`ColumnInfo.name` in the table.
    unc_p : dict of (str, str)
        The sources of "plus" uncertainties.

        Multiple uncertainty sources can be specified. Each key corresponds
        :attr:`ColumnInfo.name` of the source column, and each value denotes
        the "type" of the source. Currently, two types ``"relative"`` and
        ``"absolute"`` are implemented.

        The unit of the uncertainty column should be consistent with the unit
        of the value column.
    unc_m : dict of (str, str)
        The sources of "minus" uncertainties.

        Details are the same as `!unc_p`.
    """

    def __init__(self, column='', unc_p=None, unc_m=None, **kw):
        # type: (str, MutableMapping[str, str], MutableMapping[str, str], Any)->None
        self.column = column
        self.unc_p = unc_p or {}   # type: MutableMapping[str, str]
        self.unc_m = unc_m or {}   # type: MutableMapping[str, str]

    def validate(self):
        # type: ()->None
        """Validate the content.

        Perform the validation only within this class. This is intended to be
        called from outside of this class upon the user (of this class)'s
        request.
        """
        if not isinstance(self.column, str):
            raise TypeError('ValueInfo.column must be string: %s', self.column)
        if not self.column:
            raise ValueError('ValueInfo.column is missing')
        for title, unc in [('unc+', self.unc_p), ('unc-', self.unc_m)]:
            if not isinstance(unc, MutableMapping):
                raise TypeError('Value %s: %s must be dict', self.column, title)
            for k in unc.keys():
                if not isinstance(k, str):
                    raise TypeError('Value %s: %s has invalid column name: %s', self.column, title, k)

    @classmethod
    def from_json(cls, json_data):
        # type: (Any)->ValueInfo
        """Initialize an instance from valid json data.

        Parameters
        ----------
        json_data: Any
            a valid json object.

        Raises
        ------
        ValueError
            If :ar:`json_data` has invalid data.
        """
        if not isinstance(json_data, Mapping):
            raise TypeError('Entry of "values" must be a dict: %s', json_data)
        if 'column' not in json_data:
            raise KeyError('Entry of "values" must have a key "column": %s', json_data)

        obj = cls()
        obj.column = json_data['column']
        if ('unc' in json_data) and ('unc+' in json_data or 'unc-' in json_data):
            raise ValueError('Invalid uncertainties (asymmetric and symmetric): %s', obj.column)
        for attr_name, key_name in [('unc_p', 'unc+'), ('unc_m', 'unc-')]:
            u = json_data.get(key_name) or json_data.get('unc') or None
            if u is None:
                logger.warning('The uncertainty (%s) is missing in value "%s".', key_name, obj.column)
                continue
            if not isinstance(u, Sequence) or not all(isinstance(source, Mapping) for source in u):
                raise TypeError('Entry of "%s" in "%s" must be a list of dicts.', key_name, obj.column)
            try:
                setattr(obj, attr_name, {source['column']: source['type'] for source in u})
            except KeyError as e:
                raise ValueError('Entry of "%s" in "%s" has a missing key: %s', key_name, obj.column, *e.args)

        if not(obj.unc_p and obj.unc_m):
            logger.warning('Value %s lacks uncertainties.', obj.column)

        return obj

    def to_json(self):
        # type: ()->MutableMapping[str, Union[str, List[MutableMapping[str, str]]]]
        """Serialize the object to a json data.

        Returns
        -------
        dict(str, str or float)
            The json data describing the object.
        """
        return {
            'column': self.column,
            'unc+': [{'column': key, 'type': value} for key, value in self.unc_p.items()],
            'unc-': [{'column': key, 'type': value} for key, value in self.unc_m.items()],
        }


class TableInfo(object):
    """Stores annotations of a table.

    Attributes
    ----------
    document : dict of (Any, Any)
        Any information just for documentation, i.e., without physical
        meanings.
    columns : list of ColumnInfo
        The list of columns.
    """

    def __init__(self, document=None, columns=None, reader_options=None):
        # type: (MutableMapping[Any, Any], List[ColumnInfo], MutableMapping[str, Any])->None
        self.document = document or {}              # type: MutableMapping[Any, Any]
        self.columns = columns or []                # type: List[ColumnInfo]
        self.reader_options = reader_options or {}  # type: MutableMapping[str, Any]

    def validate(self):
        # type: ()->None
        """Validate the content."""
        if not isinstance(self.document, MutableMapping):
            raise TypeError('document must be a dict.')

        if not isinstance(self.columns, List):
            raise TypeError('columns must be list.')
        # validate columns (`index` matches actual index, names are unique)
        names_dict = {}  # type: MutableMapping[str, bool]
        for i, column in enumerate(self.columns):
            column.validate()
            if column.index != i:
                raise ValueError('Mismatched column index: %d has %d', i, column.index)
            if names_dict.get(column.name):
                raise ValueError('Duplicated column name: %s', column.name)
            names_dict[column.name] = True
        if not isinstance(self.reader_options, MutableMapping):
            raise TypeError('reader_options must be a dict.')
        if not all(k and isinstance(k, str) for k, v in self.reader_options.items()):
            raise TypeError('keys of reader_options must be str.')

    @classmethod
    def load(cls, source):
        # type: (Union[pathlib.Path, str])->TableInfo
        """Load and construct TableInfo from a json file."""
        obj = cls()
        with open(source.__str__()) as f:  # py2
            try:
                obj._load(**(json.load(f)))
            except JSONDecodeError:  # type: ignore
                logger.error('Invalid JSON file: %s', source)
                exit(1)
        return obj

    def _load(self, **kw):
        # type: (Any)->None
        """Construct TableInfo from a json data.

        Since no type-check is performed here, developers must be sure on
        validity of the information, e.g., by calling `validate` in this
        method.
        """
        self.document = kw.get('document') or {}
        self.columns = [ColumnInfo(index=i, name=c.get('name'), unit=c.get('unit'))
                        for i, c in enumerate(kw['columns'])
                        ] if 'columns' in kw else []
        self.reader_options = kw.get('reader_options') or {}

        try:
            self.validate()
        except ValueError as e:
            logger.error(*e.args)
            exit(1)
        except TypeError as e:
            logger.error(*e.args)
            exit(1)

        if not self.document:
            logger.warning('No document is given.')
        for key in kw:
            if key not in ['document', 'columns', 'reader_options']:
                logger.warning('Unrecognized attribute "%s"', key)

    def get_column(self, name):
        # type: (str)->ColumnInfo
        """Return a column with specified name.

        Search for a column with name `name` and returns it, or raise an error
        if not found. Note that this method is slow.
        """
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(name)

    def get_column_safe(self, name):
        # type: (str)->Union[ColumnInfo, None]
        """Get a column with specified name if exists."""
        try:
            return self.get_column(name)
        except KeyError:
            return None
