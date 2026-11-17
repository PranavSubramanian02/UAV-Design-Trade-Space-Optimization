# Design space definition, Latin Hypercube Sampling, and grid generation

import numpy as np
from scipy.stats import qmc

from ..sizing.converged_sizing_loop import solve_converged_sizing


def get_default_design_bounds() -> dict:
    # Lower and upper parameter bounds for tactical fixed-wing UAV sizing
    return {
        "aspect_ratio": (6.0, 18.0),
        "wing_area": (0.5, 2.5),
        "payload_mass": (0.5, 4.0),
        "V_cruise": (15.0, 30.0),
        "battery_fraction": (0.25, 0.45),
    }


def get_benchmark_missions() -> list:
    # Three representative mission profiles with distinct operational demands
    return [
        {
            "id": "M1_ISR",
            "name": "Long-Endurance Surveillance",
            "range_km": 60.0,
            "loiter_hr": 2.5,
            "payload_kg": 1.2,
            "V_cruise": 18.0,
            "battery_fraction": 0.38,
        },
        {
            "id": "M2_Payload",
            "name": "Heavy-Payload Transport",
            "range_km": 80.0,
            "loiter_hr": 0.5,
            "payload_kg": 2.8,
            "V_cruise": 20.0,
            "battery_fraction": 0.35,
        },
        {
            "id": "M3_Dash",
            "name": "High-Speed Tactical Dash",
            "range_km": 100.0,
            "loiter_hr": 0.5,
            "payload_kg": 1.0,
            "V_cruise": 26.0,
            "battery_fraction": 0.38,
        },
    ]


def generate_lhs_samples(
    n_samples: int = 500, bounds: dict = None, seed: int = 42
) -> np.ndarray:
    # Space-filling Latin Hypercube Sampling across aspect ratio and wing area
    if bounds is None:
        bounds = get_default_design_bounds()
    ar_min, ar_max = bounds["aspect_ratio"]
    s_min, s_max = bounds["wing_area"]

    sampler = qmc.LatinHypercube(d=2, seed=seed)
    raw_sample = sampler.random(n=n_samples)
    scaled_sample = qmc.scale(raw_sample, [ar_min, s_min], [ar_max, s_max])
    return scaled_sample


def generate_regular_grid(
    n_ar: int = 25,
    n_s: int = 25,
    ar_bounds: tuple = (6.0, 18.0),
    s_bounds: tuple = (0.5, 2.5),
) -> tuple:
    # Generates 2D meshgrid arrays for contour and surface plotting
    ar_vec = np.linspace(ar_bounds[0], ar_bounds[1], n_ar)
    s_vec = np.linspace(s_bounds[0], s_bounds[1], n_s)
    ar_grid, s_grid = np.meshgrid(ar_vec, s_vec)
    return ar_vec, s_vec, ar_grid, s_grid


def evaluate_design_point(
    aspect_ratio: float,
    wing_area: float,
    mission: dict,
    specific_energy: float = 220.0,
    degradation: float = 0.0,
) -> dict:
    # Evaluates a single aircraft configuration for a given mission specification
    return solve_converged_sizing(
        aspect_ratio=aspect_ratio,
        wing_area=wing_area,
        m_payload=mission["payload_kg"],
        V_cruise=mission["V_cruise"],
        range_km=mission["range_km"],
        t_loiter=mission["loiter_hr"],
        battery_fraction=mission.get("battery_fraction", 0.35),
        battery_spec_energy=specific_energy,
        battery_degradation=degradation,
    )


def evaluate_grid(
    ar_vec: np.ndarray,
    s_vec: np.ndarray,
    mission: dict,
    specific_energy: float = 220.0,
    degradation: float = 0.0,
) -> dict:
    # Evaluates a 2D grid of design points and returns structured result matrices
    n_ar = len(ar_vec)
    n_s = len(s_vec)

    endurance_matrix = np.full((n_s, n_ar), np.nan)
    margin_matrix = np.full((n_s, n_ar), np.nan)
    mtow_matrix = np.full((n_s, n_ar), np.nan)
    stall_matrix = np.full((n_s, n_ar), np.nan)
    feasible_matrix = np.zeros((n_s, n_ar), dtype=bool)

    for i in range(n_s):
        for j in range(n_ar):
            res = evaluate_design_point(
                ar_vec[j],
                s_vec[i],
                mission,
                specific_energy=specific_energy,
                degradation=degradation,
            )
            if res["converged"]:
                endurance_matrix[i, j] = res["max_endurance"]
                margin_matrix[i, j] = res["energy_margin"]
                mtow_matrix[i, j] = res["MTOW"]
                stall_matrix[i, j] = res["V_stall"]
                feasible_matrix[i, j] = res["feasible"]

    return {
        "endurance": endurance_matrix,
        "energy_margin": margin_matrix,
        "mtow": mtow_matrix,
        "stall_speed": stall_matrix,
        "feasible": feasible_matrix,
    }
