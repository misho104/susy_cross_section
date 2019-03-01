Quick Start
===========

Install and uninstall
---------------------

This package requires Python with version 2.7, 3.5 or above with `!pip` package manager.
You may check the versions by

.. code-block:: console

   $ python -V
   Python 3.6.7
   $ pip -V
   pip 19.0.3

With the set-up, you can simply install this package via PyPI:

.. code-block:: console

   $ pip install susy-cross-section             # for install
   $ pip install --upgrade susy-cross-section   # or for upgrade

   Collecting susy-cross-section
   ...
   Successfully installed susy-cross-section-(version)

You can also instantly uninstall this package by

.. code-block:: console

   $ pip uninstall susy-cross-section


Run command-line script
-----------------------

This package provides a command line script ``susy-xs``.
With using a keyword ``13TeV.n2x1+.wino``, you can get the production cross sections of neutralino--chargino pair at 13 TeV LHC, :math:`\sigma_{\mathrm{13TeV}}(pp\to \tilde\chi_2^0\tilde\chi_1^+)`:

.. code-block:: console

   $ susy-xs get 13TeV.n2x1+.wino 500
   (32.9 +2.7 -2.7) fb

   $ susy-xs get 13TeV.n2x1+.wino 513.3
   (29.4 +2.5 -2.5) fb

   $ susy-xs get 13TeV.n2x1+.wino
   Usage: get [OPTIONS] 13TeV.n2x1+.wino M_WINO
       Parameters: M_WINO   [unit: GeV]
       Table-specific options: --name=xsec   [unit: fb]  (default)

Here, as you may guess, the neutralino :math:`\tilde\chi_2^0` and the chargino :math:`\tilde\chi_1^+` are assumed to be wino-like and degenerate in mass: they are 500 GeV in the first command, while 513.3 GeV in the second command.
As shown in the third command, calling ``get`` sub-command without the mass parameter shows a short help, where you can see ``13TeV.n2x1+.wino`` accepts one argument ``M_WINO`` in the unit of GeV and by default returns ``xsec`` in the unit of fb.

For more information, you may run ``show`` sub-command:

.. code-block:: console

   $ susy-xs show 13TeV.n2x1+.wino

   ------------------------------------------------------------------------
   TABLE "xsec" (unit: fb)
   ------------------------------------------------------------------------
                  value        unc+        unc-
   m_wino
   100     13895.100000  485.572000  485.572000
   125      6252.210000  222.508000  222.508000
   150      3273.840000  127.175000  127.175000
   ...              ...         ...         ...
   475        41.023300    3.288370    3.288370
   500        32.913500    2.734430    2.734430
   525        26.602800    2.299570    2.299570
   ...              ...         ...         ...
   1950        0.005096    0.001769    0.001769
   1975        0.004448    0.001679    0.001679
   2000        0.003892    0.001551    0.001551

   [77 rows x 3 columns]

   collider: pp-collider, ECM=13TeV
   calculation order: NLO+NLL
   PDF: Envelope by LHC SUSY Cross Section Working Group
   included processes:
     p p > wino0 wino+

   ------------------------------------------------------------------------
   title: NLO-NLL wino-like chargino-neutralino (N2C1) cross sections
   authors: LHC SUSY Cross Section Working Group
   calculator: resummino
   source: https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVn2x1wino
   version: 2017-06-15
   ------------------------------------------------------------------------


Here, you see the ``xsec`` grid table followed by physical parameters and documental information.
You may also notice that the above-shown result at 500 GeV is simply taken from the grid data, while that an interpolation is performed to get the cross section of 513.3 GeV wino.

You can list-up all the available tables, or search for a table you want, by ``list`` sub-command:

.. code-block:: console

   $ susy-xs list  # to list up all the (tagged) tables.
   13TeV.n2x1-.wino       lhc_susy_xs_wg/13TeVn2x1wino_envelope_m.csv
   13TeV.n2x1+.wino       lhc_susy_xs_wg/13TeVn2x1wino_envelope_p.csv
   13TeV.n2x1+-.wino      lhc_susy_xs_wg/13TeVn2x1wino_envelope_pm.csv
   13TeV.slepslep.ll      lhc_susy_xs_wg/13TeVslepslep_ll.csv
   13TeV.slepslep.maxmix  lhc_susy_xs_wg/13TeVslepslep_maxmix.csv
   13TeV.slepslep.rr      lhc_susy_xs_wg/13TeVslepslep_rr.csv
   ...

   $ susy-xs list 7TeV  # to show tables including '7TeV' in its key or paths.
   7TeV.gg.decoup  nllfast/7TeV/gdcpl_nllnlo_mstw2008.grid
   7TeV.gg.high    nllfast/7TeV/gg_nllnlo_hm_mstw2008.grid
   7TeV.gg         nllfast/7TeV/gg_nllnlo_mstw2008.grid
   ...
   7TeV.ss10       nllfast/7TeV/ss_nllnlo_mstw2008.grid
   7TeV.st         nllfast/7TeV/st_nllnlo_mstw2008.grid

   $ susy-xs list 8t decoup
   8TeV.gg.decoup    nllfast/8TeV/gdcpl_nllnlo_mstw2008.grid
   8TeV.sb10.decoup  nllfast/8TeV/sdcpl_nllnlo_mstw2008.grid

Then you will run, for example,

.. code-block:: console

   $ susy-xs get 8TeV.gg.decoup
   Usage: get [OPTIONS] 8TeV.gg.decoup MGL
       Parameters: MGL   [unit: GeV]
       Table-specific options: --name=xsec_lo   [unit: pb]
                               --name=xsec_nlo  [unit: pb]
                               --name=xsec      [unit: pb]  (default)

   $ susy-xs get 8TeV.gg.decoup --name=xsec_lo 1210
   (0.00207 +0.00100 -0.00065) pb
   $ susy-xs get 8TeV.gg.decoup --name=xsec 1210
   (0.00325 +0.00055 -0.00051) pb

More information is available with ``--help`` options:

.. code-block:: console

   $ susy-xs --help
   $ susy-xs get --help
   $ susy-xs show --help
   $ susy-xs list --help


Use as a package
----------------

The above results are obtained also in your Python code.
For example,

.. code-block:: python

   from susy_cross_section import utility
   from susy_cross_section.table import File, Table
   from susy_cross_section.interp.interpolator import Scipy1dInterpolator

   grid_path, info_path = utility.get_paths("13TeV.n2x1+.wino")
   file = File(grid_path, info_path)

   document = file.info.document
   print(document)

   xsec_table = file["xsec"]
   xsec_attr = xsec_table.attributes
   print(xsec_attr.formatted_str())

will show the documents and attributes, and you may interpolate the table by

.. code-block:: python

   interpolator = Scipy1dInterpolator(axes="loglog", kind="linear")
   xs = interpolator.interpolate(xsec_table)
   print(xs(500), xs.fp(500), xs.fm(500), xs.unc_p_at(500), xs.unc_m_at(500))
   print(xs.tuple_at(513.3))

The output will be something like this, which reproduces the above-obtained results:

.. code-block:: python

   32.9135    35.6479    30.1791    2.7344     -2.7344
   (array(29.3516), 2.4916, -2.4916)

Note that the interpolator is `Scipy1dInterpolator` with ``linear`` option in log-log axes.
You may use another interpolator, such as PCHIP interpolator in log-log axes, by

.. code-block:: python

   pchip = Scipy1dInterpolator(axes="loglog", kind="pchip").interpolate(xsec_table)
   print(pchip.tuple_at(500))
   print(pchip.tuple_at(513.3))

The output will be:

.. code-block:: python

   (array(32.9135), 2.7344, -2.7344)
   (array(29.3641), 2.4932, -2.4932)

The results for 500 GeV is the same because it is on the grid and without interpolation, but the values for 513.3 GeV are slightly different from the previous ones.

More information is available in `API references`_.

.. _API references:
      api_reference
