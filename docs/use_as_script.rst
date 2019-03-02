Usage: as a command-line script
===============================

The package provides one script for terminal, ``susy-xs``, which accepts the following flags and sub-commands.

- ``susy-xs --help`` gives a short help and a list of sub-commands,
- ``susy-xs --version`` returns the package version,
- ``susy-xs list`` displays a list of available table-grid data files,
- ``susy-xs show`` shows the information of a specified data file,
- ``susy-xs get`` obtains a cross section value from a table, with interpolation if necessary.

Details of these sub-commands are explained below, or available from the terminal with ``--help`` flag as, for example, ``susy-xs get --help``.


.. _cmd_list:

list
----

.. code-block:: console

   $ susy-xs list (options) (substr substr ...)


This sub-command displays a list of available cross-section tables.
If `!substr` is specified, only the tables which includes it in the table name or file paths are displayed.

By default, this command lists only the files with pre-defined table keys.
In addition to these commonly-used table grids, this package contains much more cross-section data.
One can find these additional files with an option ``--all``.

With ``--full`` option, full paths to the files are displayed, which is useful for additional operations, for example,

.. code-block:: console

   $ susy-xs list --all --full gg 7TeV CTEQ
   /Users/misho/ (...) /data/nllfast/7TeV/gg_nllnlo_cteq6.grid
   /Users/misho/ (...) /data/nllfast/7TeV/gg_nllnlo_hm_cteq6.grid

   $ susy-xs show /Users/misho/ (...) /data/nllfast/7TeV/gg_nllnlo_hm_cteq6.grid
   ------------------------------------------------------------------------
   TABLE "xsec_lo" (unit: pb)
   ------------------------------------------------------------------------
                     value          unc+          unc-
   ms   mgl
   200  200   3.400000e+02  1.411437e+02  9.385184e+01
   ...

.. _cmd_show:

show
----

.. code-block:: console

   $ susy-xs show (options) table

This sub-command shows data and information of the table specified by `!table`.
`!table` can be one of pre-defined table keys, which can be displayed by :ref:`list sub-command <cmd_list>`, or a path to grid-data file.
The displayed information includes grid-tables in the file, physical attributes associated to each of the tables, and the documenting information associated to the file.

A grid-data file is read with an associated "info" file, whose name is by default resolved by replacing the suffix of the data file to ``.info``.
One can override this default behavior with the ``--info`` option.

.. _cmd_get:

get
---

.. code-block:: console

   $ susy-xs get (options) table (args ...)

This sub-command gets a cross-section value from the table specified by `!table` and the option ``--name``, where `!args` are used as the physical parameters.
Without `!args`, this sub-command displays the meanings of `!args` and ``--name`` option, such as

.. code-block:: console

   $ susy-xs get 8TeV.gg
   Usage: get [OPTIONS] 8TeV.gg MS MGL

   Parameters: MS   [unit: GeV]
               MGL  [unit: GeV]

   Table-specific options: --name=xsec_lo    [unit: pb]
                           --name=xsec_nlo   [unit: pb]
                           --name=xsec       [unit: pb]  (default)

In this case, users are asked to specify the squark mass (which is assumed to be degenerate in this grid) as the first `!args` and gluino mass as the second `!args`, both in GeV.
It is also shown here that users can get LO and NLO cross sections by using ``-name`` option or otherwise the default ``xsec`` grid is used.
So, for example, the cross section :math:`\sigma_{8 \mathrm{TeV}}(pp\to\tilde g\tilde g)` with 1 TeV gluino and 1.2 TeV squark can be obtained by

.. code-block:: console

   $ susy-xs get 8TeV.gg 1200 1000
   (0.0126 +0.0023 -0.0023) pb

Here, the default ``xsec`` grid in the table file ``8TeV.gg`` is used.
One can check with :ref:`show sub-command <cmd_show>` that this grid is calculated by NLL-fast collaboration at the NLO+NLL order with using MSTW2008nlo68cl as the parton distribution functions (PDFs), and thus this 12.6 fb is the NLO+NLL cross section.

The value is calculated by an interpolation if necessary.
This sub-command uses linear interpolation with all the parameters and values in logarithmic scale.
For example, an interpolating function for one-parameter grid table is obtained as piece-wise lines in a log-log plot.
To use other interpolating methods, users have to use this package by importing it to their Python codes as explained in `Section 4`_.
For details, confer the API document of `susy_cross_section.interp`.

`!table` can be one of pre-defined table keys, which can be displayed by :ref:`list sub-command <cmd_list>`, or a path to grid-data file.
A grid-data file is read with an associated "info" file, whose name is by default resolved by replacing the suffix of the data file to ``.info``.
One can override this default behavior with the ``--info`` option.

Additionally, several options are provided to control the output format, which are found in the ``--help``.

.. caution::

    Theoretically, one can get cross sections for various model point by repeating this sub-command.
    However, it is not recommended since this sub-command construct an interpolating function every time.
    For such use-cases, users should use this package as a package, i.e., import this package in their Python codes, as explained in `Section 4`_.

.. _Section 4:
      use_as_package
