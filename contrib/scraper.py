#!env python3

import json
import logging
import re
import sys
from typing import List, Tuple, Union
import click

__author__ = 'Sho Iwamoto'
__copyright__ = 'Copyright (C) 2018 Sho Iwamoto / Misho'
__license__ = 'MIT'
__scriptname__ = 'XS scraper'
__version__ = '0.1.0'

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


UncertaintyType = Union[float, List[float]]
ResultType = Union[
    Tuple[float, float, UncertaintyType],                    # mass, xs, unc
    Tuple[float, float, UncertaintyType, UncertaintyType]    # mass, xs, +unc, -unc
]


def scrape(data: str)->List[ResultType]:
    result = []  # type: List[ResultType]
    rows = re.findall(r'<tr(?: .*?)?>(.*?)</ *tr *>', data, re.DOTALL)
    for row in rows:
        columns = re.findall(r'<t[dh](?: .*?)?>(.*?)</ *t[dh] *>', row, re.DOTALL)
        try:
            v = [float(x) for x in columns]
        except ValueError:  # header
            logger.warning('ignored line ' + ', '.join([re.sub(r'<.*?>', '', c) for c in columns]))
            continue
        if len(v) == 3:
            result.append((v[0], v[1], v[2]))
        elif len(v) == 6:
            result.append((v[0], v[1],
                           [v[1]*v[2]/100, v[1]*v[3]/100],
                           [v[1]*v[4]/100, v[1]*v[5]/100]))
        else:
            logger.warning('ignored line ' + ', '.join(columns))

    return sorted(result, key=lambda p: p[0])


@click.command(help='Convert cross-section data on CERN TWiki to JSON',
               context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('input', type=click.Path(exists=True, dir_okay=False), required=False)
@click.argument('output', type=click.Path(dir_okay=False), required=False)
@click.version_option(__version__, '-V', '--version', prog_name=__scriptname__)
def scrape_html(**kwargs):
    if kwargs['input']:
        with open(kwargs['input']) as f:
            input_string = f.read()
    else:
        input_string = sys.stdin.read()

    output_string = json.dumps(scrape(input_string), indent=2)

    if kwargs['output']:
        with open(kwargs['output'], 'w') as f:
            f.write(output_string)
    else:
        print(output_string)


if __name__ == '__main__':
    scrape_html()
