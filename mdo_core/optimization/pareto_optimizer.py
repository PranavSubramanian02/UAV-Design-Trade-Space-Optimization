# Deb et al. (2002) NSGA-II non-dominated sorting and Pareto front extraction

import numpy as np


def fast_non_dominated_sort(objectives: np.ndarray) -> list:
    # Partitions design candidates into Pareto dominance ranks (Rank 0 = Non-Dominated)
    # Assumes all objective columns are to be MINIMIZED
    n_points = objectives.shape[0]
    domination_counts = np.zeros(n_points, dtype=int)
    dominated_sets = [[] for _ in range(n_points)]
    fronts = [[]]

    for p in range(n_points):
        for q in range(n_points):
            if p == q:
                continue
            p_leq_q = np.all(objectives[p] <= objectives[q])
            p_lt_q = np.any(objectives[p] < objectives[q])

            if p_leq_q and p_lt_q:
                dominated_sets[p].append(q)
            elif np.all(objectives[q] <= objectives[p]) and np.any(
                objectives[q] < objectives[p]
            ):
                domination_counts[p] += 1

        if domination_counts[p] == 0:
            fronts[0].append(p)

    i = 0
    while len(fronts[i]) > 0:
        next_front = []
        for p in fronts[i]:
            for q in dominated_sets[p]:
                domination_counts[q] -= 1
                if domination_counts[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    return [f for f in fronts if len(f) > 0]


def compute_crowding_distance(
    objectives: np.ndarray, front_indices: list
) -> np.ndarray:
    # Computes crowding distance metric to preserve solution diversity along the frontier
    n_points = len(front_indices)
    if n_points <= 2:
        return np.full(n_points, np.inf)

    n_objs = objectives.shape[1]
    distances = np.zeros(n_points)
    sub_objs = objectives[front_indices]

    for m in range(n_objs):
        sorted_order = np.argsort(sub_objs[:, m])
        distances[sorted_order[0]] = np.inf
        distances[sorted_order[-1]] = np.inf

        norm = sub_objs[sorted_order[-1], m] - sub_objs[sorted_order[0], m]
        if norm < 1e-6:
            continue

        for i in range(1, n_points - 1):
            distances[sorted_order[i]] += (
                sub_objs[sorted_order[i + 1], m] - sub_objs[sorted_order[i - 1], m]
            ) / norm

    return distances


def find_knee_point(objectives: np.ndarray, front_indices: list) -> int:
    # Identifies the best balanced compromise design closest to the normalized utopia point
    sub_objs = objectives[front_indices]
    min_vals = np.min(sub_objs, axis=0)
    max_vals = np.max(sub_objs, axis=0)
    norm = np.where(max_vals - min_vals < 1e-6, 1.0, max_vals - min_vals)

    normalized = (sub_objs - min_vals) / norm
    distances = np.sqrt(np.sum(normalized**2, axis=1))
    best_idx = int(np.argmin(distances))
    return front_indices[best_idx]


def extract_pareto_front(design_records: list) -> dict:
    # Filters feasible designs and extracts 3D Pareto frontier across Endurance, MTOW, and Payload
    feasible_records = [r for r in design_records if r.get("feasible", False)]
    if len(feasible_records) == 0:
        return {
            "pareto_records": [],
            "knee_record": None,
            "all_ranks": [],
            "n_feasible": 0,
        }

    # Formulate minimization objectives: [-Endurance, MTOW, -PayloadFraction]
    objs = np.array(
        [
            [
                -float(r["max_endurance"]),
                float(r["MTOW"]),
                -float(r["m_payload"] / r["MTOW"]),
            ]
            for r in feasible_records
        ]
    )

    ranks = fast_non_dominated_sort(objs)
    rank0_indices = ranks[0]

    crowding_dist = compute_crowding_distance(objs, rank0_indices)
    knee_global_idx = find_knee_point(objs, rank0_indices)

    pareto_records = [feasible_records[i] for i in rank0_indices]
    knee_record = feasible_records[knee_global_idx]

    return {
        "pareto_records": pareto_records,
        "knee_record": knee_record,
        "all_ranks": ranks,
        "crowding_distances": crowding_dist,
        "n_feasible": len(feasible_records),
    }
