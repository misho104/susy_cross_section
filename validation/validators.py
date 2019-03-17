"""Validation of interpolators for 1d grid."""

import logging
import pathlib
from typing import Any, List, Mapping, Optional, Sequence, Tuple, Union, cast

import matplotlib
import matplotlib.style
import numpy
import pandas
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.pyplot import cm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pandas import DataFrame

from susy_cross_section.interp.axes_wrapper import AxesWrapper
from susy_cross_section.interp.interpolator import (
    AbstractInterpolator,
    Interpolation,
    Scipy1dInterpolator,
    ScipyGridInterpolator,
)
from susy_cross_section.table import Table
from validation.base import BaseValidator, PathLike
from validation.sieve import SievedInterpolations

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

nllfast_cache_dir = pathlib.Path(__file__).parent / "contrib" / "nllfast-cache"


def choose_validator(table):
    # type: (Table)->type
    """Choose a validator based on the number of parameters."""
    n_keys = len(table.index.names)
    if n_keys == 1:
        return OneDimValidator
    elif n_keys == 2:
        return TwoDimValidator
    else:
        raise ValueError("No validation method is prepared for n_param=%d.", n_keys)


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

    def _build_x_y(self, table, obj, x_list=None):
        if x_list is None:
            x_list = self.split_interval(table.index, n=9, log=False)
        if isinstance(obj, AbstractInterpolator):
            interp = obj.interpolate(table)
            y_list = [interp(x) for x in x_list]
        elif isinstance(obj, Interpolation):
            y_list = []  # type: List[float]
            for x in x_list:
                try:
                    y_list.append(obj(x))
                except ValueError:
                    y_list.append(None)
        else:
            x_list, y_list = zip(*obj)
        return numpy.array(x_list), numpy.array(y_list)

    def draw_variations(self, ax, table, interp_list, **kwargs):
        # type: (Axes, Table, List[Tuple[str, AbstractInterpolator]], Any)->Tuple[float, float]
        """Plot variation among interpolators and returns the worst values."""
        label0, i0 = interp_list[0]
        ux0, uy0 = self._build_x_y(table, i0)

        n_interp = len(interp_list)

        variations = []  # type: List[float]
        badnesses = []  # type: List[float]
        for n, (label, interpolator) in enumerate(interp_list[1:]):
            interpolation = interpolator.interpolate(table)
            uy = numpy.array([interpolation(x) for x in ux0])
            ey = numpy.array([max(abs(interpolation.unc_m_at(x)), interpolation.unc_p_at(x)) for x in ux0])
            variation_list = (uy - uy0) / uy0
            variations.append(numpy.max(numpy.abs(variation_list)))
            badnesses.append(numpy.max(numpy.abs((uy0 - uy) / ey)))
            color = int(n / 2) if n_interp == len(self.interpolators) * 2 + 1 else n + 1
            k = {"linewidth": 0.5, "label": label, "c": cm.tab10(color)}
            k.update(kwargs)
            ax.plot(ux0, variation_list, **k)

        return numpy.max(variations), numpy.max(badnesses)

    def compare(self, table, nllfast_cache_key=None):
        # type: (Table, Optional[str])->None
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
        ax2.plot(table.index, ep, color="black", label="relative uncertainty of data")
        ax2.plot(table.index, em, color="black")
        v, b = self.draw_variations(ax2, table, interp_list, label="")

        # NLL-fast cache
        if nllfast_cache_key:
            cache = nllfast_cache_dir / (nllfast_cache_key + ".cache")
            if not cache.is_file():
                logger.warning("NLL-fast cache not found; skipped.")
            else:
                df = pandas.read_csv(cache, sep="\t", header=None, names=["m", "orig"])
                assert len(df.columns) == 2
                ip_base = interp_list[0][1].interpolate(table)
                for k, row in df.iterrows():
                    df.loc[k, "variation"] = row["orig"] / ip_base(row["m"]) - 1
                style = {"linestyle": " ", "markeredgewidth": 0, "style": "ko"}
                df.plot("m", "orig", ax=ax1, markersize=0.25, label="", **style)
                df.plot("m", "variation", ax=ax2, markersize=0.25, label="", **style)
                ax1.plot([], [], "k.", label="original interpolator")

        # decoration
        self.set_labels(ax1, table, x=False, title="{file_name}")
        self.set_labels(ax2, table, y=f"Variation from {interp_list[0][0]}")
        ax1.set_xscale("linear")
        ax1.set_yscale("log")
        ax1.tick_params(labelbottom=False)
        ax1.legend()
        ax2.plot([], [], " ", label=f"Variation={v:.2%}; Badness={b:.3}")
        ax2.legend()
        self._save(fig)

    def sieve(self, table):
        # type: (Table)->None
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

        interp_for_variation = []
        interp_for_variation.append(interp_list[0])

        # first plot
        self.draw_data(ax1, table)
        for index, (label, interp) in enumerate(interp_list):
            ips = SievedInterpolations(table, interp).interpolations
            c = cm.tab10(index)
            for ip in ips.values():
                interp_for_variation.append(("x", ip))
                ax1.plot(*(self._build_x_y(table, ip)), label=label, linewidth=0.5, c=c)
                label = ""  # to remove label for the second and later lines

        # second plot
        ep, em = table["unc+"] / table["value"], -table["unc-"] / table["value"]
        ax2.plot(table.index, ep, color="black", label="relative uncertainty of data")
        ax2.plot(table.index, em, color="black")
        v, b = self.draw_variations(ax2, table, interp_for_variation, label="")
        ax2.plot([], [], " ", label=f"Variation={v:.2%}; Badness={b:.3}")

        self.set_labels(ax1, table, x=False, title="{file_name}")
        self.set_labels(ax2, table, y=f"Variation")
        ax1.set_xscale("linear")
        ax1.set_yscale("log")
        ax1.tick_params(labelbottom=False)
        ax1.legend()
        ax2.legend()
        self._save(fig)


class TwoDimValidator(BaseValidator):
    """Validation with sieved table interpolations."""

    def __init__(self, output=None):
        # type: (Optional[Union[PdfPages, PathLike]])->None
        super().__init__(output=output)
        loglog_wrapper = AxesWrapper(["log", "log"], "log")
        self.interpolators = {
            "{}/loglog".format(k): ScipyGridInterpolator(k, axes_wrapper=loglog_wrapper)
            for k in ["linear", "spline33"]
        }  # type: Mapping[str, ScipyGridInterpolator]
        magma = matplotlib.pyplot.get_cmap("magma_r")
        cmap_array = [magma(i) for i in range(0, 24 * 12, 24)]
        self.cmap = matplotlib.colors.ListedColormap(cmap_array[1:-1])
        self.cmap.set_under(cmap_array[0])
        self.cmap.set_over(cmap_array[-1])

    def __del__(self):
        """Deconstruct this instance."""
        super().__del__()

    def draw_interpolation(self, ax, table, data):
        # type: (Axes, Table, DataFrame)->None
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
            xs, ys, ips, c="r", marker="_", s=10, label="interpolation", linewidth=0.5
        )
        self.set_labels_3d(ax, table, title="{file_name}")
        ax.legend(loc="upper right", bbox_to_anchor=(1, 0.92))
        ax.set_zlabel(r"$\log_{10}$ " + ax.get_zlabel())

    @staticmethod
    def _extend_grid(seq):
        # type: (Sequence[float])->List[float]
        r = [(x1 + x2) / 2 for x1, x2 in zip(seq, seq[1:])]
        r.insert(0, seq[0] - (seq[1] - seq[0]) / 2)
        r.append(seq[-1] + (seq[-1] - seq[-2]) / 2)
        return r

    def draw_badness(self, ax, table, data):
        # type: (Axes, Table, DataFrame)->None
        xs, ys = data.index.levels
        zs = abs(data["badness"].unstack().to_numpy())
        mesh = ax.pcolormesh(
            # note the reversed order!
            self._extend_grid(ys),
            self._extend_grid(xs),
            zs,
            cmap=self.cmap,
            vmin=0,
            vmax=1,
            linewidths=5,
        )
        bar = ax.figure.colorbar(mesh)
        bar.set_label("badness", rotation=270)
        bar.ax.yaxis.labelpad = 10
        ax.grid()
        self.set_labels_3d(ax, table, z="")

    def compare(self, table, nllfast_cache_key=None):
        # type: (Table, Optional[str])->None
        """Compare multiple interpolators."""
        fig1 = matplotlib.pyplot.figure(figsize=(6.4, 9.05))
        fig2 = matplotlib.pyplot.figure(figsize=(6.4, 9.05))
        ax1 = fig1.add_subplot(2, 1, 1, xmargin=0.3, ymargin=0.3)
        ax2 = fig1.add_subplot(2, 1, 2, xmargin=0.3, ymargin=0.3)
        ax3 = fig2.add_subplot(2, 1, 1)
        ax4 = fig2.add_subplot(2, 1, 2)

        ip = {k: v.interpolate(table) for k, v in self.interpolators.items()}

        diff_df = pandas.DataFrame()
        # nllfast_cache_key = "13TeV.gg"
        if nllfast_cache_key:
            # plots are configured for 2 interp + orig
            assert len(self.interpolators) == 2
            cache = nllfast_cache_dir / (nllfast_cache_key + ".cache")
            df = pandas.read_csv(
                cache, sep="\t", header=None, names=["m1", "m2", "orig"]
            )
            df.set_index(["m1", "m2"], inplace=True)
            assert len(df.columns) == 1
            n1, n2 = ip.keys()
            ip1, ip2 = ip.values()
            for key, _ in df.iterrows():
                ip1_tuple = ip1.tuple_at(key)
                df.loc[key, n1] = ip1_tuple[0]
                df.loc[key, "unc"] = min(abs(ip1_tuple[1]), abs(ip1_tuple[2]))
                df.loc[key, n2] = ip2(key)

            diff_df[f"{n1} vs {n2}"] = abs(df[n1] - df[n2]) / df["unc"]
            diff_df[f"orig vs {n1}"] = abs(df["orig"] - df[n1]) / df["unc"]
            diff_df[f"orig vs {n2}"] = abs(df["orig"] - df[n2]) / df["unc"]
            diff_df[f"max_diff"] = diff_df.max(axis=1)
            plots_and_columns = [
                (ax1, "max_diff"),
                (ax2, f"orig vs {n1}"),
                (ax3, f"orig vs {n2}"),
                (ax4, f"{n1} vs {n2}"),
            ]
        else:
            x_list = self.split_interval(table.index.levels[0], n=5, log=False)
            y_list = self.split_interval(table.index.levels[1], n=5, log=False)
            n1, n2 = ip.keys()
            ip1, ip2 = ip.values()
            xs, ys, zs = [], [], []  # type: List[float], List[float], List[float]
            for x in x_list:
                for y in y_list:
                    v1, ep, em = ip1.tuple_at(x, y)
                    v2 = ip2(x, y)
                    xs.append(x)
                    ys.append(y)
                    zs.append(abs(v1 - v2) / min(abs(ep), abs(em)))
            diff_df = pandas.DataFrame(
                zs, pandas.MultiIndex.from_arrays([xs, ys]), columns=[f"{n1} vs {n2}"]
            )
            plots_and_columns = [(ax1, f"{n1} vs {n2}")]

        xs, ys = [self._extend_grid(seq) for seq in diff_df.index.levels]
        for ax, k in plots_and_columns:
            zs = abs(diff_df[k].unstack().to_numpy())
            mesh = ax.pcolormesh(ys, xs, zs, cmap=self.cmap, vmin=0, vmax=1)
            # note the x/y reversed order!
            bar = ax.figure.colorbar(mesh, ax=ax)
            bar.set_label("badness", rotation=270)
            bar.ax.yaxis.labelpad = 10
            ax.grid()
            self.set_labels_3d(ax, table, z="", title=k)

        # decoration
        adj = {"left": 0.22, "bottom": 0.12, "right": 0.9, "top": 0.83, "hspace": 0.24}

        if len(plots_and_columns) == 1:
            ax2.remove()
            fig1.suptitle(f"{table.file.table_path.name}", y=0.9)
            fig1.subplots_adjust(**adj)
            self._save(fig1)
        elif len(plots_and_columns) == 4:
            fig1.suptitle(f"{table.file.table_path.name} (1/2)", y=0.9)
            fig1.subplots_adjust(**adj)
            self._save(fig1)
            fig2.suptitle(f"{table.file.table_path.name} (2/2)", y=0.9)
            fig2.subplots_adjust(**adj)
            self._save(fig2)
        else:
            raise RuntimeError

    def sieve(self, table):
        # type: (Table)->None
        for interp_name, interp in self.interpolators.items():
            sieved_interpolation = SievedInterpolations(table, interp)
            ip = sieved_interpolation.interpolated_table()

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
            ax1.title.set_text(f"{ax1.title.get_text()}/{interp_name}")
            self._save(fig)
