# Converged under-relaxed Picard fixed-point sizing solver

from .aerostructural import (
    compute_aerodynamics,
    compute_empty_structural_mass,
    compute_geometry,
    compute_stall_speed,
)
from .propulsion_battery import (
    compute_battery_pack,
    compute_energy_margin,
    compute_max_endurance,
    compute_mission_energy,
    compute_phase_power,
)


def solve_converged_sizing(
    aspect_ratio: float,
    wing_area: float,
    m_payload: float = 1.0,
    m_avionics: float = 0.8,
    m_batt: float = None,
    battery_fraction: float = 0.35,
    V_cruise: float = 18.0,
    range_km: float = 50.0,
    t_loiter: float = 1.5,
    battery_spec_energy: float = 220.0,
    battery_degradation: float = 0.0,
    omega: float = 0.5,
    tol: float = 1e-4,
    max_iter: int = 60,
) -> dict:
    # Solves W0 = F(W0) mass conservation contraction loop
    g = 9.81
    W0 = (m_payload + m_avionics + 5.0) * g
    converged = False
    res = 1.0
    it = 0
    current_m_batt = 1.0

    for it in range(max_iter):
        # Sizing of composite structure based on active gross weight
        struct_dict = compute_empty_structural_mass(W0, aspect_ratio, wing_area)
        m_struct = struct_dict["m_struct_total"]

        # Cruise and loiter aerodynamics
        aero_cr = compute_aerodynamics(W0, wing_area, aspect_ratio, V_cruise)
        V_loiter = max(compute_stall_speed(W0, wing_area) * 1.2, 14.0)
        aero_lt = compute_aerodynamics(W0, wing_area, aspect_ratio, V_loiter)

        # Flight phase power draws
        p_climb = compute_phase_power(
            aero_cr["drag"] * 1.25, V_cruise * 0.9, climb_rate=1.5, W0=W0
        )["P_elec_total"]
        p_cr = compute_phase_power(aero_cr["drag"], V_cruise)["P_elec_total"]
        p_lt = compute_phase_power(aero_lt["drag"], V_loiter)["P_elec_total"]

        # Phase flight durations
        t_climb = 500.0 / (1.5 * 3600.0)
        t_cr = (range_km * 1000.0) / (V_cruise * 3600.0)

        # Mission required energy
        e_dict = compute_mission_energy(p_climb, t_climb, p_cr, t_cr, p_lt, t_loiter)
        e_req = e_dict["E_total_req"]

        # Battery mass allocation (fixed pack vs mass fraction mode)
        if m_batt is not None:
            current_m_batt = float(m_batt)
        else:
            current_m_batt = max(battery_fraction * (W0 / g), 0.5)

        # Updated weight summation
        W0_new = (m_payload + m_avionics + m_struct + current_m_batt) * g
        res = abs(W0_new - W0) / g

        # Under-relaxed Picard iteration update
        W0 = (1.0 - omega) * W0 + omega * W0_new

        # Detect divergent mass snowball growth
        if (W0 / g) > 60.0:
            break
        if res < tol:
            converged = True
            break

    MTOW = float(W0 / g)
    batt_dict = compute_battery_pack(
        current_m_batt,
        specific_energy=battery_spec_energy,
        degradation=battery_degradation,
        discharge_power=p_cr,
    )

    # Calculate performance metrics and reserve margins
    margin = compute_energy_margin(batt_dict["E_usable"], e_req)
    endurance = compute_max_endurance(batt_dict["E_usable"], p_lt)
    v_stall = compute_stall_speed(W0, wing_area)
    geo = compute_geometry(aspect_ratio, wing_area)

    # Airworthiness and regulatory constraint flags
    constraints = {
        "stall_valid": bool(v_stall <= 15.0),
        "mtow_valid": bool(MTOW <= 25.0),
        "energy_valid": bool(margin >= 0.0),
    }
    feasible = bool(converged and all(constraints.values()))

    return {
        "converged": bool(converged),
        "feasible": bool(feasible),
        "iterations": int(it + 1),
        "residual": float(res),
        "MTOW": float(MTOW),
        "W0": float(W0),
        "m_payload": float(m_payload),
        "m_avionics": float(m_avionics),
        "m_struct": float(m_struct),
        "m_wing": float(struct_dict["m_wing"]),
        "m_spar": float(struct_dict["m_spar"]),
        "m_skin": float(struct_dict["m_skin"]),
        "m_fuse_tail": float(struct_dict["m_fuse_tail"]),
        "m_batt": float(current_m_batt),
        "E_batt_usable": float(batt_dict["E_usable"]),
        "E_mission_req": float(e_req),
        "energy_margin": float(margin),
        "max_endurance": float(endurance),
        "V_stall": float(v_stall),
        "lift_to_drag_cruise": float(aero_cr["lift_to_drag"]),
        "P_cruise": float(p_cr),
        "P_loiter": float(p_lt),
        "wing_loading": float(W0 / wing_area),
        "span": float(geo["span"]),
        "constraints": constraints,
    }
