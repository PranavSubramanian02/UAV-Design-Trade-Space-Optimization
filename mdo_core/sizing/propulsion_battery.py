# Propulsion and electrochemical battery modeling with Traub Peukert derating

import numpy as np


def compute_powertrain_efficiency(
    eta_prop: float = 0.78, eta_motor: float = 0.85, eta_esc: float = 0.95
) -> float:
    # Combined electrical to aerodynamic thrust efficiency
    return float(eta_prop * eta_motor * eta_esc)


def compute_peukert_factor(
    discharge_power: float, nominal_energy: float, kp: float = 1.10
) -> float:
    # Traub (2011) Peukert C-rate discharge capacity derating
    if nominal_energy <= 1e-4:
        return 0.0
    c_rate = discharge_power / nominal_energy
    if c_rate <= 1.0:
        return 1.0
    # Capacity derating exponent (kp - 1)
    f_peukert = (1.0 / c_rate) ** (kp - 1.0)
    return float(np.clip(f_peukert, 0.70, 1.0))


def compute_phase_power(
    drag: float,
    velocity: float,
    climb_rate: float = 0.0,
    W0: float = 0.0,
    P_hotel: float = 20.0,
    eta_total: float = 0.63,
) -> dict:
    # Electric power required for level flight or climbing flight
    P_aero = (drag * velocity) + (W0 * climb_rate)
    P_elec_prop = P_aero / eta_total if eta_total > 1e-4 else 0.0
    P_elec_total = P_elec_prop + P_hotel
    return {
        "P_aero": float(P_aero),
        "P_elec_prop": float(P_elec_prop),
        "P_elec_total": float(P_elec_total),
        "P_hotel": float(P_hotel),
    }


def compute_mission_energy(
    P_climb: float,
    t_climb: float,
    P_cruise: float,
    t_cruise: float,
    P_loiter: float,
    t_loiter: float,
    reserve_fraction: float = 0.20,
) -> dict:
    # Multi-phase mission energy consumption with regulatory reserve
    # Time inputs in hours, power in Watts, energy in Watt-hours (Wh)
    E_climb = P_climb * t_climb
    E_cruise = P_cruise * t_cruise
    E_loiter = P_loiter * t_loiter

    E_net = E_climb + E_cruise + E_loiter
    E_reserve = E_net * reserve_fraction
    E_total_req = E_net + E_reserve

    return {
        "E_climb": float(E_climb),
        "E_cruise": float(E_cruise),
        "E_loiter": float(E_loiter),
        "E_net": float(E_net),
        "E_reserve": float(E_reserve),
        "E_total_req": float(E_total_req),
    }


def compute_battery_pack(
    m_batt: float,
    specific_energy: float = 220.0,
    dod: float = 0.85,
    degradation: float = 0.0,
    discharge_power: float = 150.0,
    kp: float = 1.10,
) -> dict:
    # Battery usable capacity considering DoD, aging fade, and Peukert losses
    E_nom = m_batt * specific_energy
    f_peukert = compute_peukert_factor(discharge_power, E_nom, kp=kp)

    # Effective usable energy delivering to propulsion bus
    E_usable = E_nom * dod * (1.0 - degradation) * f_peukert

    return {
        "m_batt": float(m_batt),
        "E_nom": float(E_nom),
        "E_usable": float(E_usable),
        "specific_energy": float(specific_energy),
        "f_peukert": float(f_peukert),
        "degradation": float(degradation),
    }


def compute_energy_margin(E_usable: float, E_required: float) -> float:
    # Usable energy reserve margin above total mission requirements
    if E_usable <= 1e-4:
        return -100.0
    margin = ((E_usable - E_required) / E_usable) * 100.0
    return float(margin)


def compute_max_endurance(E_usable: float, P_loiter: float) -> float:
    # Maximum physical loiter endurance in hours
    if P_loiter <= 1e-4:
        return 0.0
    return float(E_usable / P_loiter)
