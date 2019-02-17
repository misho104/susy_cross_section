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

A command line script ``susy-xs-get`` is provided by this package.
For example, with using a keyword ``13TeV.n2x1+.wino``, you can get the production cross sections of neutralino--chargino pair at 13 TeV LHC, :math:`\sigma_{\mathrm{13TeV}}(pp\to \tilde\chi_2^0\tilde\chi_1^+)`:

.. code-block:: console

   $ susy-xs-get 13TeV.n2x1+.wino 500
   (32.9 +2.7 -2.7) fb

   $ susy-xs-get 13TeV.n2x1+.wino 513.3
   (29.4 +2.5 -2.5) fb

Here, as you may guess, the neutralino :math:`\tilde\chi_2^0` and the chargino :math:`\tilde\chi_1^+` are assumed to be wino-like and degenerate in mass: they are 500 GeV in the first command, while 513.3 GeV in the second command.

The keyword ``13TeV.n2x1+.wino`` is aliased to a grid data in this package; you may check the information by

.. code-block:: console

   $ susy-xs-get 13TeV.n2x1+.wino

   Usage: susy-xs-get [OPTIONS] 13TeV.n2x1+.wino M_WINO

     M_WINO in the unit of GeV

     --name=xsec (default)      unit: [fb]

   --------------------------------------------------------------------------------
   [Document]
     title: NLO-NLL wino-like chargino-neutralino (N2C1) cross sections
     authors: LHC SUSY Cross Section Working Group
     calculator: resummino
     source: https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVn2x1wino
     version: 2017-06-15
   [Attributes]
     collider : pp-collider with ECM=13TeV
     order: NLO+NLL with PDF=Envelope by LHC SUSY Cross Section Working Group
   [Processes]
     p p > wino0 wino+


Here, you see that this grid data ``13TeV.n2x1+.wino`` accepts one argument ``M_WINO``, in the unit of GeV, and returns ``xsec`` in the unit of fb.
Below the horizontal line, the information of the grid data is collected, including the provider, source, and physical attributes as well as included processes.
More information is available by ``susy-xs-get --help``.

Another script ``susy-xs-show`` allows you to browse the grid data itself:

.. code-block:: console

   # susy-xs-show 13TeV.n2x1+.wino

   ================================================================================
   xsec [fb]
   --------------------------------------------------------------------------------
                  value        unc+        unc-
   m_wino
   100     13895.100000  485.572000 -485.572000
   125      6252.210000  222.508000 -222.508000
   150      3273.840000  127.175000 -127.175000
   175      1890.260000   80.630600  -80.630600
   ...
   500        32.913500    2.734430   -2.734430
   525        26.602800    2.299570   -2.299570
   ...

This command is mainly for a debug-use, e.g., when you want to read-in your own data by this package; here you may notice that the above-shown result at 500 GeV is simply taken from the grid data, while that an interpolation is performed to get the cross section of 513.3 GeV wino.


Use as a package
----------------

If you want to use the values in your codes, or if you want to customize the interpolation algorithm, you will import this package into your Python codes.

