[![Build Status](https://api.travis-ci.org/misho104/susy_cross_section.svg?branch=master)](https://travis-ci.org/misho104/susy_cross_section)
[![Coverage Status](https://coveralls.io/repos/github/misho104/susy_cross_section/badge.svg?branch=master)](https://coveralls.io/github/misho104/susy_cross_section?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-ff25d1.svg)](https://github.com/misho104/susy_cross_section/blob/master/LICENSE)

[susy_cross_section](https://github.com/misho104/susy_cross_section): Table-format cross-section data handler
=============================================================================================================

A Python package for [cross section tables](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections) and interpolation.

Quick Start
-----------

This package supports Python 2.7 and 3.5+.

Install simply via PyPI and use a script as:

```console
$ pip install susy-cross-section
$ susy-xs-get 13TeV.n2x1+.wino 500
(32.9 +2.7 -2.7) fb
$ susy-xs-get 13TeV.n2x1+.wino 513.3
(29.4 +2.5 -2.5) fb
```

which gives the 13 TeV LHC cross section to wino-like neutralino-chargino pair-production (`p p > n2 x1+`), etc.
The values are taken from [LHC SUSY Cross Section Working Group](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections13TeVn2x1wino#Envelope_of_CTEQ6_6_and_MSTW_AN1) with interpolation if needed.

You can find a list of supported processes in [susy_cross_section/config.py](https://github.com/misho104/susy_cross_section/blob/master/susy_cross_section/config.py).
It is also straight forward to parse your own table files once you provide `.info` files as you find in [susy_cross_section/data/](https://github.com/misho104/susy_cross_section/tree/master/susy_cross_section/data/).

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
There are many sources for the values, evaluated in various tools or schemes.
For SUSY scenarios, the values provided by [LHC SUSY Cross Section Working Group](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections) are the most famous source of the "nominal" cross section expectation.
However, their results as well as results provided in other references are not in machine-readable format and the data are provided in various format.

This package provides a module `susy_cross_section` to handle those data.
Any table-like files can be interpreted and read as a [https://pandas.pydata.org/](pandas) DataFrame object, once an annotation file (`info` files in JSON format) is provided, so that one can easily interpolate the grid by, e.g., [scipy.interpolate](https://docs.scipy.org/doc/scipy/reference/interpolate.html).

For simpler use-case, a command-line script `susy-xs-get` is provided, with which one can get the cross section in several simple scenarios.

Several data tables are included in this package, which is taken from, e.g., [LHC SUSY Cross Section Working Group](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections).
In addition, one can use their own files by writing annotations, so that they interpolate their data with pre-installed interpolator.

More information to use as a Python package will be given in API references (to be written), and to use as a script can be found in their help:

```console
$ susy-xs-get --help
Usage: susy-xs-get [OPTIONS] TABLE ARGS...

  Interpolate cross-section data using the standard scipy interpolator (with
  log-log axes).

Options:
  ...
```

License
-------

The program codes included in this repository are licensed by [Sho Iwamoto / Misho](https://www.misho-web.com) under [MIT License](https://github.com/misho104/SUSY_cross_section/blob/master/LICENSE).

Original cross-section data is distributed by other authors, including

* [LHC SUSY Cross Section Working Group](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections).

References (original data)
--------------------------

* https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections

* C. Borschensky, M. Krämer, A. Kulesza, M. Mangano, S. Padhi, T. Plehn, X. Portell,
  *Squark and gluino production cross sections in pp collisions at \sqrt(s) = 13, 14, 33 and 100 TeV,*
  [Eur. Phys. J. **C74** (2014) 12](https://doi.org/10.1140/epjc/s10052-014-3174-y)
  [[arXiv:1407.5066](http://arxiv.org/abs/1407.5066)].

* M. Krämer, A. Kulesza, R. Leeuw, M. Mangano, S. Padhi, T. Plehn, X. Portell,
  *Supersymmetry production cross sections in pp collisions at sqrt{s} = 7 TeV,*
  [arXiv:1206.2892](https://arxiv.org/abs/1206.2892).

* NNLL-fast: https://www.uni-muenster.de/Physik.TP/~akule_01/nnllfast/

* W. Beenakker, C. Borschensky, M. Krämer, A. Kulesza, E. Laenen,
  *NNLL-fast: predictions for coloured supersymmetric particle production at the LHC with threshold and Coulomb resummation,*
  [JHEP **1612** (2016) 133](https://doi.org/10.1007/JHEP12(2016)133)
  [[arXiv:1607.07741](https://arxiv.org/abs/1607.07741)].
