# Battery technology sensitivity, degradation analysis, and payload-range diagrams

import numpy as np

from ..sizing.converged_sizing_loop import solve_converged_sizing


def get_battery_technologies() -> dict:
    # Gravimetric specific energy densities (Wh/kg) for battery chemistries
    return {
        "Li-ion (Baseline)": 220.0,
        "Lithium-Sulfur (Li-S)": 400.0,
        "Solid-State (Advanced)": 500.0,
    }


def compute_payload_range_curves(
    aspect_ratio: float = 12.0,
    wing_area: float = 0.8,
    mtow_limit: float = 10.0,
    payload_vec: np.ndarray = None,
    technologies: dict = None,
    dod: float = 0.85,
    V_cruise: float = 18.0,
) -> dict:
    # Generates piecewise payload-range envelopes across battery chemistries
    if payload_vec is None:
        payload_vec = np.linspace(0.5, 4.0, 10)
    if technologies is None:
        technologies = get_battery_technologies()

    curves = {}
    for tech_name, spec_energy in technologies.items():
        range_km_list = []
        for payload in payload_vec:
            # Sizing convergence under fixed gross takeoff weight limit
            res = solve_converged_sizing(
                aspect_ratio=aspect_ratio,
                wing_area=wing_area,
                m_payload=payload,
                V_cruise=V_cruise,
                battery_spec_energy=spec_energy,
                battery_fraction=0.35,
            )
            if res["converged"]:
                # Flight range at cruise airspeed based on usable energy
                flight_time_hr = res["E_batt_usable"] / res["P_cruise"]
                range_km = flight_time_hr * (V_cruise * 3.6)
                range_km_list.append(float(range_km))
            else:
                range_km_list.append(0.0)

        curves[tech_name] = np.array(range_km_list)

    return {
        "payload_vec": payload_vec,
        "curves": curves,
    }


def compute_degradation_curves(
    aspect_ratio: float = 12.0,
    wing_area: float = 0.8,
    payload_vec: np.ndarray = None,
    degradation_levels: dict = None,
    base_specific_energy: float = 220.0,
    V_cruise: float = 18.0,
) -> dict:
    # Models mission range reduction over battery operational lifecycle
    if payload_vec is None:
        payload_vec = np.linspace(0.5, 4.0, 10)
    if degradation_levels is None:
        degradation_levels = {
            "Beginning of Life (0% Fade)": 0.00,
            "Middle of Life (15% Fade)": 0.15,
            "End of Life (30% Fade)": 0.30,
        }

    curves = {}
    for label, deg in degradation_levels.items():
        range_km_list = []
        for payload in payload_vec:
            res = solve_converged_sizing(
                aspect_ratio=aspect_ratio,
                wing_area=wing_area,
                m_payload=payload,
                V_cruise=V_cruise,
                battery_spec_energy=base_specific_energy,
                battery_degradation=deg,
                battery_fraction=0.35,
            )
            if res["converged"]:
                flight_time_hr = res["E_batt_usable"] / res["P_cruise"]
                range_km = flight_time_hr * (V_cruise * 3.6)
                range_km_list.append(float(range_km))
            else:
                range_km_list.append(0.0)

        curves[label] = np.array(range_km_list)

    return {
        "payload_vec": payload_vec,
        "curves": curves,
    }


def evaluate_battery_tradeoff(
    aspect_ratio: float,
    wing_area: float,
    mission: dict,
    technologies: dict = None,
) -> list:
    # Side-by-side performance comparison for a target mission across battery chemistries
    if technologies is None:
        technologies = get_battery_technologies()

    comparison = []
    for tech_name, spec_energy in technologies.items():
        res = solve_converged_sizing(
            aspect_ratio=aspect_ratio,
            wing_area=wing_area,
            m_payload=mission["payload_kg"],
            V_cruise=mission["V_cruise"],
            range_km=mission["range_km"],
            t_loiter=mission["loiter_hr"],
            battery_spec_energy=spec_energy,
            battery_fraction=mission.get("battery_fraction", 0.35),
        )
        comparison.append(
            {
                "technology": tech_name,
                "specific_energy": spec_energy,
                "MTOW": res["MTOW"],
                "m_batt": res["m_batt"],
                "E_usable": res["E_batt_usable"],
                "max_endurance": res["max_endurance"],
                "energy_margin": res["energy_margin"],
                "feasible": res["feasible"],
            }
        )

    return comparison
