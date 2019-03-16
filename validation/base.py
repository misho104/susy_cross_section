"""Base classes and utility functions for validators."""

import logging
import pathlib
from typing import Any, List, Optional, Sequence, Union

import matplotlib.pyplot
import matplotlib.style
import numpy
from matplotlib.backends.backend_pdf import PdfPages

from susy_cross_section.table import Table

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

PathLike = Union[str, pathlib.Path]
LabelSpec = Union[bool, str]


class BaseValidator:
    """Base class for validators."""

    @staticmethod
    def split_interval(seq, n=4, log=False):
        # type: (Sequence[float], int, bool)->List[float]
        """Split each interval of given sequence to multiple intervals.i.

        Parameters
        ----------
        seq: List[numpy.float]
            A list of numbers to be fine-sampled.
        n: int
            The number of points to be inserted in each interval.
        log: bool
            Whether to insert in log-scale or not.
        """
        if log:
            return numpy.exp(BaseValidator.split_interval(numpy.log(seq)))
        return numpy.concatenate(
            [numpy.linspace(i, j, n, endpoint=None) for i, j in zip(seq, seq[1:])]
            + [seq[-1:]]
        )

    def __init__(self, output=None):
        # type: (Optional[Union[PdfPages, PathLike]])->None
        self._pdf_to_close = False
        if isinstance(output, PdfPages):
            self.pdf = output
        elif isinstance(output, str) or isinstance(output, pathlib.Path):
            self.pdf = PdfPages(str(output))
            self._pdf_to_close = True
        else:
            self.pdf = None

    def __del__(self):
        """Close the pdf as a destructor."""
        if self._pdf_to_close:
            self.pdf.close()
            self.pdf = None
            self._pdf_to_close = False

    def _save(self, fig):
        # type: (matplotlib.figure.Figure)->None
        if self.pdf:
            self.pdf.savefig(fig)

    @staticmethod
    def label_with_unit(text, unit=None):
        # type: (str, Any)->str
        """Return a text with unit if provided."""
        return text + (" [{}]".format(unit) if unit else "")

    @staticmethod
    def set_labels(ax, table, x=True, y=True, title=""):
        # type: (matplotlib.axes.Axes, Table, LabelSpec, LabelSpec, str)->None
        """Set the axes labels according to the table.

        Parameters
        ----------
        ax: matplotlib.Axes
            Axes object to be decorated.
        table: Table
            A Table object linked to a FileInfo.
        x: str or bool
            The specification for x-axis.
        y: str
            The specification for y-axis.
        title: str
            Title string formatted with the table information.
        """
        if not table.file:
            logger.warning("set_labels failed because of missing information.")
            return

        if title:
            attrs = {"file_name": table.file.table_path.name}
            ax.set_title(title.format(**attrs))

        x_name = x if isinstance(x, str) else table.index.names[0] if x else ""
        if x_name:
            try:
                x_unit = table.file.info.get_column(x_name).unit
            except KeyError:
                x_unit = ""
            ax.set_xlabel(BaseValidator.label_with_unit(x_name, x_unit))

        y_name = y if isinstance(y, str) else table.name if y else ""
        if y_name:
            try:
                y_unit = table.file.info.get_column(y_name).unit
            except KeyError:
                y_unit = ""
            ax.set_ylabel(BaseValidator.label_with_unit(y_name, y_unit))

    @staticmethod
    def set_labels_3d(ax, table, x=True, y=True, z="xsec", title=""):
        # type: (matplotlib.axes.Axes, Table, LabelSpec, LabelSpec, str, str)->None
        """Set the 3d axes labels similarly to set_labels() method."""
        if not table.file:
            logger.warning("set_labels failed because of missing information.")
            return
        if y is True and len(table.index.names) >= 2:
            y_name = table.index.names[1]
        else:
            y_name = y or ""
        BaseValidator.set_labels(ax, table, x, y_name, title)

        z_name = z if isinstance(z, str) else table.name if z else ""
        if z_name:
            try:
                z_unit = table.file.info.get_column(z_name).unit
                ax.set_zlabel(BaseValidator.label_with_unit(z_name, z_unit))
            except KeyError:
                pass

    def compare(self, table, nllfast_cache_key=None):
        # type: (Table, Optional[str])->None
        """Validate by comparing several interpolators."""
        raise NotImplementedError

    def sieve(self, table):
        # type: (Table)->None
        """Validate by sieved-interpolation method."""
        raise NotImplementedError
