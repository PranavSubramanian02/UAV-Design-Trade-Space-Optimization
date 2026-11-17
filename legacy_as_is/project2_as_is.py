#!/usr/bin/env python3
# ===========================================================================
# MISSION-DRIVEN UAV DESIGN & CONFIGURATION OPTIMIZATION FRAMEWORK
# 
# As-Is Python Migration of MATLAB Live Script (Project2.mlx)
# Author of Original Model: Pranav Subramanian (M.Tech)
# Target Venue: ICAAV-2026 (ADE-DRDO & AeSI)
# 
# References (Conceptual Design Level):
# - Raymer, Aircraft Design: A Conceptual Approach
# - Anderson, Aircraft Performance and Design
# - Beard & McLain, Small Unmanned Aircraft Systems
# - Donateo et al., Energy-Based Metrics for Electric Aircraft
# ===========================================================================

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from sklearn.cluster import KMeans

def run_trade_space(show_plots=False, save_dir="output_figures"):
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)

    # =========================================================================
    # SECTION 1 — GLOBAL CONSTANTS & PHYSICAL PARAMETERS
    # =========================================================================
    g = 9.81                                   # [m/s^2]
    rho0 = 1.225                               # Sea-level density [kg/m^3]
    H_scale = 8500.0                           # Scale height [m]

    eta_prop  = 0.75                           # Propeller efficiency
    eta_motor = 0.90                           # Motor efficiency
    eta_total = eta_prop * eta_motor           # Net propulsive efficiency

    CD0 = 0.035                                # Zero-lift drag coefficient
    e   = 0.80                                 # Oswald efficiency factor
    CL_max_allow = 1.20                        # Conservative CL limit

    k_struct = 0.45                            # Structural mass fraction constant
    misc_mass_kg = 1.2                         # Fixed non-modeled mass (avionics, wiring, etc.)

    # =========================================================================
    # SECTION 2 — DESIGN VARIABLE SPACE (EXPLICIT GRIDS)
    # =========================================================================
    AR_vec = np.linspace(8, 18, 21)            # Aspect ratio range
    WS_vec = np.linspace(40, 120, 21)          # Wing loading [N/m^2]

    # In MATLAB meshgrid(AR, WS): rows correspond to WS, cols correspond to AR
    AR_grid, WS_grid = np.meshgrid(AR_vec, WS_vec)
    nDesignPoints = AR_grid.size

    # =========================================================================
    # SECTION 3 — BATTERY MODEL (BASELINE)
    # =========================================================================
    battery_specific_energy_Whkg = 220.0       # Conservative Li-ion value

    # =========================================================================
    # SECTION 4 — MISSION DEFINITIONS (MULTI-MISSION SET)
    # =========================================================================
    missions = [
        {
            'name': 'ISR_Long_Endurance',
            'range_km': 80.0,
            'loiter_hr': 3.0,
            'payload_kg': 1.5,
            'V_cruise': 20.0,
            'altitude_m': 1000.0
        },
        {
            'name': 'Mapping_Long_Range',
            'range_km': 180.0,
            'loiter_hr': 0.5,
            'payload_kg': 2.5,
            'V_cruise': 25.0,
            'altitude_m': 1200.0
        },
        {
            'name': 'Comm_Relay',
            'range_km': 60.0,
            'loiter_hr': 2.0,
            'payload_kg': 3.0,
            'V_cruise': 18.0,
            'altitude_m': 1500.0
        }
    ]
    nMissions = len(missions)

    # =========================================================================
    # SECTION 5 & 6 — MAIN PHYSICS & FEASIBILITY LOOP
    # =========================================================================
    design_db_records = []

    for m_idx, mission in enumerate(missions, start=1):
        rho = rho0 * np.exp(-mission['altitude_m'] / H_scale)

        Endurance_map   = np.full(AR_grid.shape, np.nan)
        EnergyMargin_map = np.full(AR_grid.shape, np.nan)
        Mass_map        = np.full(AR_grid.shape, np.nan)

        # Flatten arrays column-major (Fortran order) to mirror MATLAB linear indexing
        AR_flat = AR_grid.ravel(order='F')
        WS_flat = WS_grid.ravel(order='F')

        Endurance_flat   = np.full(nDesignPoints, np.nan)
        EnergyMargin_flat = np.full(nDesignPoints, np.nan)
        Mass_flat        = np.full(nDesignPoints, np.nan)

        for i in range(nDesignPoints):
            AR = AR_flat[i]
            WS = WS_flat[i]

            # Step 1: Initial weight guess
            W0 = (mission['payload_kg'] + 4.0) * g
            S = W0 / WS

            # Step 2: Aerodynamics at cruise
            CL = W0 / (0.5 * rho * (mission['V_cruise'] ** 2) * S)
            if CL > CL_max_allow:
                continue

            CD = CD0 + (CL ** 2) / (np.pi * e * AR)
            Drag = 0.5 * rho * (mission['V_cruise'] ** 2) * S * CD

            # Step 3: Power required
            Power_req_W = Drag * mission['V_cruise'] / eta_total

            # Step 4: Mission energy
            cruise_time_hr = mission['range_km'] * 1000.0 / mission['V_cruise'] / 3600.0
            Energy_mission_Wh = Power_req_W * (cruise_time_hr + mission['loiter_hr'])

            # Step 5: Battery sizing
            battery_mass_kg = Energy_mission_Wh / battery_specific_energy_Whkg
            struct_mass_kg  = k_struct * (battery_mass_kg + mission['payload_kg'])
            total_mass_kg   = battery_mass_kg + struct_mass_kg + mission['payload_kg'] + misc_mass_kg
            Energy_available_Wh = battery_mass_kg * battery_specific_energy_Whkg

            # Step 6: Energy feasibility check
            if Energy_available_Wh >= Energy_mission_Wh:
                endurance_val = cruise_time_hr + mission['loiter_hr']
                energy_margin_val = (Energy_available_Wh - Energy_mission_Wh) / Energy_available_Wh

                Endurance_flat[i] = endurance_val
                EnergyMargin_flat[i] = energy_margin_val
                Mass_flat[i] = total_mass_kg

                design_db_records.append({
                    'MissionID': m_idx,
                    'AspectRatio': AR,
                    'WingLoading': WS,
                    'Endurance_hr': endurance_val,
                    'Range_km': mission['range_km'],
                    'Payload_kg': mission['payload_kg'],
                    'TotalMass_kg': total_mass_kg
                })

        Endurance_map = Endurance_flat.reshape(AR_grid.shape, order='F')
        EnergyMargin_map = EnergyMargin_flat.reshape(AR_grid.shape, order='F')
        Mass_map = Mass_flat.reshape(AR_grid.shape, order='F')

        # ---------------------------------------------------------------------
        # SECTION 7: CONTOURS
        # ---------------------------------------------------------------------
        # Endurance contour
        fig_end, ax_end = plt.subplots(figsize=(7, 5))
        valid_end = Endurance_map[~np.isnan(Endurance_map)]
        if len(valid_end) > 0 and (np.max(valid_end) > np.min(valid_end)):
            cs = ax_end.contourf(AR_grid, WS_grid, Endurance_map, 18, cmap='viridis')
            fig_end.colorbar(cs, ax=ax_end)
        else:
            # Replicates MATLAB's "Contour not rendered for constant ZData"
            ax_end.text(0.5, 0.5, f"Constant Endurance: {valid_end[0]:.2f} hr" if len(valid_end) else "Infeasible",
                        horizontalalignment='center', verticalalignment='center', transform=ax_end.transAxes)
        ax_end.set_xlabel('Aspect Ratio')
        ax_end.set_ylabel('Wing Loading (N/m^2)')
        ax_end.set_title(f"Endurance Contours — {mission['name']}")
        ax_end.grid(True)
        fig_end.tight_layout()
        if save_dir:
            fig_end.savefig(os.path.join(save_dir, f"fig_endurance_contour_m{m_idx}.png"), dpi=300)

        # Energy Margin contour
        fig_em, ax_em = plt.subplots(figsize=(7, 5))
        valid_em = EnergyMargin_map[~np.isnan(EnergyMargin_map)]
        if len(valid_em) > 0 and (np.max(valid_em) > np.min(valid_em)):
            cs = ax_em.contourf(AR_grid, WS_grid, EnergyMargin_map * 100, 18, cmap='magma')
            fig_em.colorbar(cs, ax=ax_em)
        else:
            ax_em.text(0.5, 0.5, "Constant Energy Margin: 0.00%",
                       horizontalalignment='center', verticalalignment='center', transform=ax_em.transAxes)
        ax_em.set_xlabel('Aspect Ratio')
        ax_em.set_ylabel('Wing Loading (N/m^2)')
        ax_em.set_title(f"Energy Margin (%) — {mission['name']}")
        ax_em.grid(True)
        fig_em.tight_layout()
        if save_dir:
            fig_em.savefig(os.path.join(save_dir, f"fig_energy_margin_contour_m{m_idx}.png"), dpi=300)

        # ---------------------------------------------------------------------
        # SECTION 8: 3D DESIGN TRADE SPACE
        # ---------------------------------------------------------------------
        fig_3d = plt.figure(figsize=(8, 6))
        ax_3d = fig_3d.add_subplot(111, projection='3d')
        mask = ~np.isnan(Endurance_flat)
        if np.any(mask):
            p = ax_3d.scatter(AR_flat[mask], WS_flat[mask], Endurance_flat[mask],
                              c=Mass_flat[mask], s=60, cmap='coolwarm', depthshade=True)
            fig_3d.colorbar(p, ax=ax_3d, label='Total Mass (kg)')
        ax_3d.set_xlabel('Aspect Ratio')
        ax_3d.set_ylabel('Wing Loading (N/m^2)')
        ax_3d.set_zlabel('Endurance (hr)')
        ax_3d.set_title(f"Design Trade Space — {mission['name']}")
        ax_3d.view_init(elev=25, azim=135)
        ax_3d.grid(True)
        fig_3d.tight_layout()
        if save_dir:
            fig_3d.savefig(os.path.join(save_dir, f"fig_trade_space_3d_m{m_idx}.png"), dpi=300)

    # =========================================================================
    # SECTION 9 — MASTER DATABASE
    # =========================================================================
    DesignDB = pd.DataFrame(design_db_records)

    # =========================================================================
    # SECTION 10 — GLOBAL PARETO FRONT EXTRACTION
    # =========================================================================
    # Objectives: Maximize Endurance (-Endurance), Minimize Total Mass (+TotalMass)
    obj = np.column_stack([-DesignDB['Endurance_hr'].values, DesignDB['TotalMass_kg'].values])
    nPoints = len(DesignDB)
    isPareto = np.ones(nPoints, dtype=bool)

    for i in range(nPoints):
        for j in range(nPoints):
            # j dominates i if j is <= i in all objectives and strictly < in at least one
            if np.all(obj[j, :] <= obj[i, :]) and np.any(obj[j, :] < obj[i, :]):
                isPareto[i] = False
                break

    DesignDB['Pareto'] = isPareto

    fig_pareto, ax_pareto = plt.subplots(figsize=(8, 5))
    ax_pareto.scatter(DesignDB['TotalMass_kg'], DesignDB['Endurance_hr'],
                      s=30, color='black', alpha=0.6, label='Feasible')
    ax_pareto.scatter(DesignDB.loc[isPareto, 'TotalMass_kg'], DesignDB.loc[isPareto, 'Endurance_hr'],
                      s=80, color='red', label='Pareto-optimal')
    ax_pareto.set_xlabel('Total Mass (kg)')
    ax_pareto.set_ylabel('Endurance (hr)')
    ax_pareto.set_title('Global Pareto Front (All Missions)')
    ax_pareto.legend(loc='best')
    ax_pareto.grid(True)
    fig_pareto.tight_layout()
    if save_dir:
        fig_pareto.savefig(os.path.join(save_dir, "fig_global_pareto_front.png"), dpi=300)

    # =========================================================================
    # SECTION 11, 12 & 13 — PAYLOAD-RANGE ENVELOPES (BATTERY TECHNOLOGIES)
    # =========================================================================
    batteryTech = [
        {'name': 'Li-ion', 'Whkg': 220.0},
        {'name': 'Li-S', 'Whkg': 400.0},
        {'name': 'Solid-State', 'Whkg': 500.0}
    ]

    payload_vec = np.linspace(0.5, 4.0, 16)
    range_vec   = np.linspace(30.0, 300.0, 20)

    baselineMission = missions[0]
    rho_baseline = rho0 * np.exp(-baselineMission['altitude_m'] / H_scale)
    V_baseline   = baselineMission['V_cruise']
    WS_baseline  = 80.0
    AR_baseline  = 14.0

    fig_env_tech, ax_env_tech = plt.subplots(figsize=(8, 5))

    for b in batteryTech:
        Whkg_nominal = b['Whkg']
        maxRange_payload = np.full(len(payload_vec), np.nan)

        for p_idx, payload in enumerate(payload_vec):
            feasible_ranges = []
            for range_km in range_vec:
                W0 = (payload + 4.0) * g
                S  = W0 / WS_baseline
                CL = W0 / (0.5 * rho_baseline * (V_baseline ** 2) * S)
                if CL > CL_max_allow:
                    continue

                CD = CD0 + (CL ** 2) / (np.pi * e * AR_baseline)
                Drag = 0.5 * rho_baseline * (V_baseline ** 2) * S * CD
                Power_req = Drag * V_baseline / eta_total

                cruise_time_hr = range_km * 1000.0 / V_baseline / 3600.0
                Energy_req_Wh = Power_req * (cruise_time_hr + baselineMission['loiter_hr'])

                batt_mass = Energy_req_Wh / Whkg_nominal
                struct_mass = k_struct * (batt_mass + payload)
                total_mass = batt_mass + struct_mass + payload + misc_mass_kg
                Energy_avail = batt_mass * Whkg_nominal

                if Energy_avail >= Energy_req_Wh and total_mass < 30.0:
                    feasible_ranges.append(range_km)

            if len(feasible_ranges) > 0:
                maxRange_payload[p_idx] = np.max(feasible_ranges)

        ax_env_tech.plot(maxRange_payload, payload_vec, linewidth=2, label=b['name'])

    ax_env_tech.set_xlabel('Maximum Feasible Range (km)')
    ax_env_tech.set_ylabel('Payload Mass (kg)')
    ax_env_tech.set_title('Payload–Range Envelopes (Battery Technology Sensitivity)')
    ax_env_tech.legend(loc='best')
    ax_env_tech.grid(True)
    fig_env_tech.tight_layout()
    if save_dir:
        fig_env_tech.savefig(os.path.join(save_dir, "fig_payload_range_battery_tech.png"), dpi=300)

    # =========================================================================
    # SECTION 14 — BATTERY DEGRADATION SENSITIVITY
    # =========================================================================
    degradation_levels = [0.0, 0.15, 0.30]
    fig_deg, ax_deg = plt.subplots(figsize=(8, 5))

    for deg in degradation_levels:
        Whkg_eff = batteryTech[0]['Whkg'] * (1.0 - deg)
        maxRange_degraded = np.full(len(payload_vec), np.nan)

        for p_idx, payload in enumerate(payload_vec):
            feasible_ranges = []
            for range_km in range_vec:
                W0 = (payload + 4.0) * g
                S  = W0 / WS_baseline
                CL = W0 / (0.5 * rho_baseline * (V_baseline ** 2) * S)
                if CL > CL_max_allow:
                    continue

                CD = CD0 + (CL ** 2) / (np.pi * e * AR_baseline)
                Drag = 0.5 * rho_baseline * (V_baseline ** 2) * S * CD
                Power_req = Drag * V_baseline / eta_total

                cruise_time_hr = range_km * 1000.0 / V_baseline / 3600.0
                Energy_req = Power_req * (cruise_time_hr + baselineMission['loiter_hr'])

                batt_mass = Energy_req / Whkg_eff
                struct_mass = k_struct * (batt_mass + payload)
                total_mass = batt_mass + struct_mass + payload + misc_mass_kg
                Energy_avail = batt_mass * Whkg_eff

                if Energy_avail >= Energy_req and total_mass < 30.0:
                    feasible_ranges.append(range_km)

            if len(feasible_ranges) > 0:
                maxRange_degraded[p_idx] = np.max(feasible_ranges)

        ax_deg.plot(maxRange_degraded, payload_vec, linewidth=2, label=f"{int(deg * 100)}% Degradation")

    ax_deg.set_xlabel('Maximum Feasible Range (km)')
    ax_deg.set_ylabel('Payload Mass (kg)')
    ax_deg.set_title('Payload–Range Envelope with Battery Degradation')
    ax_deg.legend(loc='best')
    ax_deg.grid(True)
    fig_deg.tight_layout()
    if save_dir:
        fig_deg.savefig(os.path.join(save_dir, "fig_payload_range_degradation.png"), dpi=300)

    # =========================================================================
    # SECTION 15 — MISSION CLUSTERING
    # =========================================================================
    missionFeatures = np.zeros((nMissions, 4))
    for m_idx, m in enumerate(missions):
        missionFeatures[m_idx, :] = [m['range_km'], m['loiter_hr'], m['payload_kg'], m['V_cruise']]

    nClusters = 3
    kmeans = KMeans(n_clusters=nClusters, random_state=42, n_init=10).fit(missionFeatures)
    idx = kmeans.labels_ + 1  # 1-based indexing to match MATLAB

    fig_clust, ax_clust = plt.subplots(figsize=(7, 5))
    colors = ['r', 'g', 'b']
    for c in range(1, nClusters + 1):
        c_mask = (idx == c)
        ax_clust.scatter(missionFeatures[c_mask, 0], missionFeatures[c_mask, 1],
                         c=colors[c - 1], s=100, label=f'Cluster {c}')
    ax_clust.set_xlabel('Mission Range (km)')
    ax_clust.set_ylabel('Loiter Time (hr)')
    ax_clust.set_title('Mission Clustering in Requirement Space')
    ax_clust.legend(loc='best')
    ax_clust.grid(True)
    fig_clust.tight_layout()
    if save_dir:
        fig_clust.savefig(os.path.join(save_dir, "fig_mission_clustering.png"), dpi=300)

    # =========================================================================
    # SECTION 16 — CONFIGURATION FAMILIES PER MISSION CLUSTER
    # =========================================================================
    print("\n" + "=" * 52)
    print("CONFIGURATION FAMILIES (MISSION CLUSTERS)")
    print("=" * 52)

    for c in range(1, nClusters + 1):
        clusterMissionIDs = np.where(idx == c)[0] + 1
        clusterDesigns = DesignDB[DesignDB['MissionID'].isin(clusterMissionIDs) & DesignDB['Pareto']]

        if clusterDesigns.empty:
            print(f"\nCluster {c}: No feasible Pareto designs")
            continue

        avgAR = clusterDesigns['AspectRatio'].mean()
        avgWS = clusterDesigns['WingLoading'].mean()
        avgMass = clusterDesigns['TotalMass_kg'].mean()
        avgEndurance = clusterDesigns['Endurance_hr'].mean()

        print(f"\nCluster {c} Summary:")
        print(f"  Avg Aspect Ratio      : {avgAR:.2f}")
        print(f"  Avg Wing Loading      : {avgWS:.1f} N/m^2")
        print(f"  Avg Total Mass        : {avgMass:.2f} kg")
        print(f"  Avg Endurance         : {avgEndurance:.2f} hr")

    # =========================================================================
    # SECTION 17 — FINAL SYSTEM-LEVEL INSIGHTS
    # =========================================================================
    print("\n" + "=" * 52)
    print("KEY SYSTEM-LEVEL INSIGHTS")
    print("=" * 52)
    print("• Mission feasibility is energy-limited, not geometry-limited.")
    print("• Payload–range envelopes shrink nonlinearly with battery degradation.")
    print("• Advanced batteries reshape mission capability more than aerodynamics.")
    print("• Distinct mission clusters map to distinct configuration families.")
    print("• No single UAV configuration is globally optimal.\n")

    if show_plots:
        plt.show()

    return DesignDB

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Project 2 As-Is Trade Space Exploration")
    parser.add_argument("--show", action="store_true", help="Display interactive plots")
    parser.add_argument("--save-dir", type=str, default="output_figures", help="Directory to save figures")
    args = parser.parse_args()

    run_trade_space(show_plots=args.show, save_dir=args.save_dir)
