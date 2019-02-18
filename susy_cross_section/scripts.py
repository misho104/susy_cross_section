"""Scripts for user's ease of handling the data.

Two command-line scripts are provided:

susy-xs-get:
    Interpolate cross-section grid table and return the cross section.
    This script corresponds to `!scripts.command_get` method.

susy-xs-show:
    Display cross-section grid table with information.
    This script corresponds to `!scripts.command_show` method.

For details, see the manual or try to execute with ``--help`` option.
"""

from __future__ import absolute_import, division, print_function  # py2

import logging
import sys
from typing import Any  # noqa: F401

import click

import susy_cross_section.utility as Util
from susy_cross_section.interp.axes_wrapper import AxesWrapper
from susy_cross_section.interp.interpolator import (
    AbstractInterpolator,
    Scipy1dInterpolator,
    ScipyGridInterpolator,
)
from susy_cross_section.table import Table

__author__ = "Sho Iwamoto"
__copyright__ = "Copyright (C) 2018-2019 Sho Iwamoto / Misho"
__license__ = "MIT"
__packagename__ = "susy_cross_section"
__version__ = "0.0.4"

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

_DEFAULT_VALUE_NAME = "xsec"


def _display_usage_for_table(context, table_obj, **kw):
    # type: (click.Context, Table, Any)->None
    """Display usage of the specified table."""
    arg_zero = context.info_name  # program name
    arg_table = kw["table"]
    # list of param_name and unit

    usage_line = "Usage: {a0} [OPTIONS] {table} {args}".format(
        a0=arg_zero,
        table=arg_table,
        args=" ".join(p.column.upper() for p in table_obj.info.parameters),
    )
    params_lines = ["    {title:11} {name}   [unit: {unit}]".format(
        title="Parameters:" if i == 0 else "",
        name=p.column.upper(),
        unit=table_obj.info.get_column(p.column).unit,
    ) for i, p in enumerate(table_obj.info.parameters)]
    values_lines = ["    {title:17} --name={name}   [unit: {unit}]  {default}".format(
        title="Table-specific options:" if i == 0 else "",
        name=name,
        unit=unit,
        default="(default)" if name == _DEFAULT_VALUE_NAME else "",
    ) for i, (name, unit) in enumerate(table_obj.units.items())]

    click.echo(usage_line)
    click.echo()
    for line in params_lines:
        click.echo(line)
    click.echo()
    for line in values_lines:
        click.echo(line)


@click.command(
    help="Interpolate cross-section data using the standard scipy interpolator (with log-log axes).",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.argument("table", required=True, type=click.Path(exists=False))
@click.argument("args", type=float, nargs=-1)
@click.option("--name", default="xsec", help="name of a table")
@click.option("-0", "simplest", is_flag=True, help="show in simplest format")
@click.option("-1", "simple", is_flag=True, help="show in simple format")
@click.option("--unit/--no-unit", help="display unit", default=True, show_default=True)
# @click.option('--config', type=click.Path(exists=True, dir_okay=False),
#              help='path of config json file for extra name dictionary')
@click.option("--info", type=click.Path(exists=True, dir_okay=False),
              help="path of table-info file if non-standard file name")
@click.version_option(__version__, "-V", "--version", prog_name=__packagename__ + " interpolator")
@click.pass_context
def command_get(context, **kw):
    # type: (Any, Any)->None
    """Script for cross-section interpolation."""
    # handle arguments
    args = kw["args"] or []
    value_name = kw["name"] or _DEFAULT_VALUE_NAME
    try:
        table_path, info_path = Util.get_paths(kw["table"], kw["info"])
    except (FileNotFoundError, RuntimeError) as e:
        click.echo(e.__str__())  # py2
        exit(1)

    try:
        table = Table(table_path, info_path)
    except (ValueError, TypeError) as e:
        click.echo(e.__str__())  # py2
        exit(1)

    # without arguments or with invalid number of arguments, show the table information.
    if len(args) != len(table.info.parameters):
        _display_usage_for_table(context, table, **kw)
        exit(1)

    # data evaluation
    if len(args) == 1:
        interp = Scipy1dInterpolator(axes="loglog", kind="linear")  # type: AbstractInterpolator
    else:
        wrapper = AxesWrapper(["log" for _ in args], "log")
        interp = ScipyGridInterpolator(axes_wrapper=wrapper, kind="linear")
    central, unc_p, unc_m = interp.interpolate(table, name=value_name).tuple_at(*kw["args"])

    # display
    if kw["simplest"]:
        click.echo(central)
    elif kw["simple"]:
        click.echo("{} +{} -{}".format(central, unc_p, abs(unc_m)))
    else:
        click.echo(Util.value_format(central, unc_p, unc_m,
                                     unit=table.units[value_name] if kw["unit"] else None))
    exit(0)


@click.command(
    help="Show the interpreted cross-section table with positive and negative uncertainties.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.argument("table", required=True, type=click.Path(exists=False))
# @click.option('--config', type=click.Path(exists=True, dir_okay=False),
#              help='path of config json file for extra name dictionary')
@click.option("--info", type=click.Path(exists=True, dir_okay=False),
              help="path of table-info file if non-standard file name")
@click.version_option(__version__, "-V", "--version", prog_name=__packagename__ + " table viewer")
def command_show(**kw):
    # type: (Any)->None
    """Script for cross-section interpolation."""
    # handle arguments
    try:
        table_path, info_path = Util.get_paths(kw["table"], kw["info"])
    except (FileNotFoundError, RuntimeError) as e:
        click.echo(e.__str__())  # py2
        exit(1)

    try:
        table = Table(table_path, info_path)
    except (ValueError, TypeError) as e:
        click.echo(e.__str__())  # py2
        exit(1)

    click.echo(table.dump())
    click.echo(table.info.dump())
    exit(0)
