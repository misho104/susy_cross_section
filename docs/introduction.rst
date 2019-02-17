Introduction
============

Background
----------

- Production cross section is the key number of high-energy collider experiments.
- For Standard-Model processes, the values are calculated with high accuracy (more than NNLO?).
- New physics searches rely on the cross section because an expected rate of events beyond the Standard Model are calculated as a product of cross section and integrated luminosity.
- Calculation technologies for SUSY production cross sections are recently developed and publicly available:

    - Prospino, NLLfast, ...

- The results are summarized and several standards are publicly available:

    - data set by LHC SUSY Cross Section Working Group :cite:`LHCSUSYCSWG`
    - Fastlim :cite:`Papucci:2014rja` internally uses a grid data set for SUSY production cross sections.
    - For electroweak process, DeepXS :cite:`Otten:2018kum` 


This package
------------

This python package ``susy_cross_section`` provides a tool-kit to handle various formats of cross-section grid data, so that one can get the interpolated cross section easily by running a script, or by importing this package to your python codes.

