#!env python3

import json
import logging
import pathlib
import re
from typing import cast, Sequence, Any, List, Tuple, Union, Callable  # noqa: F401

import click
import numpy as np
import scipy.interpolate

__author__ = 'Sho Iwamoto'
__copyright__ = 'Copyright (C) 2018 Sho Iwamoto / Misho'
__license__ = 'MIT'
__scriptname__ = 'XS interpolator'
__version__ = '0.1.0'

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


UncertaintyType = Union[float, List[float]]
ResultType = Union[
    Tuple[float, float, UncertaintyType],                    # mass, xs, unc
    Tuple[float, float, UncertaintyType, UncertaintyType]    # mass, xs, +unc, -unc
]

NAMES_DICTIONARY = 'names.json'


def is_number(obj: Any)->bool:
    return isinstance(obj, int) or isinstance(obj, float)


def format_str(obj: Any)->str:
    if isinstance(obj, float):
        result = '{:#.7}'.format(obj)
        if result.endswith('.'):
            result = result[:-1]
        return result
    elif isinstance(obj, list):
        return '[' + ', '.join(format_str(i) for i in obj) + ']'
    else:
        return str(obj)


def assert_same_type(data: List[ResultType])->bool:
    head = data[0]
    if not all(len(n) == len(head) for n in data):
        return False
    for i in range(2, len(head)):
        if is_number(head[i]):
            column_type = None
        elif isinstance(head[i], list) and all(is_number(k) for k in head[i]):
            column_type = len(head[i])
        else:
            return False
        for n in data:
            if column_type is None and is_number(n[i]):
                pass
            elif isinstance(n[i], list) and all(is_number(k) for k in n[i]) and len(n[i]) == column_type:
                pass
            else:
                return False
    return True


def log_interp1d(x, y, kind='linear'):
    # type: (Sequence[float], Sequence[float], str)->Callable[[float], float]
    lx = np.log10(x)
    ly = np.log10(y)
    lin_interp = scipy.interpolate.interp1d(lx, ly, kind=kind)

    def log_interp(z):  # type: (float)->float
        return cast(float, np.power(10.0, lin_interp(np.log10(z))))
    return log_interp


def interpolate(data: List[ResultType], mass: float)->Tuple[float, float, float]:
    def squeeze(obj: Union[int, float, List[Union[int, float]]])->float:
        return abs(obj) if is_number(obj) else sum(i**2 for i in obj) ** 0.5  # type: ignore

    if not assert_same_type(data):
        logger.warning('The data is malformed.')

    masses = [p[0] for p in data]
    if mass < min(masses) or max(masses) < mass:
        logger.error('Extrapolation is not allowed; {} < mass < {}.'.format(min(masses), max(masses)))
        exit(1)

    xs_plus, xs_minus = [], []   # type: List[float], List[float]
    for n in data:
        p_sum = squeeze(n[2]) if len(n) > 2 else 0
        m_sum = squeeze(n[3]) if len(n) > 3 else p_sum
        xs_plus.append(n[1] + p_sum)
        xs_minus.append(n[1] - m_sum)
    xs_result = log_interp1d(masses, [p[1] for p in data])(mass)
    unc_p = log_interp1d(masses, xs_plus)(mass) - xs_result
    unc_m = log_interp1d(masses, xs_minus)(mass) - xs_result
    return xs_result, unc_p, unc_m


def interpolate_original_format(data: List[ResultType], mass: float)->str:
    if isinstance(data, str):
        with open(data) as f:
            data = json.load(f)

    if not assert_same_type(data):
        logger.error('The data is malformed and not suitable for original-format output.')
        exit(1)

    masses = [p[0] for p in data]
    if mass < min(masses) or max(masses) < mass:
        logger.error('Extrapolation is not allowed; {} < mass < {}.'.format(min(masses), max(masses)))
        exit(1)

    xs_result = log_interp1d(masses, [p[1] for p in data])(mass)

    unc_p, unc_m = 0, 0  # type: Union[float, List[float]], Union[float, List[float]]
    if is_number(data[0][2]):
        unc_p = log_interp1d(masses, [p[1] + p[2] for p in data])(mass) - xs_result
    else:
        unc_p = [log_interp1d(masses, [p[1] + p[2][i] for p in data])(mass) - xs_result
                 for i in range(len(data[0][2]))]
    if len(data[0]) >= 4:
        if is_number(data[0][3]):
            unc_m = log_interp1d(masses, [p[1] - abs(p[3]) for p in data])(mass) - xs_result
        else:
            unc_m = [log_interp1d(masses, [p[1] - abs(p[3][i]) for p in data])(mass) - xs_result
                     for i in range(len(data[0][2]))]
        return format_str([xs_result, unc_p, unc_m])
    else:
        return format_str([xs_result, unc_p])


def parse_filename(name: str)->str:
    # direct specification
    if pathlib.Path(name).is_file():
        return name

    # ECM.process, where process is in dictionary
    cwd = pathlib.Path(__file__).resolve().parent
    try:
        with open(cwd / NAMES_DICTIONARY) as f:
            filename_dictionary = json.load(f)
    except FileNotFoundError:
        logger.error(f'NAMES_DICTIONARY {NAMES_DICTIONARY} not found. Specify data file directly.')
        exit(1)

    m = re.match(r'(\d+)\.(.*)', name)
    if m and m.group(2) in filename_dictionary:
        path = cwd / f'{m.group(1)}TeV/{filename_dictionary[m.group(2)]}'
        if not path.is_file:
            logger.error(f'{path} not found.')
        return str(path)

    logger.error(f'Cannot recognize {name}, which should be a jsonfile, or ECM.process with `processes` being:\n\t' +
                 ',\t'.join(filename_dictionary.keys()))
    exit(1)


def get(input: str, mass: float)->Tuple[float, float, float]:
    filename = parse_filename(input)
    try:
        with open(filename) as f:
            data = json.load(f)
    except json.decoder.JSONDecodeError:
        logger.error(f'Data in {filename} are malformed.')
        exit(1)
    return interpolate(data, mass)


@click.command(help='Interpolate cross-section data',
               context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('input',  required=True)
@click.argument('mass', type=float, required=True)
@click.option('--format', type=click.Choice(['short', 'original']), default='short',
              help='output format', show_default=True)
@click.version_option(__version__, '-V', '--version', prog_name=__scriptname__)
def command_get(input: str, mass: float, format: str)->None:
    if format == 'original':
        with open(parse_filename(input)) as f:
            data = json.load(f)
        result_str = interpolate_original_format(data, mass)
        print(result_str)
    else:
        central, plus, minus = get(input, mass)
        print('[{}, +{}, {}]'.format(format_str(central), format_str(plus), format_str(minus)))
    exit(0)


if __name__ == '__main__':
    command_get()
