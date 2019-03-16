r"""A subpackage to perform interpolation.

At the subpackage-level, the following modules and class aliases are defined.

=============================== ===============================================
module `interp.axes_wrapper`    has axis preprocessors for interpolation
module `interp.interpolator`    has interpolator classes
`!interp.Scipy1dInterpolator`   = `interp.interpolator.Scipy1dInterpolator`
`!interp.ScipyGridInterpolator` = `interp.interpolator.ScipyGridInterpolator`
=============================== ===============================================

This subpackage contains the following class. Actual interpolators are
subclasses of `AbstractInterpolator` and not listed here.

========================================== ====================================
 classes
========================================== ====================================
`interp.axes_wrapper.AxesWrapper`          axis preprocessor
`interp.interpolator.Interpolation`        interpolation result
`interp.interpolator.AbstractInterpolator` base class for interpolators
========================================== ====================================

Note
----

Interpolation of :math:`N` data points,

.. math:: (x_{n1}, \dots, x_{nd}; y_n)

for :math:`n=1, ..., N` and :math:`d` is the dimension of parameter space,
i.e., the number of parameters, returns a continuous function :math:`f`
satisfying :math:`f({\boldsymbol x}_n)=y_n`.


Warning
-------

One should distinguish an interpolation :math:`f` from fitting functions. An
interpolation satisfies :math:`f({\boldsymbol x}_n)=y_n` but this does not
necessarily hold for fitting functions. Meanwhile, an interpolation is defined
patch by patch, so its first or higher derivative can be discontinuous, while
usually a fit function is globally defined and class :math:`C^\infty`.
"""

from .interpolator import Scipy1dInterpolator, ScipyGridInterpolator  # noqa: F401
