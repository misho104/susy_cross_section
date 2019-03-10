"""Runner of validation scripts.

This code is supposed to be called from **the root directory of this
repository** by ``python3 -m validation ARGS``.
"""

import logging
import pathlib

import click
import coloredlogs
from matplotlib.backends.backend_pdf import PdfPages

import susy_cross_section
import susy_cross_section.config
import susy_cross_section.scripts
from susy_cross_section.table import File
from validation.validators import choose_validator

__author__ = susy_cross_section.scripts.__author__
__copyright__ = susy_cross_section.scripts.__copyright__
__license__ = "MIT"
__packagename__ = "susy_cross_section/validation"
__version__ = susy_cross_section.scripts.__version__

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _configure_logger():
    # type: ()->None
    """Configure logger so that proper logs are shown on console."""
    coloredlogs.install(
        level=logging.INFO, logger=logging.getLogger(), fmt="%(levelname)8s %(message)s"
    )


def _assert_using_local_package():
    # type: ()->None
    target_package_path = pathlib.Path(susy_cross_section.__file__).absolute()
    logger.debug("Loaded susy_cross_section package at {}.".format(target_package_path))
    if pathlib.Path(".").absolute() not in target_package_path.parents:
        logger.critical("Invalid module loaded: %s", target_package_path)
        logger.info("Maybe you call this module from a wrong directory?")
        logger.info('Run "python -m validation ARGS" from the root of this repository.')
        exit(1)


def _all_tables_iter(table_name="xsec"):
    for key in susy_cross_section.config.table_names:
        paths = susy_cross_section.config.table_paths(key)
        logger.info("Evaluating: {}".format(paths[0]))
        yield key, File(*paths).tables[table_name]


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(__version__, "-V", "--version", prog_name=__packagename__)
@click.pass_context
def main(ctx):  # type: ignore
    """Invoke specified validation command."""
    ctx.info_name = "python -m validation"
    _configure_logger()
    _assert_using_local_package()
    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())
        exit(1)


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--all", is_flag=True, help="Run for all named tables.")
@click.option("--output", "-o", type=click.Path(exists=False, writable=True))
@click.argument("table", required=False, type=click.Path(exists=True, readable=True))
@click.pass_context
def compare(ctx, *args, **kwargs):  # type: ignore
    """Plot multiple interpolation results."""
    pdf = PdfPages(kwargs["output"]) if kwargs["output"] else None
    if kwargs["all"]:
        for key, table in _all_tables_iter():
            try:
                choose_validator(table)(pdf).compare(table, key)
            except ValueError as e:
                print(e)
    elif kwargs["table"]:
        f = pathlib.Path(kwargs["table"])
        assert f.is_file()
        table = File(f).tables["xsec"]
        try:
            choose_validator(table)(pdf).compare(table)
        except ValueError as e:
            print(e)
    else:
        click.echo("table path or --all option must be required.")
    if pdf:
        pdf.close()


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--all", is_flag=True, help="Run for all named tables.")
@click.option("--output", "-o", type=click.Path(exists=False, writable=True))
@click.argument("table", required=False, type=click.Path(exists=True, readable=True))
@click.pass_context
def sieve(ctx, *args, **kwargs):  # type: ignore
    """Plot multiple interpolation results of 1d grid."""
    pdf = PdfPages(kwargs["output"]) if kwargs["output"] else None
    if kwargs["all"]:
        for _key, table in _all_tables_iter():
            try:
                choose_validator(table)(pdf).sieve(table)
            except ValueError as e:
                print(e)
    elif kwargs["table"]:
        f = pathlib.Path(kwargs["table"])
        assert f.is_file()
        table = File(f).tables["xsec"]
        try:
            choose_validator(table)(pdf).sieve(table)
        except ValueError as e:
            print(e)
    else:
        click.echo("table path or --all option must be required.")
    if pdf:
        pdf.close()


if __name__ == "__main__":
    coloredlogs.install(
        level=logging.INFO, logger=logging.getLogger(), fmt="%(levelname)8s %(message)s"
    )
    main()
