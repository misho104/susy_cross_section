"""Dictionary of the cross section tables."""

from typing import Mapping, Tuple, Union  # noqa: F401

table_names = {
    '13TeV.n2x1-.wino': 'data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_m.csv',
    '13TeV.n2x1+.wino': 'data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_p.csv',
    '13TeV.n2x1+-.wino': 'data/lhc_susy_xs_wg/13TeVn2x1wino_envelope_pm.csv',
}  # type: Mapping[str, Union[str, Tuple[str, str]]]
