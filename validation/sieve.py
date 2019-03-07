"""Validation of interpolators for 1d grid."""

import itertools
import logging
import pathlib
from typing import List, MutableMapping, Optional, Sequence, Union

from pandas import DataFrame

from susy_cross_section.interp.interpolator import AbstractInterpolator
from susy_cross_section.table import Table

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
PathLike = Union[str, pathlib.Path]


class SievedTable:
    """Sieved Table."""

    @staticmethod
    def get_levels(table):
        # type: (DataFrame)->List[List[float]]
        """Return levels, or the values of grids, of a table."""
        if table.index.nlevels == 1:
            return [table.index.values]
        else:
            return table.index.levels

    @staticmethod
    def get_loc_list(table, key, mod=None):
        # type: (DataFrame, Sequence[float], Optional[int])->Sequence[int]
        """Return the location of key as a list."""
        if mod:
            return tuple(c % mod for c in SievedTable.get_loc_list(table, key))
        if len(key) == 1:
            return (table.index.get_loc(key[0]),)
        else:
            return tuple(table.index.levels[n].get_loc(k) for n, k in enumerate(key))

    @staticmethod
    def sieve(table, signature, base):
        # type: (DataFrame, Sequence[int], int)->DataFrame
        """Return a (new) sieved table with specified signature.

        Parameters
        ----------
        table: pandas.DataFrame
            The original data, which is not modified by this method.staticmethod
        signature: List[int]
            The grids to remain; all the other grid lines are removed.
        base: int
            The sparseness of the sieving.
        """
        t = table.copy()
        levels = SievedTable.get_levels(table)
        assert len(signature) == len(levels)
        for level, points in enumerate(levels):
            to_sieve = [p for i, p in enumerate(points) if i % base != signature[level]]
            t.drop(to_sieve, inplace=True, level=level if level > 0 else None)
        try:
            # For MultiIndex, https://stackoverflow.com/questions/28772494/
            t.index = t.index.remove_unused_levels()
        except AttributeError:
            pass
        return t

    @staticmethod
    def generate_sieved_tables(table, base):
        # type: (DataFrame, int)->MutableMapping[Sequence[int], DataFrame]
        """Generate all the patterns of sieved tables."""
        levels = SievedTable.get_levels(table)
        result = {}  # type: MutableMapping[Sequence[int], DataFrame]
        for signature in itertools.product(range(base), repeat=len(levels)):
            result[signature] = SievedTable.sieve(table, signature, base)
        return result

    def __init__(self, table, base=2):
        self.tables = self.generate_sieved_tables(table, base)


class SievedInterpolations:
    """Interpolations based on sieved tables.

    Interpolations are performed for all the patterns of sieving.
    """

    def __init__(self, table, interpolator, base=2):
        # type: (Table, AbstractInterpolator, int)->None
        self._table = table
        self._interpolator = interpolator
        self._base = 2
        self._sieved = SievedTable(table, base)
        self._interpolations = {
            signature: interpolator.interpolate(sieved_table)
            for signature, sieved_table in SievedTable(table, base=base).tables.items()
        }

    def _negate(self, grid_point):
        # type: (int)->int
        return int(grid_point + self._base / 2) % self._base

    def __call__(self, args):
        # type: (Sequence[float])->float
        """Calculate sieved-interpolated values for a given table."""
        loc = self._sieved.get_loc_list(self._table, args, self._base)
        signature = tuple(self._negate(x) for x in loc)  # use the farthest
        return self._interpolations[signature](*args)

    def interpolated_table(self):
        result = self._table.copy()
        for level, points in enumerate(result.index.levels):
            result.drop([points[0], points[-1]], level=level, inplace=True)
        try:
            result.index = result.index.remove_unused_levels()  # for multiindex
        except AttributeError:
            pass
        for key, row in result.iterrows():
            interp = self(key)
            badness = (interp - row["value"]) / min(row["unc+"], row["unc-"])
            result.loc[key, "interpolation"] = interp
            result.loc[key, "badness"] = badness
        return result
