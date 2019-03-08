"""Validation of interpolators for 1d grid."""

import logging
from typing import Any, List, Optional, Sequence, Tuple, Union, cast

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


class OneDimValidator(BaseValidator):
    """Generator of validation plots for one-dimensional grid tables."""

    interpolators = [
        Scipy1dInterpolator(kind="linear", axes="loglog"),
        Scipy1dInterpolator(kind="spline", axes="loglog"),
        Scipy1dInterpolator(kind="akima", axes="loglog"),
        Scipy1dInterpolator(kind="pchip", axes="loglog"),
    ]
    """The interpolators to test, with first being the benchmark standard."""

    def __init__(self, output=None):
        # type: (Optional[Union[PdfPages, PathLike]])->None
        super().__init__(output=output)
        matplotlib.style.use("seaborn-whitegrid")

    def __del__(self):
        """Close the pdf as a destructor."""
        super().__del__()

    def draw_data(self, ax, table, **kwargs):
        # type: (Axes, Table, Any)->None
        """Draw the original data with uncertainty."""
        x = table.index
        y = table["value"]
        ey = (table["unc-"], table["unc+"])
        assert len(x.names) == 1
        assert len(x) == len(y) == len(ey[0]) == len(ey[1])
        k = {"fmt": "none", "elinewidth": 1, "ecolor": "black", "label": "data"}
        k.update(kwargs)
        ax.errorbar(x, y, ey, **k)

    def _build_x_y(self, table, obj):
        x_list = self.split_interval(table.index, n=9, log=False)
        if isinstance(obj, AbstractInterpolator):
            interp = obj.interpolate(table)
            y_list = [interp(x) for x in x_list]
        elif isinstance(obj, Interpolation):
            y_list = [obj(x) for x in x_list]
        else:
            x_list, y_list = zip(*obj)
        return x_list, y_list

    @staticmethod
    def _calculate_badness(table, ux, uy1, uy2):
        # type: (Table, numpy.ndarray, numpy.ndarray, numpy.ndarray)->Tuple[List[float], List[float]]
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
        uy1: numpy.ndarray
            Values corresponding to ux from an interpolator.
        uy2: numpy.ndarray
            Values corresponding to ux from another interpolator.

        Returns
        -------
        Tuple[List[float], List[float]]
            A pair of variation and badness
        """
        x_list, em, ep = (
            table.index.to_numpy(),
            numpy.abs(table["unc-"]).to_numpy(),
            table["unc+"].to_numpy(),
        )

        representative_unc = [
            min(ep[i], ep[i + 1], em[i], em[i + 1]) for i in range(0, len(x_list) - 1)
        ]  # type: List[float]

        variations = []  # type: List[float]
        badnesses = []  # type: List[float]

        for n, x in enumerate(ux):
            for x1, x2, r in zip(x_list, x_list[1:], representative_unc):
                if x1 <= x <= x2:
                    d = abs(uy2[n] - uy1[n])
                    variations.append(d / uy1[n])
                    badnesses.append(d / r)
                    break

        return variations, badnesses

    def draw_variations(self, ax, table, interp_list, **kwargs):
        # type: (Axes, Table, List[Tuple[str, AbstractInterpolator]], Any)->Tuple[float, float]
        """Plot variation among interpolators and returns the worst values."""
        label0, i0 = interp_list[0]
        ux0, uy0 = self._build_x_y(table, i0)

        variations = []  # type: List[List[float]]
        badnesses = []  # type: List[List[float]]
        for label, i in interp_list:
            f = i.interpolate(table)
            uy = numpy.array([f(x) for x in ux0])
            v, b = self._calculate_badness(table, ux0, uy0, uy)
            variations.append(v)
            badnesses.append(b)
            k = {"linewidth": 0.5, "label": label}
            k.update(kwargs)
            ax.plot(ux0, uy / uy0 - 1, **k)

        return max(max(v) for v in variations), max(max(v) for v in badnesses)

    def compare(self, table):
        # type: (Table)->None
        """Compare multiple interpolators."""
        m = (0.22, 0.13, 0.1, 0.1)  # left, bottom, right, top
        w, h = 1 - m[0] - m[2], 1 - m[1] - m[3]
        h1 = h * 0.6

        fig = matplotlib.pyplot.figure(figsize=(6.4, 9.05))
        ax1 = fig.add_axes((m[0], m[1] + (h - h1), w, h1))
        ax2 = fig.add_axes((m[0], m[1], w, h - h1), sharex=ax1)

        interp_list = [
            ("{}/{}".format(i.kind, i.axes), cast(AbstractInterpolator, i))
            for i in self.interpolators
        ]

        # first plot
        self.draw_data(ax1, table)
        for label, i in interp_list:
            ax1.plot(*(self._build_x_y(table, i)), linewidth=0.5, label=label)

        # second plot
        ep, em = table["unc+"] / table["value"], -table["unc-"] / table["value"]
        v, b = self.draw_variations(ax2, table, interp_list, label="")
        ax2.plot(table.index, ep, color="black", label="relative uncertainty of data")
        ax2.plot(table.index, em, color="black")
        ax2.plot([], [], " ", label=f"Variation={v:.2%}; Badness={b:.3}")

        # decoration
        self.set_labels(ax1, table, x=False, title="{file_name}")
        self.set_labels(ax2, table, y=f"Variation from {interp_list[0][0]}")
        ax1.set_xscale("linear")
        ax1.set_yscale("log")
        ax1.tick_params(labelbottom=False)
        ax1.legend()
        ax2.legend()
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
            self.set_labels_3d(ax, table, z="")
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
