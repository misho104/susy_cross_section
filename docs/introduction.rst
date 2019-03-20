.. cSpell:words colliders resummation NNLO NLO Prospino NNLL NLL gluon Fuks
.. cSpell:words Beenakker Aaboud

Introduction
============

Background
----------

Collider experiments have long been the central tools to look for new physics beyond the Standard Model (SM).
The number of new physics events in colliders are given by the product of production cross section and an integrated luminosity, where the former is theoretically calculated based on a hypothesized theory and the latter is measured by the experiment collaboration with, e.g., at the ATLAS or CMS experiments at the LHC, 2%-level precision :cite:`Aaboud:2016hhf,CMS:2018elu`.
Therefore, cross sections of new physics processes are the most important values in any new-physics theory and should be calculated with similar precision.

Cross-section calculation with such precision is not a simple task because the leading order (LO) calculation, which usually includes only the tree-level contributions, will not give such precision and we have to include loop-level calculations.
Especially, when colored particles are involved in the process, the large QCD couplings worsen convergence of the perturbation series and even the next-to-leading-order (NLO) calculation may give uncertainties more than 10%, and we have to include the next-to-NLO (NNLO) diagrams and/or soft-gluon resummation.

For SUSY processes, several tools are published for precise cross-section calculations.
Prospino :cite:`Beenakker:1996ed` is one of the pioneer works.
It is upgraded to `Prospino 2`_ :cite:`ProspinoWeb`, with which we can calculate NLO cross sections of most SUSY processes within a few minutes.
For soft-gluon resummation, `Resummino`_ :cite:`Fuks:2013vua` is available, which allows us to calculate the resummation at the accuracy level of next-to-leading-log (NLL) or the next-to-NLL (NNLL).

`NNLL-fast`_ :cite:`Beenakker:2016lwe` is another type of tools for SUSY cross sections.
It provides grid data of cross sections calculated with accuracy level of approximated-NNLO plus NNLL together with an interpolator, with which users can obtain cross sections for various parameter set of simplified scenario less than a few second.
While available process are limited compared to `Prospino 2`_ or `Resummino`_ and the results suffer from uncertainties due to the interpolation, the fast calculation provided by NNLL-fast has a great advantage for new-physics studies, which usually consider a huge number of parameter sets.

Grid tables for SUSY cross sections are provided by other collaborations as well [#deepxs]_.
The most nominal set is the one provided by `LHC SUSY Cross Section Working Group`_ :cite:`LHCSUSYCSWG`, which is obtained by compiling the results from the above calculators.
They provide cross-section grid tables for various simplified models and collision energies.
However, the grid tables provided by various collaborations are (of course) in various formats.
This package `!susy_cross_section` aims to handle those grid data, including ones appearing in future, in an unified manner.

This Package
------------

`!susy_cross_section` is a Python package to handle cross-section grid tables regardless of their format.
With this package, one can import any table-like grid files as a `pandas`_ DataFrame, once an annotation file (`info` file) is provided in JSON format :cite:`json`.
Several interpolators are also provided, with which one can interpolate the grid tables to obtain the central values together with (possibly asymmetric) uncertainties.
A quick start guide is provided in `Section 2`_.

For simple use-cases, a command-line script `!susy-xs` is provided.
You can get interpolated cross sections for simplified scenarios with the sub-command `!susy-xs get` on your terminal, based on simple log-log interpolators.
More information on the script is available in `Section 3`_.

.. only:: html
    
    You can include this package in your Python code for more customization.
    For example, you may use the cross section values in your code, or interpolate the grid tables with other interpolators, including your own ones.
    `Section 4`_ of this document is devoted to such use-cases, and the full API reference of this package is provided in `Section 5`_.
    In `Section 6`_ we propose two methods to validate the interpolation procedure.

.. only:: latex
    
    You can include this package in your Python code for more customization.
    For example, you may use the cross section values in your code, or interpolate the grid tables with other interpolators, including your own ones.
    `Section 4`_ of this document is devoted to such use-cases.

    The appendices contain additional information of this package. `Appendix A`_ is the full API reference of this package, and in `Appendix B`_ two methods to estimate the errors due to interpolation are provided together with the validation results.


.. _LHC SUSY Cross Section Working Group:
      https://mathworks.com/help/matlab/ref/pchip.html
.. _Prospino 2:
      https://www.thphys.uni-heidelberg.de/~plehn/index.php?show=prospino
.. _NNLL-fast:
      https://www.uni-muenster.de/Physik.TP/~akule_01/nnllfast/doku.php?id=start
.. _Resummino:
      https://resummino.hepforge.org/
.. _pandas:
      https://pandas.pydata.org/
.. _Section 2:
      quick_start
.. _Section 3:
      use_as_script
.. _Section 4:
      use_as_package
.. _Section 5:
      api_reference
.. _Appendix A:
      api_reference
.. _Section 6:
      validations
.. _Appendix B:
      validations

.. rubric:: Footnotes

.. [#deepxs] DeepXS :cite:`Otten:2018kum` is another tool for precise SUSY cross section, which utilizes deep learning technique for cross-section estimation.
