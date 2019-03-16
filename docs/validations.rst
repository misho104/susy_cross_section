Validations
===========

This package also provides tools to validate interpolation methods, i.e., to estimate uncertainties due to interpolation.
We here discuss the validation methods we propose, show some of the validation results, and introduce the procedure for users to test their interpolator or their grid data.
The validation results are provided in |vdir|__ directory of this package, together with all the codes to generate the results.

We propose and use two methods for validation.
One is based on comparison among several interpolator; it is simple and gives a good measure of the error estimation due to interpolation.
Another one is what we call "sieve-interpolation" results [#naming]_, which gives strict upper bounds on the error of interpolations.

.. [#naming] Or tell me another better name, if you have.

.. |vdir| replace:: validations/
__ https://github.com/misho104/susy_cross_section/tree/master/validation/

Notation
--------

We use the following notations to discuss our validations.
This package compiles each row of the grid data to :math:`({\boldsymbol x}, y, \Delta^+, \Delta^-)`, where :math:`\boldsymbol x\in P\subset\mathbb R^D` is a parameter set with :math:`D` being the number of parameters, :math:`y` is the central value for cross section :math:`\sigma({\boldsymbol x})`, and :math:`\Delta^\pm` are the absolute values of positive and negative uncertainties.

We here assume that the grid is "rectilinear"; i.e., the parameter space :math:`P` is a :math:`D`-dimensional cube sliced along all the axes with possibly non-uniform grid spacing.
In other words, the grid is defined by lists of numbers, :math:`[c_{11}, c_{12}, \dots], \dots, [c_{D1}, c_{D2}, \dots]`, where each list corresponds to one parameter axis [#level]_, and all the grid points :math:`(c_{1i_1}, c_{2i_2}, \dots, c_{Di_D})` are provided in the grid table.
Thus we can address each grid point by :math:`D`-integers, :math:`I:=(i_1, \dots, i_D)`, which we will mainly use in the following discussion.

Each patch of tessellation can also be addressed by :math:`D`-integers.
In a :math:`D`-dimensional grid, a patch is formed by :math:`2^D` grid points and we use the smallest index among the points to label a tessellation patch.
For example, a patch :math:`S_{i,j}` of a two-dimensional grid is the square surrounded by the points :math:`(\boldsymbol x_{i,j}, \boldsymbol x_{i,j+1}, \boldsymbol x_{i+1, j}, \boldsymbol x_{i+1, j+1})`, or more explicitly,

.. math:: S_{i,j} := \Bigl\{(x_1, x_2) \Big| c_{1,i} \le x_1 \le c_{1, i+1}, c_{2,j} \le x_2 \le c_{2, j+1} \Bigr\}.

An interpolator constructs an interpolating function :math:`f: P\to \mathbb{R}` from a grid table.
It is a continuous function (at least in this package) and satisfies :math:`f({\boldsymbol x}_I)=y_I`.
he interpolators of this package also gives interpolations for values with uncertainties :math:`f^\pm`, which satisfy :math:`f^\pm({\boldsymbol x}_I)=y_I\pm\Delta^\pm`.

.. [#level] This array is equivalent to the :py:attr:`~pandas.MultiIndex.levels` attribute of :py:class:`~pandas.MultiIndex` used to describe the grid index of data-frame for :math:`D\ge2`.

To discuss the difference between two functions :math:`f_1` and :math:`f_2`, we define variations and badnesses.
The variation :math:`v` is defined by the relative difference, while the badness :math:`b` is the ratio of the difference to the ther uncertainty; i.e.,

.. math::

     v({\boldsymbol x}) = \frac{f_2({\boldsymbol x}) - f_1({\boldsymbol x})}{f_1({\boldsymbol x})},\qquad
     b({\boldsymbol x}) = \frac{f_2({\boldsymbol x}) - f_1({\boldsymbol x})}{\min\bigl[f^+_1({\boldsymbol x})-f_1({\boldsymbol x}), f_1({\boldsymbol x})-f^-_1({\boldsymbol x})\bigr]}.

Though they are not symmetric for :math:`f_1` and :math:`f_2`, the differences are negligible for our discussion.

The badness is a good measure to discuss the interpolation uncertainty.
For example, :math:`b=0.5` means the interpolation uncertainty is the half of the uncertainty :math:`\sigma` stored in the grid table, where we can estimate the total uncertainty by

.. math::  \sigma_{\text{total}} = \sqrt{\sigma^2 + (0.5\sigma)^2} \simeq 1.12\sigma.

Accordingly, we can safely ignore the difference between two interpolations if :math:`b<0.3` (or :math:`\sigma_{\text{total}}<1.04\sigma`), while we should consider including interpolation uncertainty if :math:`b>0.5`.


"Compare" method
----------------

This method estimates the interpolation error by comparing results from several interpolators.
For :math:`D=1`, we have several "kinds" of `Scipy1dInterpolator`, while for :math:`D=2`, we have "linear" and "spline" options for `ScipyGridInterpolator`.
The differences among the interpolators will give us a good estimation of the interpolation error.
This method does not suit for :math:`D\ge3`, but such tables are not yet included in this package.


|begintwofigure|

.. _sdcpl-compare:
.. twofigure:: _static/images/sdcpl-compare-1.*
      :width: 360px
      :align: center

      For 13 TeV :math:`pp\to\tilde q\tilde q^*` cross section.

.. _slep-compare:
.. twofigure:: _static/images/slep-compare-1.*
      :width: 360px
      :align: center

      For 13 TeV :math:`pp\to\tilde l\tilde l^*` cross section.

.. raw::  latex

   \caption{%
      Validation results of one-dimensional interpolators. The left (right) figure uses the grid table for 13 TeV LHC cross section provided by NNLLfast collaboration (LHC SUSY Cross Section Working Group).
      In the upper figures the interpolating functions and the original grid data are plotted, where the vertical black lines correspond the uncertainty band of the original data.
      The lower figures show the relative difference between the linear interpolator and the other interpolators together with the original uncertainty including the scale, PDF, and $\alpha_{\mathrm s}$ uncertainties.
      The left figure also includes results from the NNLLfast's official interpolating routine. They are shown by very tiny black dots but exactly overlapping the other lines.
   }

|endtwofigure|


Two examples of :math:`D=1` are shown in :numref:`sdcpl-compare` and :numref:`slep-compare`, where the linear, cubic-spline, Akima :cite:`akima`, and piecewise cubic Hermite interpolating polynomial (PCHIP) :cite:`pchip` interpolators based on log-log axes are compared to each other.
In addition, for data tables provided by the NNLLfast collaboration (i.e., in :numref:`sdcpl-compare`), we compare our interpolators with their official interpolator; the results are shown by very tiny black dots, which may be seen as a black line overlapping the other results.

In the upper figures the interpolation results are plotted together with the original grid data shown by black vertical lines.
All the results, crossing the central values by definition, are overlapped and undistinguishable.
The lower plots show the relative differences between the linear and other interpolators.
In :numref:`sdcpl-compare` the badness is at most 8.9% and we regard those interpolators are equivalent.
Meanwhile, in :numref:`slep-compare` the differences are visible.
Especially, in the first interval, the linear interpolator gives a result considerably different from the other interpolators. which are all based on spline method and thus consistent, corresponding a badness of 0.91.
Since we cannot tell which interpolator is giving the most accurate result, an interpolation uncertainty should be introduced for this interval, for example, by multiplying the other uncertainty by a factor :math:`\sqrt{1+0.91^2}\simeq 1.35`.

In general, the interpolation results are less accurate for the "surface" region of the parameter space :math:`P`, which corresponds to the first and last intervals in one-dimension case.
For example, in the cubic-spline method, the functions of the first and last intervals are highly dependent on the boundary conditions.
Thus users should be very careful if they apply interpolations to the surface regions in their analysis.

.. _gg-compare:
.. figure:: _static/images/gg-compare.*
      :align: center

      A validation result of two-dimensional interpolators using the 13 TeV :math:`pp\to\tilde g\tilde g` cross-section grid provided by NNLLfast collaboration.
      We here compare the linear and spline interpolators with the official NNLLfast interpolator ("orig") and plot the badness, which is defined by the ratio of the difference to the other uncertainties.
      The upper-left plot shows the largest difference among the three comparisons, while the respective differences are shown in the other plots.

:numref:`gg-compare` shows a comparison result for two-dimensional case.
The linear and spline interpolators, together with the NNLLfast official interpolator, are compared in the gluino pair-production grid for the 13 TeV LHC.
The grid spacing is 100 GeV for both axes.
The spline interpolator (`ScipyGridInterpolator` with "spline" option) reproduces the official interpolator, while the linear interpolator has small deviations but the points with :math:`b>0.3` is found only in the surface regions ("ms" or "mgl" less than 600 GeV).
Accordingly, these interpolators are equivalent for non-surface regions, while attention should always be paid for interpolating results of the surface regions.

Validation results for other grid tables are provided together with the package.
For most of the grid tables the differences among the interpolators are negligible for non-surface regions, while significant differences are found in surface regions of some grid tables.
While users should think of including uncertainties for interpolations in surface regions, one should keep in mind that this "compare" method is just a comparison and thus qualitative rather than quantitative.
Thus we put further analyses out of scope of this package and left them to users.
For details, see the files in |vdir|__, where codes and instructions to generate the validation results by their own are provided.


.. |vdir| replace:: validations/
__ https://github.com/misho104/susy_cross_section/tree/master/validation/

"Sieve" method
--------------

TBW
