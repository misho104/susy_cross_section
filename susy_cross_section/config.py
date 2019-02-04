"""Dictionary of the cross section tables."""

from __future__ import absolute_import, division, print_function  # py2

import sys
from typing import Mapping, Tuple, Union  # noqa: F401

if sys.version_info[0] < 3:  # py2
    str = basestring          # noqa: A001, F821

table_names = {
    '13TeV.n2x1-.wino': 'data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_m.csv',
    '13TeV.n2x1+.wino': 'data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_p.csv',
    '13TeV.n2x1+-.wino': 'data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_pm.csv',
    '13TeV.x1x1.wino': 'data/lhc_susy_xs_wg/13TeVx1x1wino_envelope.csv',
    '13TeV.slepslep.ll': 'data/lhc_susy_xs_wg/13TeVslepslep_ll.csv',
    '13TeV.slepslep.rr': 'data/lhc_susy_xs_wg/13TeVslepslep_rr.csv',
    '13TeV.slepslep.maxmix': 'data/lhc_susy_xs_wg/13TeVslepslep_maxmix.csv',
}  # type: Mapping[str, Union[str, Tuple[str, str]]]
