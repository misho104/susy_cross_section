"""Scripts for user's ease of handling the data."""

from __future__ import absolute_import, division, print_function  # py2

import logging
import os
import pathlib
import sys
from typing import Any  # noqa: F401

import click

import susy_cross_section.config
import susy_cross_section.utility
from susy_cross_section.cross_section_table import CrossSectionTable
from susy_cross_section.interpolator import Scipy1dInterpolator

__author__ = 'Sho Iwamoto'
__copyright__ = 'Copyright (C) 2018-2019 Sho Iwamoto / Misho'
__license__ = 'MIT'
__scriptname__ = 'XS interpolator'
__version__ = '0.1.0'

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


@click.command(help='Interpolate cross-section data using the standard scipy interpolator (with log-log axes).',
               context_settings={'help_option_names': ['-h', '--help']})
@click.argument('table', required=True, type=click.Path(exists=False))
@click.argument('args', type=float, required=True, nargs=-1)
@click.option('--name', default='xsec', help='name of a table')
@click.option('-0', 'simplest', is_flag=True, help='show in simplest format')
@click.option('-1', 'simple', is_flag=True, help='show in simple format')
@click.option('--unit/--no-unit', help='display unit', default=True, show_default=True)
# @click.option('--config', type=click.Path(exists=True, dir_okay=False),
#              help='path of config json file for extra name dictionary')
@click.option('--info', type=click.Path(exists=True, dir_okay=False),
              help='path of table-info file if non-standard file name')
@click.version_option(__version__, '-V', '--version', prog_name=__scriptname__)
def command_get(**kw):
    # type: (Any)->None
    """Script for cross-section interpolation."""
    # handle arguments
    info_path = None
    if os.path.exists(kw['table']):
        table_path = pathlib.Path(kw['table'])
    elif kw['table'] in susy_cross_section.config.table_names:
        pwd = pathlib.Path(__file__).parent
        t = susy_cross_section.config.table_names[kw['table']]
        if isinstance(t, str):
            table_path = pwd / t
        else:
            table_path, info_path = pwd / t[0], pwd / t[1]
    else:
        click.echo('No table found: {}'.format(kw['table']))
        exit(1)
    if kw['info']:
        info_path = kw['info']

    # data evaluation
    table = CrossSectionTable(table_path, info_path)
    name = kw.get('name') or 'xsec'
    unit = table.units[name] if kw['unit'] else None
    interpolator = Scipy1dInterpolator(axes='loglog', kind='linear')
    central, unc_p, unc_m = interpolator.interpolate(table, name=name).tuple_at(*kw['args'])

    # display
    if kw['simplest']:
        click.echo(central)
    elif kw['simple']:
        click.echo('{} +{} -{}'.format(central, unc_p, abs(unc_m)))
    else:
        click.echo(susy_cross_section.utility.value_format(central, unc_p, unc_m, unit))
    exit(0)


@click.command(help='Show the interpreted cross-section table with positive and negative uncertainties.',
               context_settings={'help_option_names': ['-h', '--help']})
@click.argument('table', required=True, type=click.Path(exists=False))
# @click.option('--config', type=click.Path(exists=True, dir_okay=False),
#              help='path of config json file for extra name dictionary')
@click.option('--info', type=click.Path(exists=True, dir_okay=False),
              help='path of table-info file if non-standard file name')
@click.version_option(__version__, '-V', '--version', prog_name=__scriptname__)
def command_show(**kw):
    # type: (Any)->None
    """Script for cross-section interpolation."""
    # handle arguments
    info_path = None
    if os.path.exists(kw['table']):
        table_path = pathlib.Path(kw['table'])
    elif kw['table'] in susy_cross_section.config.table_names:
        pwd = pathlib.Path(__file__).parent
        t = susy_cross_section.config.table_names[kw['table']]
        if isinstance(t, str):
            table_path = pwd / t
        else:
            table_path, info_path = pwd / t[0], pwd / t[1]
    else:
        click.echo('No table found: {}'.format(kw['table']))
        exit(1)
    if kw['info']:
        info_path = kw['info']

    # data evaluation
    table = CrossSectionTable(table_path, info_path)
    click.echo('=' * 80)
    for key in table.data:
        unit_str = '[{}]'.format(table.units[key]) if table.units[key] else ''
        click.echo('{} {}'.format(key, unit_str))
        click.echo('-' * 80)
        click.echo(table.data[key])
        click.echo('=' * 80)
    exit(0)


if __name__ == '__main__':
    command_get()
