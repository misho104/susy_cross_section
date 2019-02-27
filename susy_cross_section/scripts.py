"""Scripts for user's ease of handling the data.

The main command ``susy-xs`` may invoke the follwoing subcommands:

get:
    Interpolate cross-section grid table and return the cross section.

show:
    Display cross-section grid table with information.

For details, see the manual or try to execute with ``--help`` option.
"""

from __future__ import absolute_import, division, print_function  # py2

import logging
import sys
from typing import Any  # noqa: F401

import click
import coloredlogs

import susy_cross_section.utility as Util
from susy_cross_section.interp.axes_wrapper import AxesWrapper
from susy_cross_section.interp.interpolator import (
    AbstractInterpolator,
    Scipy1dInterpolator,
    ScipyGridInterpolator,
)
from susy_cross_section.table import File

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


def _configure_logger():
    # type: ()->None
    """Configure logger so that proper logs are shown on console."""
    coloredlogs.install(
        level=logging.INFO, logger=logging.getLogger(), fmt="%(levelname)8s %(message)s"
    )


def _display_usage_for_file(context, data_file, **kw):
    # type: (click.Context, File, Any)->None
    """Display usage of the specified table."""
    arg_zero = context.info_name  # program name
    arg_table = kw["table"]
    # list of param_name and unit

    usage_line = "Usage: {a0} [OPTIONS] {table} {args}".format(
        a0=arg_zero,
        table=arg_table,
        args=" ".join(p.column.upper() for p in data_file.info.parameters),
    )
    params_lines = [
        "    {title:11} {name}   [unit: {unit}]".format(
            title="Parameters:" if i == 0 else "",
            name=p.column.upper(),
            unit=data_file.info.get_column(p.column).unit,
        )
        for i, p in enumerate(data_file.info.parameters)
    ]
    values_lines = [
        "    {title:17} --name={name}   [unit: {unit}]  {default}".format(
            title="Table-specific options:" if i == 0 else "",
            name=name,
            unit=table.unit,
            default="(default)" if name == _DEFAULT_VALUE_NAME else "",
        )
        for i, (name, table) in enumerate(data_file.tables.items())
    ]

    click.echo(usage_line)
    click.echo()
    for line in params_lines:
        click.echo(line)
    click.echo()
    for line in values_lines:
        click.echo(line)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name=__packagename__)
def main():
    # type: ()->None
    """Handle cross-section grid tables with uncertainties."""
    pass


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("table", required=True, type=click.Path(exists=False))
@click.argument("args", type=float, nargs=-1)
@click.option("--name", default="xsec", help="name of a table")
@click.option("-0", "simplest", is_flag=True, help="show in simplest format")
@click.option("-1", "simple", is_flag=True, help="show in simple format")
@click.option("-2", "relative", is_flag=True, help="show relative uncertainties")
@click.option("--unit/--no-unit", help="display unit", default=True, show_default=True)
# @click.option('--config', type=click.Path(exists=True, dir_okay=False),
#              help='path of config json file for extra name dictionary')
@click.option(
    "--info",
    type=click.Path(exists=True, dir_okay=False),
    help="path of table-info file if non-standard file name",
)
@click.pass_context
def get(context, **kw):
    # type: (Any, Any)->None
    """Get cross-section value using interpolation."""
    _configure_logger()
    # handle arguments
    args = kw["args"] or []
    value_name = kw["name"] or _DEFAULT_VALUE_NAME
    try:
        table_path, info_path = Util.get_paths(kw["table"], kw["info"])
        data_file = File(table_path, info_path)
    except (FileNotFoundError, RuntimeError, ValueError, TypeError) as e:
        click.echo(repr(e))
        exit(1)

    try:
        table = data_file.tables[value_name]
    except KeyError as e:
        logger.critical("Data file does not contain specified table.")
        click.echo(repr(e))
        exit(1)

    # without arguments or with invalid number of arguments, show the table information.
    if len(args) != len(data_file.info.parameters):
        _display_usage_for_file(context, data_file, **kw)
        exit(1)

    # data evaluation
    if len(args) == 1:
        interp = Scipy1dInterpolator(
            axes="loglog", kind="linear"
        )  # type: AbstractInterpolator
    else:
        wrapper = AxesWrapper(["log" for _ in args], "log")
        interp = ScipyGridInterpolator(axes_wrapper=wrapper, kind="linear")
    cent, u_p, u_m = interp.interpolate(table).tuple_at(*kw["args"])

    # display
    if kw["simplest"]:
        click.echo(cent)
    elif kw["simple"]:
        click.echo("{} +{} -{}".format(cent, u_p, abs(u_m)))
    else:
        relative = bool(kw.get("relative", False))
        unit = table.unit if kw["unit"] else None
        click.echo(Util.value_format(cent, u_p, u_m, unit, relative))
    exit(0)


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("table", required=True, type=click.Path(exists=False))
# @click.option('--config', type=click.Path(exists=True, dir_okay=False),
#              help='path of config json file for extra name dictionary')
@click.option(
    "--info",
    type=click.Path(exists=True, dir_okay=False),
    help="path of table-info file if non-standard file name",
)
def show(**kw):
    # type: (Any)->None
    """Show the cross-section table with combined uncertainties."""
    _configure_logger()
    # handle arguments
    try:
        table_path, info_path = Util.get_paths(kw["table"], kw["info"])
    except (FileNotFoundError, RuntimeError) as e:
        click.echo(e.__repr__())  # py2
        exit(1)

    try:
        data_file = File(table_path, info_path)
    except (ValueError, TypeError) as e:
        click.echo(e.__repr__())  # py2
        exit(1)

    click.echo(data_file.dump())
    exit(0)
