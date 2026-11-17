# Unit tests for Picard sizing convergence and mass conservation balance

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mdo_core.sizing.aerostructural import compute_wing_structural_mass
from mdo_core.sizing.converged_sizing_loop import solve_converged_sizing
from mdo_core.sizing.propulsion_battery import compute_peukert_factor


class TestSizingConvergence(unittest.TestCase):
    # Automated tests for numerical sizing convergence and physical laws

    def test_mass_conservation_closure(self):
        # Verifies that gross takeoff weight strictly equals the sum of constituent masses
        res = solve_converged_sizing(
            aspect_ratio=12.0,
            wing_area=0.8,
            m_payload=1.2,
            m_avionics=0.8,
            battery_fraction=0.35,
        )
        self.assertTrue(res["converged"])
        g = 9.81
        w_sum = (
            res["m_payload"] + res["m_avionics"] + res["m_struct"] + res["m_batt"]
        ) * g
        self.assertAlmostEqual(res["W0"], w_sum, delta=1e-3)
        self.assertLess(res["residual"], 1e-4)

    def test_spar_bending_penalty_monotonicity(self):
        # Verifies that higher aspect ratios incur greater root bending moments and spar mass
        w_low = compute_wing_structural_mass(80.0, aspect_ratio=8.0, wing_area=1.0)
        w_high = compute_wing_structural_mass(80.0, aspect_ratio=18.0, wing_area=1.0)
        self.assertGreater(w_high["m_wing"], w_low["m_wing"])
        self.assertGreater(w_high["M_root"], w_low["M_root"])

    def test_peukert_derating_physics(self):
        # Verifies that Traub Peukert derating penalizes capacity only at C-rates above 1C
        f_low = compute_peukert_factor(discharge_power=100.0, nominal_energy=200.0)
        f_high = compute_peukert_factor(discharge_power=400.0, nominal_energy=200.0)
        self.assertEqual(f_low, 1.0)
        self.assertLess(f_high, 1.0)

    def test_snowball_divergence_handling(self):
        # Verifies that unphysical payloads cleanly trigger infeasibility flags without hanging
        res = solve_converged_sizing(12.0, 0.5, m_payload=50.0)
        self.assertFalse(res["feasible"])


if __name__ == "__main__":
    unittest.main()
