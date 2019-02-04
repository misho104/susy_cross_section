"""Classes for annotations to a table."""

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

    A column is defined by `index`, but is referreed to by `name` for
    flexibility and readability. Also in physics context a column is
    accompanied by a unit.

    note: In this version `unit` is just a `str` and thus just for
    annotation, but in future numeric units such as 1000 to describe
    "x1000" could be implemented.

    Attributes
    ----------
    index : int
        The index (zero-based indexing) of column. Non-negative.
    name : str
        The name of column, used as an identifier and thus should be unique in one table.
    unit : str
        The unit of column. If without unit, it must be an empty string.
    """

    def __init__(self, index, name, unit=''):
        # type: (int, str, str)->None
        self.index = index       # type: int
        self.name = name         # type: str
        self.unit = unit or ''   # type: str

    def validate(self):
        # type: ()->None
        """Validate the content.

        Perform the validation only within ColumnInfo. This is intended
        to be called from outside of this class upon the user (of this
        class)'s request.
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
    """Stores information of parameter.

    Parameter is a number characterized by its `column` name and users
    will interpolate the data according to them. For grid-based
    interpolation, another property `granularity` should be provided,

    Attributes
    ----------
    column: str
        Name of the column that stores this parameter.
    granularity : int or float
        granularity of the parameter when interpreted as a list of
        grid-points. For a parameter list `v`, the integers
        round(v[i] / granularity) should specify one grid-point.

        For example, for a parameter grid [10, 20, 30, 50, 70, 200],
        it will be 10 in principle, but 5, 2, 1, or 0.1 are possible.
        For [33.3, 50, 70], it should be 0.1 (or 0.05, etc.) to track
        the first decimal point of 33.3.
    """

    def __init__(self, column='', granularity=None):
        # type: (str, float)->None
        self.column = column                    # type: str
        self.granularity = granularity or None  # type: Optional[float]

    def validate(self):
        # type: ()->None
        """Validate the content.

        Perform the validation only within this class. This is intended
        to be called from outside of this class upon the user (of this
        class)'s request.
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

    @classmethod
    def from_json(cls, json_data):
        # type: (Any)->ParameterInfo
        """Construct an object from json-based data."""
        if not isinstance(json_data, Mapping):
            raise TypeError('Entry of "values" must be a dict: %s', json_data)
        column = json_data.get('column')
        granularity = json_data.get('granularity', None)
        if not column:
            raise ValueError('Entry of "values" must have a key "column": %s', json_data)
        return cls(column=column, granularity=granularity)

    def to_json(self):
        # type: ()->MutableMapping[str, Union[str, float]]
        """Dump json-based data from an object."""
        json_data = {'column': self.column}   # type: MutableMapping[str, Union[str, float]]
        if self.granularity:
            json_data['granularity'] = self.granularity
        return json_data


class ValueInfo(object):
    """Stores information of value accompanied by uncertainties.

    This includes `column` as the name of column the value is stored,
    and plus- and minus-directed uncertainty sources of the value.
    An uncertainty source is characterized by a column-name and a type,
    which currently includes "relative" or "absolute".

    Attributes
    ----------
    column: str
        Name of the column that stores this value.
    unc_p : dict of (str, str)
        The sources of "plus" uncertainties, where each key describe
        `name` of another `ColumnInfo` and each value denotes the
        "type" of the source.
    unc_m : dict of (str, str)
        The sources of "minus" uncertainties.
    """

    def __init__(self, column='', unc_p=None, unc_m=None, **kw):
        # type: (str, MutableMapping[str, str], MutableMapping[str, str], Any)->None
        self.column = column
        self.unc_p = unc_p or {}   # type: MutableMapping[str, str]
        self.unc_m = unc_m or {}   # type: MutableMapping[str, str]

    def validate(self):
        # type: ()->None
        """Validate the content.

        Perform the validation only within this class. This is intended
        to be called from outside of this class upon the user (of this
        class)'s request.
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
        """Construct an object from json-based data."""
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
        """Dump json-based data from an object."""
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
        Any information just for documentation, i.e., without physical meanings.
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

        Since no type-check is performed here, developers must be sure
        on validity of the information, e.g., by calling `validate` in
        this method.
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

        Search for a column with name `name` and returns it, or raise an
        error if not found. Note that this method is slow.
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
