"""Classes for annotations to a table."""

from __future__ import absolute_import, division, print_function  # py2

import logging
import pathlib
import sys
from typing import (Any, List, Mapping, MutableMapping, Optional,  # noqa: F401
                    Sequence, SupportsFloat, Tuple, Union, cast)

import pandas

from susy_cross_section.table_info import ParameterInfo, TableInfo, ValueInfo
from susy_cross_section.utility import Unit

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class CrossSectionAttributes(object):
    """Stores physical attributes of a cross section table."""

    def __init__(self,
                 processes=None,
                 collider='',
                 ecm='',
                 order='',
                 pdf_id=None,
                 pdf_name=None):
        # type: (Union[str, List[str]], str, str, str, int, str)->None
        self.processes = [processes] if isinstance(processes, str) else processes or []   # type: List[str]
        self.collider = collider           # type: str
        self.ecm = ecm                     # type: str            # because it is always with units
        self.order = order                 # type: str
        self.pdf_id = pdf_id               # type: Optional[int]
        self.pdf_name = pdf_name           # type: Optional[str]  # either of these is necessary

    def validate(self):
        # type: ()->None
        """Validate the content.

        A strict type-check is also performed in order to validate
        (human-written) info files.
        """
        for attr, typ in [('processes', List),
                          ('collider', str),
                          ('ecm', str),
                          ('order', str),
                          ('pdf_id', int if self.pdf_id is not None else None),
                          ('pdf_name', str if self.pdf_name is not None else None)]:
            if typ and not isinstance(getattr(self, attr), typ):
                raise TypeError('attributes: %s must be %s', attr, typ)
        if not all(isinstance(s, str) for s in self.processes):
            raise TypeError('attributes: processes must be a list of string.')
        if not (self.pdf_id or self.pdf_name):
            raise ValueError('attributes: pdf_id or pdf_name is required.')
        if self.pdf_name is not None and not self.pdf_name:
            raise ValueError('attributes: pdf_name is empty.')


class CrossSectionInfo(TableInfo):
    """Stores annotations of a cross section table."""

    def __init__(self, attributes=None, parameters=None, values=None, **kw):
        # type: (CrossSectionAttributes, List[ParameterInfo], List[ValueInfo], Any)->None
        self.attributes = attributes or CrossSectionAttributes()   # type: CrossSectionAttributes
        self.parameters = parameters or []                         # type: List[ParameterInfo]
        self.values = values or []                                 # type: List[ValueInfo]
        super(CrossSectionInfo, self).__init__(**kw)  # py2

    @classmethod
    def load(cls, source):
        # type: (Union[pathlib.Path, str])->CrossSectionInfo
        """Load and construct CrossSectionInfo from a json file."""
        return cast(CrossSectionInfo, super(CrossSectionInfo, cls).load(source))  # py2

    def _load(self, **kw):    # noqa: C901
        # type: (Any)->None
        try:
            attributes, data = kw['attributes'], kw['data']
        except KeyError as e:
            logger.error('CrossSectionInfo lacks a key: %s', *e.args)
            exit(1)
        del kw['attributes']
        del kw['data']
        super(CrossSectionInfo, self)._load(**kw)  # py2
        if not isinstance(attributes, Mapping):
            logger.error('CrossSectionInfo.attributes must be a dict.')
            exit(1)
        self.attributes = CrossSectionAttributes(**attributes)

        # parse data
        try:
            parameters, values = data['parameters'], data['values']
        except TypeError:
            logger.error('data must be required and dict.')
            exit(1)
        except KeyError:
            logger.error('data must contain "parameters" and "values".')
            exit(1)
        for unused_key in [k for k in data.keys() if k not in ['parameters', 'values']]:
            logger.warning('Unrecognized attribute "%s" in data.', unused_key)

        if not (isinstance(parameters, Sequence) and isinstance(values, Sequence)):
            logger.error('data["values"] and data["parameters"] must be list of dicts.')
            exit(1)
        try:
            self.parameters = [ParameterInfo.from_json(p_json) for p_json in parameters]
            self.values = [ValueInfo.from_json(value_json) for value_json in values]
        except ValueError as e:
            logger.error(*e.args)
            exit(1)
        except TypeError as e:
            logger.error(*e.args)
            exit(1)

        self.validate()


class CrossSectionTable(object):
    """Data of a cross section with parameters, read from a table file."""

    def _reader_options(self):
        # type: ()->Mapping[str, Any]
        default = {
            'skiprows': [0],
            'names': [c.name for c in self.info.columns],
        }
        default.update(self.info.reader_options)
        return default

    def __init__(self, table_path, info_path=None):
        # type: (Union[pathlib.Path, str], Union[pathlib.Path, str])->None

        self.table_path = pathlib.Path(table_path)         # type: pathlib.Path
        self.info_path = pathlib.Path(
            info_path if info_path
            else self.table_path.with_suffix('.info'))     # type: pathlib.Path
        self.info = CrossSectionInfo.load(self.info_path)  # type: CrossSectionInfo
        try:
            self.raw_data = pandas.read_csv(self.table_path, **self._reader_options())
        except ValueError as e:
            logger.error('Data parse failed: %s', *e.args)
            exit(1)
        self._parse_data()
        self.validate()

    @staticmethod
    def _validate_uncertainty_info(uncertainty_info):
        # type: (Mapping[str, str])->None
        for _name, typ in uncertainty_info.items():
            if typ not in ['relative', 'absolute']:
                raise ValueError('Invalid type of uncertainty: %s', typ)

    def _uncertainty_factors(self, value_unit, uncertainty_info):
        # type: (Unit, Mapping[str, str])->Mapping[str, float]
        factors = {}
        for source_name, source_type in uncertainty_info.items():
            unc_unit = Unit(self.info.get_column(source_name).unit)
            if source_type == 'relative':
                unc_unit *= value_unit
            # unc / unc_unit == "number in the table"
        # we want to get "unc / value_unit" = "number in the table"  * unc_unit / value_unit
            factors[source_name] = float(unc_unit / value_unit)
        return factors

    @staticmethod
    def _combine_uncertainties(row, value_name, uncertainty_info, uncertainty_factors):
        # type: (Any, str, Mapping[str, str], Mapping[str, float])->float
        uncertainties = []
        for source_name, source_type in uncertainty_info.items():
            uncertainties.append(row[source_name] * uncertainty_factors[source_name] * (
                row[value_name] if source_type == 'relative' else 1
            ))
        return sum(x**2 for x in uncertainties) ** 0.5

    def _parse_data(self):
        # type: ()->None
        self.data = {}   # type: MutableMapping[str, pandas.core.frame.DataFrame]
        self.units = {}  # type: MutableMapping[str, str]

        for value_info in self.info.values:

            name = value_info.column
            value_unit = self.info.get_column(name).unit
            parameters = self.info.parameters
            data = self.raw_data.copy()

            # set index with quantizing the values with granularity to avoid float precision problems
            for p in parameters:
                data[p.column] = (data[p.column] / p.granularity).apply(round) * p.granularity
            data.set_index([p.column for p in parameters], inplace=True)

            self._validate_uncertainty_info(value_info.unc_p)
            self._validate_uncertainty_info(value_info.unc_m)
            unc_p_factors = self._uncertainty_factors(Unit(value_unit), value_info.unc_p)
            unc_m_factors = self._uncertainty_factors(Unit(value_unit), value_info.unc_m)

            def unc_p(row):
                # type: (Any)->float
                return self._combine_uncertainties(row, name, value_info.unc_p, unc_p_factors)

            def unc_m(row):
                # type: (Any)->float
                return -self._combine_uncertainties(row, name, value_info.unc_m, unc_m_factors)

            self.data[name] = pandas.DataFrame()
            self.data[name]['value'] = data[name]
            self.data[name]['unc+'] = data.apply(unc_p, axis=1)
            self.data[name]['unc-'] = data.apply(unc_m, axis=1)
            self.units[name] = value_unit

    def validate(self):
        # type: ()->None
        """Validate the data grid."""
        failed = False
        for key, data in self.data.items():
            duplication = data.index[data.index.duplicated()]
            for d in duplication:
                failed = True
                logger.error('Found duplicated entries: %s, %s', key, d)
                if len(duplication) > 5:
                    logger.error('Maybe parameter granularity is set too large?')
        if failed:
            exit(1)

    def __getitem__(self, key):
        # type: (str)->pandas.core.frame.DataFrame
        """Return the cross-section table."""
        return self.data[key]

    def dump(self):
        # type: ()->None
        """Print out data table."""
        for key, data_table in self.data.items():
            print('# {name} [{unit}] with absolute uncertainties'.format(name=key, unit=self.units[key]))
            print(data_table)

    def str_information(self):
        # type: ()->str
        """Return the information in a formatted string display."""
        rows = []  # type: List[str]

        # information
        rows.append('[Document]')
        for k, v in self.info.document.items():
            rows.append('  {}: {}'.format(k, v))

        attr = self.info.attributes
        rows.append('[Attributes]')
        rows.append('  collider : {}-collider with ECM={}'.format(attr.collider, attr.ecm))
        rows.append('  order: {} with PDF={}'.format(attr.order, attr.pdf_name or attr.pdf_id))
        rows.append('[Processes]')
        for i in attr.processes:
            rows.append('  {}'.format(i))

        return '\n'.join(rows)

    def param_information(self):
        # type: ()->Sequence[Mapping[str,str]]
        """Return the information of parameters."""
        result = []   # type: List[MutableMapping[str, Any]]
        for param in self.info.parameters:
            name = param.column
            column = self.info.get_column(name)
            result.append({'name': name, 'unit': column.unit, 'granularity': param.granularity})
        return result

    def value_information(self):
        # type: ()->Sequence[Mapping[str,str]]
        """Return the information of parameters."""
        result = []   # type: List[MutableMapping[str, str]]
        for value in self.info.values:
            name = value.column
            column = self.info.get_column(name)
            result.append({'name': name, 'unit': column.unit})
        return result
