#!env python3

"""A script to scrape various cross-section data files into a CSV."""


import csv
import io
import sys
from typing import List, Sequence, Tuple, Union  # noqa: F401

import bs4
import click

__author__ = "Sho Iwamoto"
__copyright__ = "Copyright (C) 2018 Sho Iwamoto / Misho"
__license__ = "MIT"
__scriptname__ = "XS scraper"
__version__ = "0.2.0"


CrossSectionValueType = Union[float, str]   # because '10.0%' may be included in the data....
CrossSectionTableType = List[List[CrossSectionValueType]]


class CrossSectionTableWriter:
    """Describe the CSV writer used in this package."""

    def __init__(self, f):
        self.writer = csv.writer(f, dialect="excel", strict="True", quoting=csv.QUOTE_MINIMAL)

    def _format_float(self, v):
        # type: (CrossSectionValueType)->CrossSectionValueType
        if isinstance(v, str) or isinstance(v, int):
            return v
        elif isinstance(v, float):
            if 0 < abs(v) < 1e-3:
                return "{value:e}".format(value=v)
            else:
                return v

    def _get_max_width(self, table):
        # type: (CrossSectionTableType)->List[int]
        max_columns = max(len(row) for row in table)
        width = [0 for i in range(max_columns)]

        for row in table:
            for i, v in enumerate(row):
                w = len(str(v))
                if w > width[i]:
                    width[i] = w
        return width

    def _padding(self, row, width):
        # type: (List[CrossSectionValueType], List[int])->List[CrossSectionValueType]
        result = []  # type: List[CrossSectionValueType]
        to_pad = 0
        for i, v in enumerate(row):
            s = str(v)
            length = len(s)
            if i == 0:
                result.append(s)
            else:
                result.append(" " + (s.rjust(length + to_pad) if to_pad > 0 else s))
            to_pad = width[i] - length
        return result

    def writerows(self, table):
        # type: (CrossSectionTableType)->None
        """Output multiple rows in a formatted and padded CSV format."""
        table = [[self._format_float(v) for v in row] for row in table]
        width = self._get_max_width(table)
        table = [self._padding(row, width) for row in table]
        self.writer.writerows(table)

    def writerow(self, row):
        # type: (Sequence[CrossSectionValueType])->None
        """Output single row in a formatted CSV format."""
        self.writer.writerow([self._format_float(v) for v in row])


def parse_html_table(input_string):
    # type: (str)->List[CrossSectionTableType]

    def parse_td(td):
        # type: (bs4.element.Tag)->Union[float, str]
        content = " ".join(td.stripped_strings)
        try:
            return float(content)
        except ValueError:
            return content

    def parse_tr(tr):
        # type: (bs4.element.Tag)->List[CrossSectionValueType]
        return [parse_td(td) for td in tr.find_all(["td", "th"])]

    def parse_table(table):
        # type: (bs4.element.Tag)->CrossSectionTableType
        return [parse_tr(tr) for tr in table.find_all(["tr"])]

    tables = bs4.BeautifulSoup(input_string, features="lxml").find_all("table")
    return [parse_table(t) for t in tables]


script_help = """Parse various cross - section data to CSV file.


For data containing multiple tables, `index` option is required to choose the data to parse."""


@click.command(help=script_help, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name=__scriptname__)
@click.option("--input-type", type=click.Choice(["html-table"]), default="html-table", show_default=True,
              help="Input-data format.")
@click.option("--index", type=int, default=-1, help="The index of data parsed if multiple entries are found.")
def call_scrape(input_type="html-table", index=-1):
    # type: (str, int)->None
    """Handle command - line arguments and IO and call scrape method.

    Parameters
    ----------
    input_type: input format.
    """
    input_string = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="ignore").read()
    if input_type == "html-table":
        data_tables = parse_html_table(input_string)
    else:
        raise RuntimeError  # never come here as far as called with Click

    if len(data_tables) == 0:
        raise click.ClickException("No cross-section data is found in input.")
    elif len(data_tables) == 1:
        data = data_tables[0]
    elif index > 0:
        data = data_tables[index - 1]
    else:
        raise click.ClickException("Multiple data tables are found; specify --index option.")

    CrossSectionTableWriter(sys.stdout).writerows(data)
    exit(0)


if __name__ == "__main__":
    call_scrape()
