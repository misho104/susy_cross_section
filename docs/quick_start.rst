Quick Start
===========

Install and uninstall
---------------------

You can simply install (or upgrade) via PyPI:

.. code-block:: console

   $ pip install susy-cross-section             # install
   $ pip install --upgrade susy-cross-section   # upgrade

You can also instantly uninstall this package by

.. code-block:: console

   $ pip uninstall susy-cross-section


Use as scripts
--------------

A command line script ``susy-xs`` is provided by this package.
For example, with using a keyword ``13TeV.n2x1+.wino``, you can get the production cross sections of neutralino--chargino pair at 13 TeV LHC, :math:`\sigma_{\mathrm{13TeV}}(pp\to \tilde\chi_2^0\tilde\chi_1^+)`:

.. code-block:: console

   $ susy-xs get 13TeV.n2x1+.wino 500
   (32.9 +2.7 -2.7) fb

   $ susy-xs get 13TeV.n2x1+.wino 513.3
   (29.4 +2.5 -2.5) fb

Here, as you may guess, the neutralino :math:`\tilde\chi_2^0` and the chargino :math:`\tilde\chi_1^+` are assumed to be wino-like and degenerate in mass: they are 500 GeV in the first command, while 513.3 GeV in the second command.

The keyword ``13TeV.n2x1+.wino`` is aliased to a grid data in this package; you may check the information by

.. code-block:: console

   $ susy-xs get 13TeV.n2x1+.wino

   Usage: get [OPTIONS] 13TeV.n2x1+.wino M_WINO

       Parameters: M_WINO   [unit: GeV]

       Table-specific options: --name=xsec   [unit: fb]  (default)


Here, you see that this grid data ``13TeV.n2x1+.wino`` accepts one argument ``M_WINO``, in the unit of GeV.
By default, --name=xsec is chosen, so it will return ``xsec`` in the unit of fb.
More information is available by ``show`` command:

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
   1950        0.005096    0.001769    0.001769
   1975        0.004448    0.001679    0.001679
   2000        0.003892    0.001551    0.001551
   
   [77 rows x 3 columns]
   
   collider: pp-collider, ECM=13TeV
   calculation order: NLO+NLL
   PDF: Envelope by LHC SUSY Cross Section Working Group
   included processes:
     p p > wino0 wino+

It displays the "xsec" table with attributes, such as the colliers or the processes.
You may also notice that the above-shown result at 500 GeV is simply taken from the grid data, while that an interpolation is performed to get the cross section of 513.3 GeV wino.


Use as a package
----------------

If you want to use the values in your codes, or if you want to customize the interpolation algorithm, you will import this package into your Python codes.

