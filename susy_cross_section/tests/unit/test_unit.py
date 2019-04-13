from __future__ import absolute_import, division, print_function  # py2

import unittest

from nose.tools import eq_, ok_, raises, assert_raises, assert_almost_equal  # noqa: F401

from susy_cross_section.utility import Unit


class TestUnit(unittest.TestCase):
    def eq_unit(self, unit1, unit2):
        """Compare the two units.

        Unit has no __eq__ method because of the numerical uncertainty.
        """
        try:
            f = float(unit1 / unit2)
        except ValueError:
            raise AssertionError("%s != %s" % (unit1, unit2))

        assert_almost_equal(f, 1)

    def test_initialize(self):
        cases = [
            1,
            1000,
            0.123,
            "pb",
            "fb",
            "%",
            (1000, "fb"),
            ("fb", "fb", "%", 120, 0.1)
        ]
        for c in cases:
            if isinstance(c, tuple):
                u = Unit(*c)
            else:
                u = Unit(c)
            ok_(u)

            # idempotence
            self.eq_unit(u, Unit(u))

    def test_special_units(self):
        for a, b in [
            [Unit("%"), Unit(0.01)],
            [Unit("%", 100), Unit(1)],
            [Unit("fb"), Unit(0.001, "pb")],
            [Unit("pb"), Unit(1000, "fb")],
            [Unit(1, 2, 3), Unit(6)],
            [Unit(), Unit(1)],
        ]:
            self.eq_unit(a, b)

    def test_inverse(self):
        for u in [
            Unit(1000),
            Unit("%"),
            Unit("fb"),
            Unit("pb"),
        ]:
            eq_(float(u * u.inverse()), 1)

    def test_multiplication_and_division(self):
        for a, b, c in [
            [Unit("pb"), Unit("pb"), Unit("pb", "pb")],
            [Unit("fb"), Unit("pb"), Unit("fb", "pb")],
            [Unit(10), Unit(20), Unit(200)],
            [Unit(100, "%"), Unit("pb"), Unit("pb")],
        ]:
            self.eq_unit(a * b, c)
            self.eq_unit(c / b, a)
            self.eq_unit(c / a, b)

    def test_float(self):
        for a, b in [
            (Unit(), 1),
            (Unit(1000), 1000),
            (Unit(0.5), 0.5),
            (Unit("%"), 0.01)
        ]:
            assert_almost_equal(float(a), b)

        for u in [
            Unit("pb"),
            Unit("fb").inverse(),
            Unit("pb") * Unit("pb"),
        ]:
            with assert_raises(ValueError):
                float(u)
