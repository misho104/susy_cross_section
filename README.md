[![Build Status](https://api.travis-ci.org/misho104/susy_cross_section.svg?branch=master)](https://travis-ci.org/misho104/susy_cross_section)
[![Coverage Status](https://coveralls.io/repos/github/misho104/susy_cross_section/badge.svg?branch=master)](https://coveralls.io/github/misho104/susy_cross_section?branch=master)
[![Doc Status](http://readthedocs.org/projects/susy-cross-section/badge/)](https://susy-cross-section.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/susy-cross-section.svg)](https://badge.fury.io/py/susy-cross-section)
[![License: MIT](https://img.shields.io/badge/License-MIT-ff25d1.svg)](https://github.com/misho104/susy_cross_section/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

[susy_cross_section](https://github.com/misho104/susy_cross_section): Table-format cross-section data handler
=============================================================================================================

A Python package for [cross section tables](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections) and interpolation.

Quick Start
-----------

This package supports Python 2.7 and 3.5+.

Install simply via PyPI and use a script as:

```console
$ pip install susy-cross-section
$ susy-xs get 13TeV.n2x1+.wino 500
(32.9 +2.7 -2.7) fb
$ susy-xs get 13TeV.n2x1+.wino 513.3
(29.4 +2.5 -2.5) fb
```

which gives the 13 TeV LHC cross section to wino-like neutralino-chargino pair-production (`p p > n2 x1+`), etc.
The values are taken from [LHC SUSY Cross Section Working Group](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVn2x1wino#Envelope_of_CTEQ6_6_and_MSTW_AN1) with interpolation if needed.

To see more information, you will use `show` sub-command, which displays the cross-section table with physical attributes.

```console
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
```

You may also notice that the above value for 513.3GeV is obtained by interpolating the grid data.

You can list all the available tables, or search for tables you want, by `list` sub-command:

```console
$ susy-xs list
13TeV.n2x1-.wino       lhc_susy_xs_wg/13TeVn2x1wino_envelope_m.csv
13TeV.n2x1+.wino       lhc_susy_xs_wg/13TeVn2x1wino_envelope_p.csv
13TeV.n2x1+-.wino      lhc_susy_xs_wg/13TeVn2x1wino_envelope_pm.csv
13TeV.slepslep.ll      lhc_susy_xs_wg/13TeVslepslep_ll.csv
13TeV.slepslep.maxmix  lhc_susy_xs_wg/13TeVslepslep_maxmix.csv
13TeV.slepslep.rr      lhc_susy_xs_wg/13TeVslepslep_rr.csv
...

$ susy-xs list 7TeV
7TeV.gg.decoup  nllfast/7TeV/gdcpl_nllnlo_mstw2008.grid
7TeV.gg.high    nllfast/7TeV/gg_nllnlo_hm_mstw2008.grid
7TeV.gg         nllfast/7TeV/gg_nllnlo_mstw2008.grid
...
7TeV.ss10       nllfast/7TeV/ss_nllnlo_mstw2008.grid
7TeV.st         nllfast/7TeV/st_nllnlo_mstw2008.grid

$ susy-xs list 8t decoup
8TeV.gg.decoup    nllfast/8TeV/gdcpl_nllnlo_mstw2008.grid
8TeV.sb10.decoup  nllfast/8TeV/sdcpl_nllnlo_mstw2008.grid
```

and run for it:

```console
$ susy-xs get 8TeV.sb10.decoup 1120
(0.00122 +0.00019 -0.00019) pb
```

For more help, try to run with `--help` option.

```console
$ susy-xs --help
Usage: susy-xs [OPTIONS] COMMAND [ARGS]...
...

$ susy-xs get --help
Usage: susy-xs get [OPTIONS] TABLE [ARGS]...
...
```

You can uninstall this package as simple as

```console
$ pip uninstall susy-cross-section
Uninstalling susy-cross-section-x.y.z:
   ...
Proceed (y/n)?
```

Introduction
------------

Production cross sections are the most important values for high-energy physics collider experiments.
Many collaborations publish their cross-section tables, calculated in various tools or schemes, which are available on the WWW.
For SUSY scenarios, the values provided by [LHC SUSY Cross Section Working Group](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections) are the most famous source of the "nominal" cross section expectation for the LHC, while [NNLL-fast](https://www.uni-muenster.de/Physik.TP/~akule_01/nnllfast/) collaboration publishes those for colored process at the very high precision.

However, these results are provided in various format; for example, some are in HTML with absolute combined symmetric uncertainties, and others are in CSV files with relative asymmetric uncertainties.

This package `susy_cross_section` is provided to handle those data regardless of their format.
This package reads any table-like grid files with help of [pandas](https://pandas.pydata.org/) DataFrame, and interpret any format of uncertainties once an annotation file  (`info` files) written in JSON format is provided, which allows one to interpolate the grid easily, e.g., by using [scipy.interpolate](https://docs.scipy.org/doc/scipy/reference/interpolate.html) package.

For simpler use-case, a command-line script `susy-xs` is provided, with which one can get the cross section in several simple scenarios.
For more customization, you can use this package from your own code with more detailed interpolator options (linear-interpolation, loglog-spline-interpolation, etc.) or with your interpolator.

Document
--------

The document is provided on [readthedocs.io](https://susy-cross-section.readthedocs.io), together with [API references](https://susy-cross-section.readthedocs.io/en/latest/api_reference.html).
A [PDF file](https://github.com/misho104/susy_cross_section/blob/master/docs/doc.pdf) is also distributed with this package.

License and Citation Policy
---------------------------

The program codes included in this repository are licensed by [Sho Iwamoto / Misho](https://www.misho-web.com) under [MIT License](https://github.com/misho104/SUSY_cross_section/blob/master/LICENSE).

The non-program-code documents are licensed by [Sho Iwamoto / Misho](https://www.misho-web.com) under [CC BY-NC 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/) License.

Original cross-section data is distributed by other authors, including

* [LHC SUSY Cross Section Working Group](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections).
* [NNLL-fast](https://www.uni-muenster.de/Physik.TP/~akule_01/nnllfast/)

Full list of references are shown in [citations.pdf](https://github.com/misho104/susy_cross_section/blob/master/contrib/citations.pdf) distributed with this package, where you will find the citation policy for this package.
