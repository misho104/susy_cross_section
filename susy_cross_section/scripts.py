"""Scripts for user's ease of handling the data.

For details, see the manual or try to execute with ``--help`` option.
"""

from __future__ import absolute_import, division, print_function  # py2

import logging
from typing import Any, List, MutableMapping, Optional, Tuple  # noqa: F401

import click
import colorama
import coloredlogs

import susy_cross_section.config as config
import susy_cross_section.utility as utility
from susy_cross_section.interp.axes_wrapper import AxesWrapper
from susy_cross_section.interp.interpolator import (
    AbstractInterpolator,
    Scipy1dInterpolator,
    ScipyGridInterpolator,
)
from susy_cross_section.table import File

__author__ = "Sho Iwamoto"
__copyright__ = "Copyright (C) 2018-2022 Sho Iwamoto / Misho"
__license__ = "MIT"
__packagename__ = "susy_cross_section"
__version__ = "0.2.3"


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
        table_path, info_path = utility.get_paths(kw["table"], kw["info"])
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
            axes="loglog", kind="spline"
        )  # type: AbstractInterpolator
    else:
        wrapper = AxesWrapper(["log" for _ in args], "log")
        kind = "spline33" if len(args) == 2 else "linear"
        interp = ScipyGridInterpolator(axes_wrapper=wrapper, kind=kind)
    cent, u_p, u_m = interp.interpolate(table).tuple_at(*kw["args"])

    # display
    if kw["simplest"]:
        click.echo(cent)
    elif kw["simple"]:
        click.echo("{} +{} -{}".format(cent, u_p, abs(u_m)))
    else:
        relative = bool(kw.get("relative", False))
        unit = table.unit if kw["unit"] else None
        click.echo(utility.value_format(cent, u_p, u_m, unit, relative))
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
        table_path, info_path = utility.get_paths(kw["table"], kw["info"])
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


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("table", required=True, type=click.Path(exists=False))
@click.option("--name", default="xsec", help="name of a table")
@click.option("--unit/--no-unit", help="with unit", default=True, show_default=True)
@click.option("--unc/--no-unc", help="uncertainty", default=True, show_default=True)
@click.option(
    "--format",
    type=click.Choice(["TSV", "CSV", "Math"], case_sensitive=False),
    default="TSV",
    show_default=True,
)
@click.option(
    "--info",
    type=click.Path(exists=True, dir_okay=False),
    help="path of table-info file if non-standard file name",
)
@click.pass_context
def export(context, **kw):
    # type: (Any, Any)->None
    """Export cross-section table."""
    _configure_logger()
    # handle arguments
    value_name = kw["name"] or _DEFAULT_VALUE_NAME
    try:
        table_path, info_path = utility.get_paths(kw["table"], kw["info"])
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

    header = table.header()
    records = table.to_records()
    n_columns = len(header)

    units = ["" for i in header]
    if kw["unit"]:
        try:
            units = [" " + u for u in table.units()]
        except RuntimeError:
            logger.warning("Unit information not available for specified table.")

    if kw["format"] == "TSV" or kw["format"] == "CSV":
        sep = "\t" if kw["format"] == "TSV" else ","
        click.echo(sep.join(header))
        for i_record in range(len(records)):  # As mypy.records does not have __iter__
            record = records[i_record]
            line = []  # type: List[str]
            for i, v in enumerate(record):
                if i < n_columns - 2:
                    line.append(str(v) + units[i])  # key & value
                elif kw["unc"]:
                    line.append(f"{v:.5g}{units[-1]}")  # unc
            click.echo(sep.join(line))
    elif kw["format"] == "Math":  # Mathematica

        def concat(c):  # type: (List[str])->str
            return "  {" + ", ".join(c) + "}"

        lines = [concat([f'"{s}"' for s in header[:-2]])]  # header
        for i_record in range(len(records)):
            r = records[i_record]
            if kw["unc"]:
                value = f"Around[{r[-3]}, {{{r[-1]:.5g}, {r[-2]:.5g}}}]"
            else:
                value = str(r[-3])
            value = value.replace("e", "*^") + units[-1]  # Mathematica "E" notation
            keys = [f"{v}{units[i]}" for i, v in enumerate(r) if i < n_columns - 3]
            keys.append(value)
            lines.append(concat(keys))
        click.echo("{\n" + ",\n".join(lines) + "\n}")
    exit(0)


@main.command(name="list", context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("substr", nargs=-1)
@click.option("--all", "-a", is_flag=True, help="List all the tables in this package.")
@click.option("--full", "-f", is_flag=True, help="List full paths")
def cmd_list(**kw):
    # type: (Any)->None
    """List the predefined tables, containing SUBSTR if specified."""
    colorama.init()
    _configure_logger()

    table_dir_abs = config.package_dir / config.table_dir  # absolute path
    substr_list = [s.lower() for s in kw["substr"]]  # case insensitive

    def to_show(key, grid, info):
        # type: (Optional[str], str, Optional[str])->bool
        """Check if all the substr are in (any of) the arguments."""
        return all(
            any(v is not None and substr in v.lower() for v in [key, grid, info])
            for substr in substr_list
        )

    def str_to_pathstr(s):
        # type: (str)->str
        return (table_dir_abs / s).absolute().__str__() if kw["full"] else s

    # predefined paths
    lines = []  # type: List[Tuple[Optional[str], str, Optional[str]]]
    checked = {}  # type: MutableMapping[str, bool]
    for key, value in config.table_names.items():
        grid, info = config.parse_table_value(value)
        checked[grid.__str__()] = True
        if to_show(key, grid, info):
            lines.append((key, grid, info))

    # list all the grid even without predefined keys
    if kw["all"]:
        for f in sorted(table_dir_abs.glob("**/*")):
            rel_path = f.relative_to(table_dir_abs).__str__()
            if all(
                [
                    not rel_path.endswith(".info"),
                    to_show(None, rel_path, None),
                    not checked.get(rel_path),
                    f.is_file(),
                    f.with_suffix(".info").is_file(),
                ]
            ):
                lines.append((None, rel_path, None))

    for k, grid, info in sorted(lines, key=lambda x: x[1]):
        click.echo(
            "{key}\t{dim}{grid}{info}{reset}".format(
                key=k or "",
                grid=str_to_pathstr(grid),
                info=" " + str_to_pathstr(info) if info else "",
                dim=colorama.Style.DIM,
                reset=colorama.Style.RESET_ALL,
            )
        )
    exit(0)
