# Unit tests for multi-objective Pareto dominance sorting and crowding distance

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mdo_core.optimization.pareto_optimizer import (
    compute_crowding_distance,
    extract_pareto_front,
    fast_non_dominated_sort,
    find_knee_point,
)


class TestParetoOptimality(unittest.TestCase):
    # Automated tests for Deb et al. NSGA-II Pareto sorting algorithms

    def test_fast_non_dominated_sort(self):
        # Verifies separation into true non-dominated Rank 0 and dominated Rank 1
        objs = np.array(
            [
                [1.0, 5.0],
                [2.0, 3.0],
                [3.0, 1.0],
                [2.5, 4.0],
            ]
        )
        fronts = fast_non_dominated_sort(objs)
        self.assertEqual(len(fronts), 2)
        self.assertEqual(sorted(fronts[0]), [0, 1, 2])
        self.assertEqual(fronts[1], [3])

    def test_crowding_distance_boundaries(self):
        # Verifies boundary solutions receive infinite distance to preserve frontier span
        objs = np.array(
            [
                [1.0, 5.0],
                [2.0, 3.0],
                [3.0, 1.0],
            ]
        )
        dists = compute_crowding_distance(objs, [0, 1, 2])
        self.assertTrue(np.isinf(dists[0]))
        self.assertTrue(np.isinf(dists[-1]))
        self.assertTrue(np.isfinite(dists[1]))

    def test_knee_point_selection(self):
        # Verifies identification of the balanced compromise knee configuration
        objs = np.array(
            [
                [0.1, 0.9],
                [0.5, 0.5],
                [0.9, 0.1],
            ]
        )
        knee_idx = find_knee_point(objs, [0, 1, 2])
        self.assertEqual(knee_idx, 1)

    def test_extract_pareto_front_integration(self):
        # Verifies integration with aircraft sizing outputs and feasibility filtering
        records = [
            {
                "feasible": True,
                "max_endurance": 5.0,
                "MTOW": 7.0,
                "m_payload": 1.5,
                "span": 3.0,
            },
            {
                "feasible": True,
                "max_endurance": 3.0,
                "MTOW": 6.0,
                "m_payload": 1.5,
                "span": 2.5,
            },
            {
                "feasible": True,
                "max_endurance": 2.0,
                "MTOW": 9.0,
                "m_payload": 1.0,
                "span": 2.0,
            },
            {
                "feasible": False,
                "max_endurance": 6.0,
                "MTOW": 5.0,
                "m_payload": 1.5,
                "span": 3.5,
            },
        ]
        result = extract_pareto_front(records)
        self.assertEqual(len(result["pareto_records"]), 2)
        self.assertIsNotNone(result["knee_record"])


if __name__ == "__main__":
    unittest.main()
