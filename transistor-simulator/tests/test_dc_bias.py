"""Unit tests ของสมการ DC Bias — รันด้วย python -m unittest discover -s tests -v"""

import unittest

from dc_bias import BiasInputs, ValidationError, calculate_dc_bias, parse_inputs

FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}


def ref_inputs(**overrides):
    base = dict(vcc=12.0, r1=100.0, r2=22.0, rc=2.2, re=1.0, beta=100.0, vbe=0.7)
    base.update(overrides)
    return BiasInputs(**base)


class TestParseInputs(unittest.TestCase):
    def test_valid_form_is_parsed(self):
        inputs = parse_inputs(FORM)
        self.assertAlmostEqual(inputs.vcc, 12.0)
        self.assertAlmostEqual(inputs.r1, 100.0)
        self.assertAlmostEqual(inputs.vbe, 0.70)

    def test_non_numeric_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({**FORM, "r1": "abc"})
        self.assertIn("r1", ctx.exception.errors)

    def test_zero_resistance_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({**FORM, "r2": "0"})
        self.assertIn("r2", ctx.exception.errors)

    def test_negative_beta_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({**FORM, "beta": "-10"})
        self.assertIn("beta", ctx.exception.errors)

    def test_missing_field_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({"vcc": "12"})
        self.assertIn("r1", ctx.exception.errors)
        self.assertIn("beta", ctx.exception.errors)

    def test_vbe_must_be_below_vcc(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({**FORM, "vbe": "12"})
        self.assertIn("vbe", ctx.exception.errors)


class TestCalculate(unittest.TestCase):
    def test_reference_operating_point(self):
        result = calculate_dc_bias(ref_inputs())

        self.assertAlmostEqual(result.vth, 2.1639, places=3)
        self.assertAlmostEqual(result.rth_kohm, 18.0328, places=3)
        self.assertAlmostEqual(result.ib_ma, 0.0123, places=4)
        self.assertAlmostEqual(result.ic_ma, 1.2299, places=3)
        self.assertAlmostEqual(result.ie_ma, 1.2422, places=3)
        self.assertAlmostEqual(result.ve, 1.2422, places=3)
        self.assertAlmostEqual(result.vb, 1.9422, places=3)
        self.assertAlmostEqual(result.vc, 9.2942, places=3)
        self.assertAlmostEqual(result.vce, 8.0520, places=3)

        self.assertEqual(result.region, "active")
        self.assertEqual(result.warnings, ())

    def test_cutoff_when_vth_below_vbe(self):
        result = calculate_dc_bias(ref_inputs(r2=1.0))

        self.assertEqual(result.region, "cutoff")
        self.assertEqual(result.ic_ma, 0.0)
        self.assertEqual(result.ie_ma, 0.0)
        self.assertTrue(result.warnings)

    def test_saturation_when_vce_negative(self):
        result = calculate_dc_bias(ref_inputs(rc=20.0))

        self.assertEqual(result.region, "saturation")
        self.assertLessEqual(result.vce, 0.2)
        self.assertTrue(any("Forward-Active" in w for w in result.warnings))

    def test_kohm_values_are_converted_before_calculation(self):
        result = calculate_dc_bias(ref_inputs())

        self.assertAlmostEqual(result.rth_kohm, 18.0328, places=3)
        self.assertLess(result.ic_ma, 10.0)


if __name__ == "__main__":
    unittest.main()
