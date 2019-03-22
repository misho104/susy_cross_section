"""Configuration data of this package."""

from __future__ import absolute_import, division, print_function  # py2

import pathlib
import sys
from typing import Mapping, Optional, Tuple, Union  # noqa: F401

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821

table_dir = "susy_cross_section/data"
"""
Base directory for table data, relative to the package directory.

:Type:
    :typ:`str`
"""

package_dir = pathlib.Path(__file__).absolute().parent.parent
"""
The package diretory, usually no need to change.

:Type:
    :typ:`pathlib.Path`
"""


table_names = {
    # gluino
    "7TeV.gg.decoup": "nllfast/7TeV/gdcpl_nllnlo_mstw2008.grid",
    "7TeV.gg": "nllfast/7TeV/gg_nllnlo_mstw2008.grid",
    "7TeV.gg.high": "nllfast/7TeV/gg_nllnlo_hm_mstw2008.grid",
    "8TeV.gg.decoup": "nllfast/8TeV/gdcpl_nllnlo_mstw2008.grid",
    "8TeV.gg": "nllfast/8TeV/gg_nllnlo_mstw2008.grid",
    "8TeV.gg.high": "nllfast/8TeV/gg_nllnlo_hm_mstw2008.grid",
    "13TeV.gg.decoup": "nnllfast/13TeV/gdcpl_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    "13TeV.gg": "nnllfast/13TeV/gg_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    "7TeV.sg": "nllfast/7TeV/sg_nllnlo_mstw2008.grid",
    "7TeV.sg.high": "nllfast/7TeV/sg_nllnlo_hm_mstw2008.grid",
    "8TeV.sg": "nllfast/8TeV/sg_nllnlo_mstw2008.grid",
    "8TeV.sg.high": "nllfast/8TeV/sg_nllnlo_hm_mstw2008.grid",
    "13TeV.sg": "nnllfast/13TeV/sg_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    # squark (10 squarks)
    "7TeV.sb10.decoup": "nllfast/7TeV/sdcpl_nllnlo_mstw2008.grid",
    "7TeV.sb10": "nllfast/7TeV/sb_nllnlo_mstw2008.grid",
    "7TeV.ss10": "nllfast/7TeV/ss_nllnlo_mstw2008.grid",
    "8TeV.sb10.decoup": "nllfast/8TeV/sdcpl_nllnlo_mstw2008.grid",
    "8TeV.sb10": "nllfast/8TeV/sb_nllnlo_mstw2008.grid",
    "8TeV.ss10": "nllfast/8TeV/ss_nllnlo_mstw2008.grid",
    "13TeV.sb10.decoup": "nnllfast/13TeV/sdcpl_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    "13TeV.sb10": "nnllfast/13TeV/sb_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    "13TeV.ss10": "nnllfast/13TeV/ss_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    # stop
    "7TeV.st": "nllfast/7TeV/st_nllnlo_mstw2008.grid",
    "8TeV.st": "nllfast/8TeV/st_nllnlo_mstw2008.grid",
    "13TeV.st": "nnllfast/13TeV/st_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    # EWKino
    "13TeV.n2x1-.wino": "lhc_susy_xs_wg/13TeVn2x1wino_envelope_m.csv",
    "13TeV.n2x1+.wino": "lhc_susy_xs_wg/13TeVn2x1wino_envelope_p.csv",
    "13TeV.n2x1+-.wino": "lhc_susy_xs_wg/13TeVn2x1wino_envelope_pm.csv",
    "13TeV.x1x1.wino": "lhc_susy_xs_wg/13TeVx1x1wino_envelope.csv",
    "13TeV.slepslep.ll": "lhc_susy_xs_wg/13TeVslepslep_ll.csv",
    "13TeV.slepslep.rr": "lhc_susy_xs_wg/13TeVslepslep_rr.csv",
    "13TeV.slepslep.maxmix": "lhc_susy_xs_wg/13TeVslepslep_maxmix.csv",
}  # type: Mapping[str, Union[str, Tuple[str, str]]]
"""
Preset table names and paths to files.

A :typ:`dict` object, where the values show the paths to table and info files.
Values are a tuple `!(table_file_path, info_file_path)`, or `!table_file_path`
if info_file_path is given by replacing the extension of table_file_path to
`!.info`. The path is calculated relative to :data:`table_dir`.

:Type:
    :typ:`dict[str, str or tuple[str, str]]`
"""


def parse_table_value(obj):
    # type: (Union[str, Tuple[str, str]])->Tuple[str, Optional[str]]
    """Parse the table values, which might be str or tuple, to a tuple.

    Parameters
    ----------
    obj: str or tuple[str, str]
        The value of :data:`table_names`.

    Returns
    -------
    tuple[str, str or None]
        The path to grid file and (if specified) to info file.
    """
    if not obj:
        raise ValueError("Table value must not be empty.")
    elif len(obj) < 2:
        # having one or two elements must be a tuple.
        return obj[0], obj[1] if len(obj) == 2 else None
    else:
        # otherwise it seems a string.
        assert isinstance(obj, str)
        return obj, None


def table_paths(key, absolute=False):
    # type: (str, bool)->Tuple[Optional[pathlib.Path], Optional[pathlib.Path]]
    """Return the relative paths to table file and info file.

    Parameters
    ----------
    key: str
        The key of cross-section table.
    absolute: bool
        Whether to return absolute paths or not.

    Returns
    -------
    Tuple[pathlib.Path, pathlib.Path]
        The relative path to the grid file and the info file.

        The path for info file is returned only if it is configured. The paths
        are calculated relative to the package directory.
    """
    value = table_names.get(key)
    if not value:
        return None, None

    grid, info = parse_table_value(value)

    base_dir = pathlib.Path(table_dir)
    if absolute:
        base_dir = package_dir / base_dir
    grid_path = base_dir / grid
    info_path = base_dir / info if info else None
    return grid_path, info_path
