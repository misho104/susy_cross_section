Usage: as a Python package
==========================

.. graphviz::
   :caption: Conceptual structure of data and classes.

   digraph class {
     rankdir="LR";
     {
       rank=same;
       File [shape=box];
       filedata [label="pandas.DataFrame"];
     };
     {
       rank=same;
       Table [shape=record; label="<1>Table|<2>Table|..."]
       FileInfo [shape=box]
       ColumnInfo [shape=none; label=<<table BORDER="0" CELLBORDER="1" CELLSPACING="0"><tr><td>ColumnInfo</td></tr><tr><td>ColumnInfo</td></tr><tr><td>...</td></tr></table>>];
     }
     {
       rank=same;
       tabledata [label="pandas.DataFrame"]
       ParameterInfo [shape=record; label="ParameterInfo|ParameterInfo|..."]
       ValueInfo [shape=record; label="ValueInfo|ValueInfo|..."]
       CrossSectionAttributes [shape=box]
     };
     File->Table [label=".tables (dict)"];
     File->filedata [label="                        .raw_data"];
     File->FileInfo [label=".info"]
     Table:1->CrossSectionAttributes [label=".attributes"]
     Table:1->tabledata[label="._df"]
     FileInfo->ValueInfo [label="values (list)"];
     FileInfo->ParameterInfo [label="parameters (list)"];
     FileInfo->ColumnInfo:1 [label="columns (list)"];
   }

Grid-data file and Info file
----------------------------

The fundamental objects of this package are `File` and `Table` classes, representing the files and the cross-section grid tables, respectively.
A `File` instance carries two files as paths: `!File.table_path` for grid-data file and `!File.info_path`.
A grid-data file contains a table representing one or more cross sections.
The content of a grid-data file is read and parsed by `pandas.read_csv`, which can parse most of table-format files [#dsv]_ with a proper `!reader_options` specified in the "info" file.
The resulting `pandas.DataFrame` object is stored as-is in `!File.raw_table` for further interpretation.

.. [#dsv] Parsable formats include comma-separated values (CSV), tab-separated values (TSV), and space-separated values (SSV); in addition, fixed-width formatted tables are usually parsable.

A "info" file corresponds `FileInfo` instance and is provided in JSON format :cite:`json`.
It has data for `ColumnInfo`, `ParameterInfo`, and `ValueInfo` objects in addition to `!reader_options`.
Those three types of information is used to interpret the `!File.raw_table` data.
Detailed specification of "info" files are described below.

One grid table has multiple columns, where the name and unit of each column is specified by `ColumnInfo`.
Some columns are "parameters" for cross sections, such as the mass of relevant particles, which are specified by `ParameterInfo`.
Other columns are for "values" and `ValueInfo` is used to define the values.
`ValueInfo` uses one column as a central value, and one or more columns as uncertainties, which can be relative or absolute and symmetric or asymmetric.
Multiple columns for an uncertainty are combined in quadrature, i.e., :math:`\sigma_1\oplus\sigma_2 := \sqrt{\sigma_1^2 + \sigma_2^2}`.

For each `ValueInfo`, the interpreter constructs one :class:`~pandas.DataFrame` object.
It is parameterized by :py:class:`~pandas.Index` or :py:class:`~pandas.MultiIndex` and three columns, ``value``, ``unc+``, and ``unc-``, respectively containing the cross-section central value, positive combined absolute uncertainty, and (the absolute values of) negative combined absolute uncertainty.
The :class:`~pandas.DataFrame` is wrapped by `Table` class and stored in `!File.tables` (:typ:`dict`) with keys being the ``name`` of the value columns.

This is an example of data handling:

.. code-block:: python

   from susy_cross_section import utility
   from susy_cross_section.table import File, Table

   grid_path, info_path = utility.get_paths("13TeV.n2x1+.wino")
   file = File(grid_path, info_path)

   xsec_table = file.tables["xsec"]

Here an utility function `get_paths` is used to look-up paths for the key ``13TeV.n2x1+.wino`` and from the passes a `File` instance is constructed.
Then a table with the column name ``xsec`` is read from the `!tables` dictionary.

Interpolation
-------------

The table interpolation is handled by `susy_cross_section.interp` subpackage.
This package first performs axes transformation using `axes_wrapper` module, and then use one of the interpolators defined in `interpolator` module.
Detail information is available in the API document of each module.

The cross-section data with one mass parameter are usually fit well by a negative power of the mass, i.e., :math:`\sigma(m)\propto m^{-n}`.
For such cases, interpolating the function by piece-wise lines in log-log axes would work well, which is implemented as

.. code-block:: python

   from susy_cross_section.interp.interpolator import Scipy1dInterpolator

   xs = Scipy1dInterpolator(axes="loglog", kind="linear").interpolate(xsec_table)
   print(xs(500), xs.fp(500), xs.fm(500), xs.unc_p_at(500), xs.unc_m_at(500))

One can implement more complicated interpolators by extending `AbstractInterpolator`.

A proposal for INFO file format
-------------------------------

An info file is a JSON file and its data is one dict object.
The dict has six keys: ``document``, ``attributes`` (optional), ``columns``, ``reader_options`` (optional), ``parameters``, and ``values``.

``document`` as :typ:`dict(str, str)`:

  This dictionary may contain any values and no specification is given, but the content should be used only for documental purposes; i.e., programs should not change their behavior by the content of ``document``.
  Data for such purposes should be stored not in ``document`` but in ``attributes``.

  Possible keys are: ``title``, ``authors``, ``calculator``, ``source``, and ``version``.

``attributes`` as :typ:`dict(str, str)`:

  This dictionary contains *the default values* for `CrossSectionAttributes`, which is attached to each values.
  These default values are overridden by the ``attributes`` defined in respective values.

  `CrossSectionAttributes` stores, contrary to ``document``, non-documental information, based on which programs may change their behavior.
  Therefore the content must be neat and in machine-friendly formats.
  The proposed keys are: ``processes``, ``collider``, ``ecm``, ``order``, and ``pdf_name``.
  For details, see the API document of `CrossSectionAttributes`.

``columns`` as a list of :typ:`dict(str, str)`:

  This is a list of dictionaries used to construct `ColumnInfo`; the :m:`n`-th element defines :m:`n`-th column in the grid-data file.
  The length of this list thus matches the number of the columns.
  Each dictionary must have two keys: ``name`` and ``unit``, respectively specify the name and unit of the column.
  The names must be unique in one file.
  For dimension-less column, ``unit`` is an empty string.

``reader_options`` as :typ:`dict(str, Any)`:

  This dictionary is directly passed to :func:`read_csv` and used as the keyword arguments.

``parameters`` as a list of :typ:`dict(str, Any)`:

  This list defines the parameters for indexing.
  Each element is a dictionary, which has two keys ``column`` and ``granularity`` and constructs a `ParameterInfo` object.
  The value for ``column`` is one of the ``name`` of ``columns``.
  The value for ``granularity`` is a number used to quantize the parameter grid; for details see the API document of `ParameterInfo`.

``values`` as a list of dictionary:

  This list defines the cross-section values.
  Each element is a dictionary and constructs a `ValueInfo` object.
  The dictionary has possibly the keys ``column``, ``unc``, ``unc+``, ``unc-``, and ``attributes``.
  Among these keys, ``column`` is mandatory and corresponding value must be one of the ``name`` of ``columns``, where the column is used as the central value of cross-section.
  The value for ``attributes`` is a dictionary :typ:`dict(str, Any)`. It overrides the file-wide default values (explained above) to construct a `CrossSectionAttributes`.

  The other three keys are used to specify uncertainties.
  ``unc`` specifies symmetric uncertainty, while a pair of ``unc+`` and ``unc-`` specifies asymmetric uncertainty; ``unc`` will not be present together with ``unc+`` or ``unc-``.
  Each value of ``unc``, ``unc+``, and ``unc-`` is *a list of dictionaries*, :typ:`list(dict(str, str))`.
  Each element of the list, being a dictionary with two keys ``column`` and ``type``, describes one source of uncertainties.
  The value for ``column`` is one of the ``name`` of ``columns``, or a list of the names.
  If one name is specified, the column is used as the source.
  If a list is specified, the column with the largest value among them is used as the source.
  The value for ``type`` specifies the type of uncertainty; possible options and further details are found in the API document of `ValueInfo`.


How to use own tables
---------------------

Users may use this package to handle their own cross-section grid tables, once they provide an INFO file.
The procedure is summarized as follows.

1. Find proper `!reader_options` to read the table.

   This package uses :func:`pandas.read_csv` to read the grid table, for which proper options should be specified.
   The following script may be useful to find the proper option for your table.
   Possible keys for `!reader_options` are found in the API document of :func:`pandas.read_csv`.

   .. code-block:: python

      import pandas

      reader_options = {
          "sep": ";",
          "skiprows": 1
      }
      grid_path = "mydata/table_grid.txt"
      data_frame = pandas.read_csv(grid_path, **reader_options)
      print(data_frame)

2. Write the INFO file.
   One should be careful especially of "type" of uncertainties and "unit" of columns.

3. Verify whether the file is correctly read.
   :ref:`show sub-command <cmd_show>` is useful for this purpose; for example,


   .. code-block:: console

      $ susy-xs show mydata/table_grid.txt mydata/table_grid.info

   After verifying with show sub-command, users can use :ref:`get sub-command <cmd_get>`, or read the data in their code as:

   .. code-block:: python

      my_grid = File("mydata/table_grid.txt", "mydata/table_grid.info")
