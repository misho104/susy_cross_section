"""Validation of interpolators for 1d grid."""

import logging
from typing import Any, List, Optional, Sequence, Tuple, Union

import matplotlib
import matplotlib.style
import numpy
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pandas import DataFrame

from susy_cross_section.interp.interpolator import (
    AbstractInterpolator,
    Interpolation,
    Scipy1dInterpolator,
)
from susy_cross_section.table import Table
from validation.base import BaseValidator, PathLike
from validation.sieve import SievedInterpolations

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

    def draw_interpolations(self, ax, table, interpolations):
        # type: (Table, Axes, List[Tuple[str, Any]])->None
        """Draw a plot of data points interpolations.

        Parameters
        ----------
        ax: Axes
            The axes to be drawn.
        table: Table
            The data table to be interpolated and drawn.
        interpolations: List[Tuple[str, interpolation object]]
            The interpolation data to be drawn.

            The object can be an interpolator (`AbstractInterpolator`), its output
            (`Interpolation`), or a list of (x, y)-tuples.
        """
        ax.set_xscale("linear")
        ax.set_yscale("log")

        x = table.index
        y = table["value"]
        ey = (table["unc-"], table["unc+"])
        self.set_labels(ax, table, title="Interpolation result of {file_name}")
        ax.errorbar(x, y, ey, fmt="none", elinewidth=1, ecolor="black", label="data")

        ux = self.split_interval(x, n=self.grid_division, log=False)
        for label, ip in interpolations:
            if isinstance(ip, AbstractInterpolator):
                i = ip.interpolate(table)
                x_list = ux
                y_list = [i(x) for x in ux]
            elif isinstance(ip, Interpolation):
                x_list = ux
                y_list = [ip(x) for x in ux]
            else:
                x_list, y_list = zip(*ip)
            ax.plot(x_list, y_list, linewidth=0.5, label=label)
        ax.legend()

    def generate_variation_plot(self, table, ax, with_legend=False):
        # type: (Table, Axes, bool)->None
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
        ips = [("{}/{}".format(i.kind, i.axes), i) for i in self.interpolators]

        self.draw_interpolations(ax1, table, ips)
        self.generate_variation_plot(table, ax2, with_legend=False)
        ax1.tick_params(labelbottom=False)
        ax1.set_title(table.file.table_path.name)
        ax1.set_xlabel(None)
        ax2.set_title(None)
        self._save(fig)


class SievedInterpolationValidator(BaseValidator):
    """Validation with sieved table interpolations."""

    def __init__(self, output=None):
        # type: (Optional[Union[PdfPages, PathLike]])->None
        super().__init__(output=output)

    def __del__(self):
        """Deconstruct this instance."""
        super().__del__()

    def draw_interpolation(self, ax, table, data):
        # type: (Axes, Table, DataFrame)->None
        if data.index.nlevels == 1:
            pass
        elif data.index.nlevels == 2:

            def f(x):
                # type: (float)->float
                return numpy.log10(x)

            ax.view_init(30, 40)

            xs, ys = zip(*table.index.values)
            zs, zps, zms = (table[k].to_numpy() for k in ("value", "unc+", "unc-"))
            with_label = True
            for x, y, z, zp, zm in zip(xs, ys, zs, zps, zms):
                ax.plot(
                    [x, x],
                    [y, y],
                    [f(z + zp), f(z - zm)],
                    marker="",
                    c="black",
                    linewidth=0.3,
                    label="Data" if with_label else None,
                )
                with_label = False

            xs, ys = zip(*data.index.values)
            ips = [f(z) for z in data["interpolation"].to_numpy()]
            ax.scatter(
                xs,
                ys,
                ips,
                c="r",
                marker="_",
                s=10,
                label="interpolation",
                linewidth=0.5,
            )
            self.set_labels_3d(ax, table, title="{file_name}")
            ax.legend(loc="upper right", bbox_to_anchor=(1, 0.92))
            ax.set_zlabel(r"$\log_{10}$ " + ax.get_zlabel())
        else:
            logger.critical("Plot index dimension too high.")
            raise ValueError("Too high dimension.")

    def draw_badness(self, ax, table, data):
        # type: (Axes, Table, DataFrame)->None

        def extend(seq):
            # type: (Sequence[float])->List[float]
            r = [(x1 + x2) / 2 for x1, x2 in zip(seq, seq[1:])]
            r.insert(0, seq[0] - (seq[1] - seq[0]) / 2)
            r.append(seq[-1] + (seq[-1] - seq[-2]) / 2)
            return r

        magma = matplotlib.pyplot.get_cmap("magma_r")
        cmap_array = [magma(i) for i in range(0, 24 * 12, 24)]
        cmap = matplotlib.colors.ListedColormap(cmap_array[1:-1])
        cmap.set_under(cmap_array[0])
        cmap.set_over(cmap_array[-1])

        if data.index.nlevels == 1:
            pass
        elif data.index.nlevels == 2:
            xs, ys = data.index.levels
            zs = abs(data["badness"].unstack().to_numpy())
            mesh = ax.pcolormesh(
                # note the reversed order!
                extend(ys),
                extend(xs),
                zs,
                cmap=cmap,
                vmin=0,
                vmax=1,
                linewidths=5,
            )
            bar = ax.figure.colorbar(mesh)
            bar.set_label("badness", rotation=270)
            bar.ax.yaxis.labelpad = 10
            ax.grid()
            self.set_labels_3d(ax, table, z=False)
        else:
            logger.critical("Plot index dimention too high.")
            raise ValueError("Too high dimension.")

    def plot(self, table, interpolator):
        # type: (Table, Union[AbstractInterpolator, DataFrame])->matplotlib.figure.Figure
        if isinstance(interpolator, AbstractInterpolator):
            # perform interpolation according to specified interpolator
            sieved_interpolation = SievedInterpolations(table, interpolator)
            ip = sieved_interpolation.interpolated_table()
        else:
            # or results are already given as `interpolator`
            ip = interpolator

        m = (0.22, 0.13, 0.1, 0.1)  # left, bottom, right, top
        w, h = 1 - m[0] - m[2], 1 - m[1] - m[3]
        h1 = h * 0.65

        fig = matplotlib.pyplot.figure(figsize=(6.4, 9.05))
        ax1 = fig.add_axes(
            (m[0] - 0.08, m[1] + (h - h1), w + 0.08, h1), projection="3d"
        )
        ax2 = fig.add_axes((m[0], m[1], w - 0.02, h - h1 * 1.07))

        self.draw_interpolation(ax1, table, ip)
        self.draw_badness(ax2, table, ip)
        return fig

    def draw_plot(self, table, interpolator):
        # type: (Table, Union[AbstractInterpolator, DataFrame])->None
        if not self.pdf:
            logger.warning("No PDF object to write.")
            return
        fig = self.plot(table, interpolator)
        self._save(fig)
