"""Validation of interpolators for 1d grid."""

import logging
from typing import List, Optional, Tuple, Union

import matplotlib.pyplot
import matplotlib.style
import numpy
from matplotlib.backends.backend_pdf import PdfPages

from susy_cross_section.interp.interpolator import Interpolation, Scipy1dInterpolator
from susy_cross_section.table import Table
from validation.base import BaseValidator, PathLike

SubplotType = Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
matplotlib.style.use("seaborn-whitegrid")


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class OneDimComparator(BaseValidator):
    """Generator of validation plots for one-dimensional grid tables."""

    interpolators = [
        Scipy1dInterpolator(kind="pchip", axes="loglog"),
        Scipy1dInterpolator(kind="linear", axes="loglog"),
        Scipy1dInterpolator(kind="spline", axes="loglog"),
        Scipy1dInterpolator(kind="akima", axes="loglog"),
    ]
    """The interpolators to test.

    The first one is used as the benchmark standard."""

    grid_division = 9
    """Number of sample points within each interval."""

    def __init__(self, output=None):
        # type: (Optional[Union[PdfPages, PathLike]])->None
        super().__init__(output=output)
        matplotlib.style.use("seaborn-whitegrid")

    def __del__(self):
        """Close the pdf as a destructor."""
        super().__del__()

    @staticmethod
    def _calculate_badness(table, ux, ip1, ip2):
        # type: (Table, numpy.ndarray, Interpolation, Interpolation)->Tuple[float, float]
        """Calculate the maximal variation and badness of interpolator.

        Variation is defined for each sampling point by the difference between
        two interpolation results, :ar:`ip1` and :ar:`ip2`, where multiple
        sampling points are picked up in every interval and they are given by
        :ar:`ux`. This function returns its maximum.

        For each interval, the representative value of uncertainty is defined
        by the minimum of the uncertainties associated to the grid points
        surrounding the interval. Badness for each sampling point is defined by
        the ratio of the variation to the representative value, and this
        function returns the maximum of the badnesses.

        Parameters
        ----------
        table: Table
            The table for evaluation.
        ux: numpy.ndarray
            The sampling points in x-axis.
        ip1: Interpolation
            A result of interpolation.
        ip2: Interpolation
            Another result of interpolation.

        Returns
        -------
        Tuple[float, float]
            The first element is the max difference between the interpolation
            results normalized to the central value, or relative uncertainty due to
            the interpolation, and the second is the ratio of the relative
            uncertainty to the other uncertainty in the grid data.
        """
        x = table.index
        y, ym, yp = table["value"], numpy.abs(table["unc-"]), table["unc+"]

        variations = []  # type: List[float]
        badnesses = []  # type: List[float]

        for x1, x2 in zip(x, x[1:]):
            interval = [xx for xx in ux if x1 < xx < x2]
            rep_unc = min(
                ym[x1] / y[x1], ym[x2] / y[x2], yp[x1] / y[x1], yp[x2] / y[x2]
            )
            uy1 = numpy.array([ip1(x) for x in interval])
            uy2 = numpy.array([ip2(x) for x in interval])
            var = numpy.max(numpy.abs(uy2 / uy1 - 1))
            variations.append(var)
            badnesses.append(var / rep_unc)
        return float(max(variations)), float(max(badnesses))

    def generate_interpolation_plot(self, table, ax):
        # type: (Table, matplotlib.axes.Axes)->None
        """Return a plot with the data points and interpolating functions."""
        ax.set_xscale("linear")
        ax.set_yscale("log")

        x = table.index
        y = table["value"]
        ey = (table["unc-"], table["unc+"])
        self.set_labels(ax, table, title="Interpolation result of {file_name}")
        ax.errorbar(x, y, ey, fmt="none", elinewidth=1, ecolor="black", label="data")

        ux = self.split_interval(x, n=self.grid_division, log=False)
        for interp in self.interpolators:
            i = interp.interpolate(table)
            label = "{}/{}".format(interp.kind, interp.axes)
            ax.plot(ux, [i(x) for x in ux], linewidth=0.5, label=label)
        ax.legend()

    def generate_variation_plot(self, table, ax, with_legend=False):
        # type: (Table, matplotlib.axes.Axes, bool)->None
        """Plot variation among interpolators."""
        ax.set_xscale("linear")
        ax.set_yscale("linear")

        if len(self.interpolators) < 2:
            logger.warning("No interpolators to compare.")
            return

        x = table.index
        y = table["value"]
        ey = (table["unc-"], table["unc+"])
        ux = self.split_interval(x, n=self.grid_division, log=False)

        variations = []  # type: List[float]
        badnesses = []  # type: List[float]
        for k, interp in enumerate(self.interpolators):
            i = interp.interpolate(table)
            uy = numpy.array([i(x) for x in ux])
            label = "{}/{}".format(interp.kind, interp.axes)
            if k == 0:
                i0 = i
                uy0 = uy
                label0 = label
                label = ""
            else:
                v, b = self._calculate_badness(table, ux, i0, i)
                variations.append(v)
                badnesses.append(b)
            if not with_legend:
                label = ""
            ax.plot(ux, uy / uy0 - 1, linewidth=0.5, label=label)
        max_variation = max(variations)
        max_badness = max(badnesses)

        ax.plot(x, ey[1] / y, color="black", label="uncertainty of cross-section value")
        ax.plot(x, -ey[0] / y, color="black")
        self.set_labels(ax, table, title="Interpolator comparison in {file_name}")
        ax.set_ylabel("Variation from {}".format(label0))
        msg = "Variation={:.2%}; Badness={:.3}".format(max_variation, max_badness)
        ax.plot([], [], " ", label=msg)
        ax.legend()

    def draw_plots(self, file, file_name):
        m = (0.22, 0.13, 0.1, 0.1)  # left, bottom, right, top
        w, h = 1 - m[0] - m[2], 1 - m[1] - m[3]
        h1 = h * 0.6

        fig = matplotlib.pyplot.figure(figsize=(6.4, 9.05))
        ax1 = fig.add_axes((m[0], m[1] + (h - h1), w, h1))
        ax2 = fig.add_axes((m[0], m[1], w, h - h1), sharex=ax1)

        table = file.tables[file_name]
        self.generate_interpolation_plot(table, ax1)
        self.generate_variation_plot(table, ax2, with_legend=False)
        ax1.tick_params(labelbottom=False)
        ax1.set_title(table.file.table_path.name)
        ax1.set_xlabel(None)
        ax2.set_title(None)
        self._save(fig)
