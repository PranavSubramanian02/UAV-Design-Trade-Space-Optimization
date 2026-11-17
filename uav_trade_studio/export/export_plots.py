# Publication-grade figure generator for MDO trade studies and Pareto fronts

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mdo_core.analysis.battery_sensitivity import (
    compute_degradation_curves,
    compute_payload_range_curves,
)
from mdo_core.analysis.mission_clustering import cluster_mission_configurations
from mdo_core.optimization.design_space import (
    evaluate_design_point,
    evaluate_grid,
    generate_lhs_samples,
    generate_regular_grid,
    get_benchmark_missions,
)
from mdo_core.optimization.pareto_optimizer import extract_pareto_front


def plot_trade_space_3d(
    ar_grid: np.ndarray,
    s_grid: np.ndarray,
    z_matrix: np.ndarray,
    mission_name: str,
    output_path: str,
    dpi: int = 300,
):
    # Generates a 3D response surface plot of endurance over aspect ratio and wing area
    fig = plt.figure(figsize=(9, 6.5))
    ax = fig.add_subplot(111, projection="3d")

    surf = ax.plot_surface(
        ar_grid,
        s_grid,
        z_matrix,
        cmap="viridis",
        edgecolor="none",
        alpha=0.92,
        antialiased=True,
    )
    cbar = fig.colorbar(surf, ax=ax, shrink=0.55, aspect=10, pad=0.08)
    cbar.set_label("Max Loiter Endurance (hr)", fontsize=10)

    ax.set_title(
        f"3D Design Trade Space — {mission_name}",
        fontsize=11,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Aspect Ratio (AR)", fontsize=10, labelpad=8)
    ax.set_ylabel("Wing Surface Area ($m^2$)", fontsize=10, labelpad=8)
    ax.set_zlabel("Endurance (hr)", fontsize=10, labelpad=8)
    ax.view_init(elev=28, azim=-125)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_2d_contour(
    ar_vec: np.ndarray,
    s_vec: np.ndarray,
    z_matrix: np.ndarray,
    mission_name: str,
    metric_label: str,
    output_path: str,
    stall_matrix: np.ndarray = None,
    cmap: str = "viridis",
    dpi: int = 300,
):
    # Generates a 2D filled contour map with flight feasibility constraint boundaries
    fig, ax = plt.subplots(figsize=(7.5, 5.5))

    cs = ax.contourf(ar_vec, s_vec, z_matrix, levels=14, cmap=cmap)
    cbar = fig.colorbar(cs, ax=ax)
    cbar.set_label(metric_label, fontsize=10)

    lines = ax.contour(
        ar_vec, s_vec, z_matrix, levels=8, colors="white", alpha=0.35, linewidths=0.8
    )
    ax.clabel(lines, inline=True, fontsize=8, fmt="%.1f")

    # Stall speed boundary constraint (V_stall <= 15 m/s)
    if stall_matrix is not None:
        ax.contour(
            ar_vec,
            s_vec,
            stall_matrix,
            levels=[14.0],
            colors="#ef4444",
            linestyles="--",
            linewidths=1.8,
        )

    ax.set_title(
        f"{metric_label} Contour — {mission_name}", fontsize=11, fontweight="bold"
    )
    ax.set_xlabel("Aspect Ratio (AR)", fontsize=10)
    ax.set_ylabel("Wing Area ($m^2$)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.4)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_global_pareto_front(
    pareto_records: list, knee_record: dict, output_path: str, dpi: int = 300
):
    # Generates the multi-objective Pareto frontier plotting Mass vs Endurance vs Payload
    fig, ax = plt.subplots(figsize=(8, 5.5))

    mtow = [r["MTOW"] for r in pareto_records]
    endur = [r["max_endurance"] for r in pareto_records]
    payload = [r["m_payload"] for r in pareto_records]

    scatter = ax.scatter(
        mtow,
        endur,
        c=payload,
        cmap="plasma",
        s=70,
        edgecolors="#1e293b",
        linewidth=0.8,
        zorder=3,
    )
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Payload Capacity (kg)", fontsize=10)

    # Highlight the knee point configuration
    if knee_record:
        ax.scatter(
            knee_record["MTOW"],
            knee_record["max_endurance"],
            color="#ef4444",
            s=160,
            marker="*",
            edgecolors="black",
            zorder=4,
            label=f"Knee Compromise ({knee_record['MTOW']:.1f} kg, {knee_record['max_endurance']:.1f} hr)",
        )
        ax.legend(loc="upper left", framealpha=0.9, fontsize=9)

    ax.set_title(
        "Global Pareto Frontier (NSGA-II Non-Dominated Set)",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlabel("Takeoff Gross Mass (MTOW [kg])", fontsize=10)
    ax.set_ylabel("Max Flight Endurance (hr)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_payload_range_technologies(data: dict, output_path: str, dpi: int = 300):
    # Generates the payload-range envelope comparing Li-ion, Li-S, and Solid-State batteries
    fig, ax = plt.subplots(figsize=(8, 5))
    payloads = data["payload_vec"]
    curves = data["curves"]
    colors = ["#0284c7", "#10b981", "#8b5cf6"]

    for (tech_name, ranges), color in zip(curves.items(), colors):
        ax.plot(ranges, payloads, label=tech_name, color=color, linewidth=2.2)

    ax.set_title(
        "Payload–Range Envelope: Battery Chemistry Comparison",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlabel("Flight Range (km)", fontsize=10)
    ax.set_ylabel("Payload Mass (kg)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_payload_range_degradation(data: dict, output_path: str, dpi: int = 300):
    # Generates the operational degradation payload-range envelope (0%, 15%, 30% fade)
    fig, ax = plt.subplots(figsize=(8, 5))
    payloads = data["payload_vec"]
    curves = data["curves"]
    colors = ["#10b981", "#f59e0b", "#ef4444"]

    for (deg_label, ranges), color in zip(curves.items(), colors):
        ax.plot(ranges, payloads, label=deg_label, color=color, linewidth=2.2)

    ax.set_title(
        "Payload–Range Sensitivity to Battery Capacity Fade",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlabel("Flight Range (km)", fontsize=10)
    ax.set_ylabel("Payload Mass (kg)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_mission_clusters(cluster_data: dict, output_path: str, dpi: int = 300):
    # Generates scatter visualization of mission configuration family clusters
    fig, ax = plt.subplots(figsize=(8, 5.5))
    clusters = cluster_data.get("clusters", {})
    colors = ["#0284c7", "#10b981", "#8b5cf6"]

    for (fam_name, info), color in zip(clusters.items(), colors):
        rep = info["representative_design"]
        ax.scatter(
            info["avg_aspect_ratio"],
            info["avg_endurance"],
            s=info["n_designs"] * 35 + 80,
            color=color,
            alpha=0.75,
            edgecolors="#0f172a",
            linewidth=1.2,
            label=f"{fam_name} (N={info['n_designs']})",
        )
        ax.annotate(
            f"MTOW ~ {info['avg_mtow']:.1f} kg\nPayload ~ {info['avg_payload']:.1f} kg",
            (info["avg_aspect_ratio"], info["avg_endurance"]),
            textcoords="offset points",
            xytext=(10, 8),
            fontsize=8,
            fontweight="semibold",
        )

    score = cluster_data.get("silhouette_score", 0.0)
    ax.set_title(
        f"Mission-Driven Configuration Families (Silhouette Score: {score:.2f})",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlabel("Average Aspect Ratio (AR)", fontsize=10)
    ax.set_ylabel("Average Flight Endurance (hr)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="lower right", framealpha=0.9, fontsize=9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def export_all_publication_figures(output_dir: str = "output_figures", dpi: int = 300):
    # Batch generates and exports all 13 publication-grade figures matching the baseline suite
    os.makedirs(output_dir, exist_ok=True)
    missions = get_benchmark_missions()
    ar_vec, s_vec, ar_grid, s_grid = generate_regular_grid(n_ar=20, n_s=20)
    all_pareto_records = []

    # 1. Generate 3D trade space surfaces and 2D contour maps for each mission
    for idx, mission in enumerate(missions, start=1):
        grid_data = evaluate_grid(ar_vec, s_vec, mission)

        # 3D Trade Space
        path_3d = os.path.join(output_dir, f"fig_trade_space_3d_m{idx}.png")
        plot_trade_space_3d(
            ar_grid, s_grid, grid_data["endurance"], mission["name"], path_3d, dpi=dpi
        )

        # 2D Endurance Contour
        path_endur = os.path.join(output_dir, f"fig_endurance_contour_m{idx}.png")
        plot_2d_contour(
            ar_vec,
            s_vec,
            grid_data["endurance"],
            mission["name"],
            "Endurance (hr)",
            path_endur,
            stall_matrix=grid_data["stall_speed"],
            dpi=dpi,
        )

        # 2D Energy Margin Contour (Dynamic, non-zero reserve isolines)
        path_margin = os.path.join(output_dir, f"fig_energy_margin_contour_m{idx}.png")
        plot_2d_contour(
            ar_vec,
            s_vec,
            grid_data["energy_margin"],
            mission["name"],
            "Energy Margin (%)",
            path_margin,
            cmap="plasma",
            dpi=dpi,
        )

        # Collect LHS samples for global Pareto extraction
        lhs_pts = generate_lhs_samples(n_samples=35, seed=idx * 10)
        for pt in lhs_pts:
            res = evaluate_design_point(pt[0], pt[1], mission)
            if res["converged"]:
                res["mission_name"] = mission["name"]
                all_pareto_records.append(res)

    # 2. Global Pareto Frontier
    pareto_dict = extract_pareto_front(all_pareto_records)
    path_pareto = os.path.join(output_dir, "fig_global_pareto_front.png")
    plot_global_pareto_front(
        pareto_dict["pareto_records"],
        pareto_dict["knee_record"],
        path_pareto,
        dpi=dpi,
    )

    # 3. Payload-Range Diagrams (Battery Technology & Degradation)
    pr_tech_data = compute_payload_range_curves(aspect_ratio=12.0, wing_area=0.8)
    path_pr_tech = os.path.join(output_dir, "fig_payload_range_battery_tech.png")
    plot_payload_range_technologies(pr_tech_data, path_pr_tech, dpi=dpi)

    pr_deg_data = compute_degradation_curves(aspect_ratio=12.0, wing_area=0.8)
    path_pr_deg = os.path.join(output_dir, "fig_payload_range_degradation.png")
    plot_payload_range_degradation(pr_deg_data, path_pr_deg, dpi=dpi)

    # 4. Mission Clustering
    if len(pareto_dict["pareto_records"]) >= 3:
        cluster_res = cluster_mission_configurations(
            pareto_dict["pareto_records"], n_clusters=3
        )
        path_cluster = os.path.join(output_dir, "fig_mission_clustering.png")
        plot_mission_clusters(cluster_res, path_cluster, dpi=dpi)
