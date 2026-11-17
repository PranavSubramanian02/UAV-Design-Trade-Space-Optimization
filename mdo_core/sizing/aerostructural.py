# Aerostructural analysis module for fixed-wing UAV sizing

import numpy as np


def compute_geometry(
    aspect_ratio: float, wing_area: float, taper_ratio: float = 0.6
) -> dict:
    # Compute basic wing planform geometry
    span = np.sqrt(aspect_ratio * wing_area)
    mean_chord = wing_area / span
    root_chord = (2.0 * wing_area) / (span * (1.0 + taper_ratio))
    tip_chord = root_chord * taper_ratio
    return {
        "span": float(span),
        "mean_chord": float(mean_chord),
        "root_chord": float(root_chord),
        "tip_chord": float(tip_chord),
        "aspect_ratio": float(aspect_ratio),
        "wing_area": float(wing_area),
    }


def compute_oswald_efficiency(aspect_ratio: float) -> float:
    # Raymer / Kroo Oswald efficiency degradation model with aspect ratio
    e = 1.78 * (1.0 - 0.045 * (aspect_ratio**0.68)) - 0.64
    return float(np.clip(e, 0.60, 0.92))


def compute_aerodynamics(
    W0: float,
    wing_area: float,
    aspect_ratio: float,
    velocity: float,
    rho: float = 1.225,
    CD0: float = 0.024,
) -> dict:
    # Compute aerodynamic coefficients and drag force in steady level flight (L = W0)
    q = 0.5 * rho * (velocity**2)
    CL = W0 / (q * wing_area)

    e = compute_oswald_efficiency(aspect_ratio)
    CD_induced = (CL**2) / (np.pi * e * aspect_ratio)
    CD = CD0 + CD_induced

    drag = CD * q * wing_area
    lift_to_drag = CL / CD if CD > 1e-6 else 0.0

    return {
        "CL": float(CL),
        "CD": float(CD),
        "CD0": float(CD0),
        "CD_induced": float(CD_induced),
        "lift_to_drag": float(lift_to_drag),
        "drag": float(drag),
        "dynamic_pressure": float(q),
        "oswald_e": float(e),
    }


def compute_stall_speed(
    W0: float, wing_area: float, CL_max: float = 1.35, rho: float = 1.225
) -> float:
    # Hand / catapult launch stall speed calculation
    return float(np.sqrt((2.0 * W0) / (rho * wing_area * CL_max)))


def compute_wing_structural_mass(
    W0: float,
    aspect_ratio: float,
    wing_area: float,
    n_ult: float = 3.8,
    tc_ratio: float = 0.12,
    sigma_allow: float = 1.8e8,
    rho_cf: float = 1550.0,
    k_skin: float = 1.25,
) -> dict:
    # Sizing of composite wing spar and skin under limit pull-up load factor
    geo = compute_geometry(aspect_ratio, wing_area)
    b = geo["span"]
    c_root = geo["root_chord"]

    # Root bending moment for elliptical / trapezoidal lift distribution
    M_root = (n_ult * W0 * b) / (3.0 * np.pi)

    # Spar height at root section
    h_spar = tc_ratio * c_root

    # Required spar cap area to resist bending stress
    A_cap = M_root / (sigma_allow * h_spar)

    # Spar mass (caps + shear web factor of 1.4)
    m_spar = 1.4 * (2.0 * rho_cf * A_cap * (b / 2.0))

    # Skin, ribs, and sandwich core mass proportional to wing surface area
    m_skin = k_skin * wing_area

    # Total wing structural mass
    m_wing = m_spar + m_skin

    return {
        "m_wing": float(m_wing),
        "m_spar": float(m_spar),
        "m_skin": float(m_skin),
        "M_root": float(M_root),
        "A_cap": float(A_cap),
    }


def compute_empty_structural_mass(
    W0: float,
    aspect_ratio: float,
    wing_area: float,
    k_fuse: float = 0.35,
) -> dict:
    # Total airframe structural mass: wing + fuselage pod + tail empennage
    wing_dict = compute_wing_structural_mass(W0, aspect_ratio, wing_area)

    # Fuselage and empennage mass scaling with gross weight and planform size
    m_fuse_tail = k_fuse * (W0 / 9.81) ** 0.7 + 0.3 * wing_area
    m_struct_total = wing_dict["m_wing"] + m_fuse_tail

    return {
        "m_struct_total": float(m_struct_total),
        "m_wing": float(wing_dict["m_wing"]),
        "m_spar": float(wing_dict["m_spar"]),
        "m_skin": float(wing_dict["m_skin"]),
        "m_fuse_tail": float(m_fuse_tail),
        "M_root": float(wing_dict["M_root"]),
    }
