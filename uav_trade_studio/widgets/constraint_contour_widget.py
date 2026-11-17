# 2D design constraint contour widget with interactive flight feasibility overlays

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class ConstraintContourWidget(QWidget):
    # Renders 2D design space isolines and overlays stall and MTOW safety boundaries
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_ar_vec = None
        self.cached_s_vec = None
        self.cached_data = None
        self.active_point = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Metric Selector Header
        header = QHBoxLayout()
        header_lbl = QLabel("Display Metric:")
        header_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")

        self.combo_metric = QComboBox()
        self.combo_metric.addItems(
            [
                "Endurance (hr)",
                "Energy Margin (%)",
                "Gross Takeoff Mass (MTOW [kg])",
                "Stall Speed (m/s)",
            ]
        )
        self.combo_metric.currentIndexChanged.connect(self.replot)
        header.addWidget(header_lbl)
        header.addWidget(self.combo_metric)
        header.addStretch()
        layout.addLayout(header)

        # High-Contrast Matplotlib Canvas
        self.fig = Figure(figsize=(6, 4.5), facecolor="#0f172a")
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111, facecolor="#0b0f19")
        layout.addWidget(self.canvas)

    def update_contours(
        self,
        ar_vec: np.ndarray,
        s_vec: np.ndarray,
        data_dict: dict,
        active_point: tuple = None,
    ):
        # Caches current sweep matrices and updates plot
        self.cached_ar_vec = ar_vec
        self.cached_s_vec = s_vec
        self.cached_data = data_dict
        self.active_point = active_point
        self.replot()

    def update_active_point(self, active_point: tuple):
        # Rapidly updates the active design marker without recomputing full grid
        self.active_point = active_point
        self.replot()

    def replot(self):
        # Draws filled contour map and constraint boundary lines
        if self.cached_data is None:
            return

        self.fig.clear()
        self.ax = self.fig.add_subplot(111, facecolor="#0b0f19")

        ar_vec = self.cached_ar_vec
        s_vec = self.cached_s_vec
        metric_idx = self.combo_metric.currentIndex()

        metric_keys = ["endurance", "energy_margin", "mtow", "stall_speed"]
        colormaps = ["viridis", "plasma", "cividis", "magma"]
        titles = [
            "Max Loiter Endurance (hr)",
            "Usable Energy Margin (%)",
            "Gross Takeoff Mass (kg)",
            "Launch Stall Speed (m/s)",
        ]

        key = metric_keys[metric_idx]
        cmap = colormaps[metric_idx]
        title = titles[metric_idx]
        z_matrix = self.cached_data[key]

        # Filled Contours
        cs = self.ax.contourf(ar_vec, s_vec, z_matrix, levels=14, cmap=cmap)
        cbar = self.fig.colorbar(cs, ax=self.ax)
        cbar.set_label(title, color="#e2e8f0", fontsize=9)
        cbar.ax.yaxis.set_tick_params(color="#94a3b8")
        for t in cbar.ax.get_yticklabels():
            t.set_color("#94a3b8")

        # Contour Isolines
        lines = self.ax.contour(
            ar_vec,
            s_vec,
            z_matrix,
            levels=8,
            colors="white",
            alpha=0.25,
            linewidths=0.7,
        )
        self.ax.clabel(lines, inline=True, fontsize=8, fmt="%.1f")

        # Stall constraint boundary: V_stall <= 15.0 m/s
        stall_matrix = self.cached_data.get("stall_speed")
        if stall_matrix is not None:
            self.ax.contour(
                ar_vec,
                s_vec,
                stall_matrix,
                levels=[14.5],
                colors="#ef4444",
                linestyles="--",
                linewidths=1.8,
            )

        # MTOW regulatory constraint boundary: MTOW <= 25.0 kg
        mtow_matrix = self.cached_data.get("mtow")
        if mtow_matrix is not None and np.nanmax(mtow_matrix) >= 24.5:
            self.ax.contour(
                ar_vec,
                s_vec,
                mtow_matrix,
                levels=[25.0],
                colors="#f59e0b",
                linestyles="-.",
                linewidths=1.8,
            )

        # Active Design Point Crosshair Marker
        if self.active_point is not None:
            ar_pt, s_pt = self.active_point
            self.ax.scatter(
                ar_pt,
                s_pt,
                color="#38bdf8",
                s=140,
                marker="*",
                edgecolors="white",
                linewidths=1.2,
                zorder=5,
            )
            self.ax.axvline(
                ar_pt, color="#38bdf8", linestyle=":", alpha=0.4, linewidth=1.0
            )
            self.ax.axhline(
                s_pt, color="#38bdf8", linestyle=":", alpha=0.4, linewidth=1.0
            )

        # Visual Styling
        self.ax.set_title(title, color="#e2e8f0", fontsize=10, fontweight="bold")
        self.ax.set_xlabel("Aspect Ratio (AR)", color="#94a3b8", fontsize=9)
        self.ax.set_ylabel("Wing Surface Area ($m^2$)", color="#94a3b8", fontsize=9)
        self.ax.tick_params(colors="#94a3b8")
        self.ax.grid(True, linestyle=":", alpha=0.25, color="#64748b")

        self.fig.tight_layout()
        self.canvas.draw()
