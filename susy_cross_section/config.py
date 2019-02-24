"""Configuration data of this package."""

from __future__ import absolute_import, division, print_function  # py2

import sys
from typing import Mapping, Tuple, Union  # noqa: F401

if sys.version_info[0] < 3:  # py2
    str = basestring  # noqa: A001, F821

table_names = {
    # gluino
    "7TeV.gg.decoup": "data/nllfast/7TeV/gdcpl_nllnlo_mstw2008.grid",
    "7TeV.gg": "data/nllfast/7TeV/gg_nllnlo_mstw2008.grid",
    "7TeV.gg.high": "data/nllfast/7TeV/gg_nllnlo_hm_mstw2008.grid",
    "8TeV.gg.decoup": "data/nllfast/8TeV/gdcpl_nllnlo_mstw2008.grid",
    "8TeV.gg": "data/nllfast/8TeV/gg_nllnlo_mstw2008.grid",
    "8TeV.gg.high": "data/nllfast/8TeV/gg_nllnlo_hm_mstw2008.grid",
    "13TeV.gg.decoup": "data/nnllfast/13TeV/gdcpl_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    "13TeV.gg": "data/nnllfast/13TeV/gg_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    "7TeV.sg": "data/nllfast/7TeV/sg_nllnlo_mstw2008.grid",
    "7TeV.sg.high": "data/nllfast/7TeV/sg_nllnlo_hm_mstw2008.grid",
    "8TeV.sg": "data/nllfast/8TeV/sg_nllnlo_mstw2008.grid",
    "8TeV.sg.high": "data/nllfast/8TeV/sg_nllnlo_hm_mstw2008.grid",
    "13TeV.sg": "data/nnllfast/13TeV/sg_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    # squark (10 squarks)
    "7TeV.sb10.decoup": "data/nllfast/7TeV/sdcpl_nllnlo_mstw2008.grid",
    "7TeV.sb10": "data/nllfast/7TeV/sb_nllnlo_mstw2008.grid",
    "7TeV.ss10": "data/nllfast/7TeV/ss_nllnlo_mstw2008.grid",
    "8TeV.sb10.decoup": "data/nllfast/8TeV/sdcpl_nllnlo_mstw2008.grid",
    "8TeV.sb10": "data/nllfast/8TeV/sb_nllnlo_mstw2008.grid",
    "8TeV.ss10": "data/nllfast/8TeV/ss_nllnlo_mstw2008.grid",
    "13TeV.sb10.decoup": "data/nnllfast/13TeV/sdcpl_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    # stop
    "7TeV.st": "data/nllfast/7TeV/st_nllnlo_mstw2008.grid",
    "8TeV.st": "data/nllfast/8TeV/st_nllnlo_mstw2008.grid",
    "13TeV.st": "data/nnllfast/13TeV/st_nnlonnll_pdf4lhc15_13TeV_wpresc.grid",
    # EWKino
    "13TeV.n2x1-.wino": "data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_m.csv",
    "13TeV.n2x1+.wino": "data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_p.csv",
    "13TeV.n2x1+-.wino": "data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_pm.csv",
    "13TeV.x1x1.wino": "data/lhc_susy_xs_wg/13TeVx1x1wino_envelope.csv",
    "13TeV.slepslep.ll": "data/lhc_susy_xs_wg/13TeVslepslep_ll.csv",
    "13TeV.slepslep.rr": "data/lhc_susy_xs_wg/13TeVslepslep_rr.csv",
    "13TeV.slepslep.maxmix": "data/lhc_susy_xs_wg/13TeVslepslep_maxmix.csv",
}  # type: Mapping[str, Union[str, Tuple[str, str]]]
"""
Preset table names and paths to files.

A :typ:`dict` object, where the values show the paths to table and info files.
Values are a tuple `!(table_file_path, info_file_path)`, or `!table_file_path`
if info_file_path is given by replacing the extension of table_file_path to
`!.info`. Relative paths are interpreted from this package directory (i.e.,
the directory having this file).

:Type:
    :typ:`dict[str, str or tuple[str, str]]`
"""
