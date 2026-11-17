# 3D interactive design trade space surface visualization widget

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class TradeSpace3DWidget(QWidget):
    # Renders 3D response surface over aspect ratio and wing area with interactive rotation
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_ar_grid = None
        self.cached_s_grid = None
        self.cached_data = None
        self.active_design = None
        self.current_elev = 26
        self.current_azim = -120
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Metric Selector
        header = QHBoxLayout()
        header_lbl = QLabel("3D Response Metric:")
        header_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")

        self.combo_metric = QComboBox()
        self.combo_metric.addItems(
            [
                "Max Endurance (hr)",
                "Gross Takeoff Mass (MTOW [kg])",
                "Energy Margin (%)",
            ]
        )
        self.combo_metric.currentIndexChanged.connect(self.replot)
        header.addWidget(header_lbl)
        header.addWidget(self.combo_metric)
        header.addStretch()
        layout.addLayout(header)

        # 3D Canvas
        self.fig = Figure(figsize=(6, 4.5), facecolor="#0f172a")
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

    def update_surface(
        self,
        ar_grid: np.ndarray,
        s_grid: np.ndarray,
        data_dict: dict,
        active_design: dict = None,
    ):
        # Updates design surface grid data and active configuration marker
        self.cached_ar_grid = ar_grid
        self.cached_s_grid = s_grid
        self.cached_data = data_dict
        self.active_design = active_design
        self.replot()

    def update_active_marker(self, active_design: dict):
        # Updates active marker position while preserving 3D surface mesh
        self.active_design = active_design
        self.replot()

    def replot(self):
        # Renders 3D surface and active operating point while preserving camera viewpoint
        if self.cached_data is None:
            return

        # Preserve user camera orientation if already rotated
        if hasattr(self, "ax") and self.ax is not None:
            self.current_elev = self.ax.elev
            self.current_azim = self.ax.azim

        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection="3d", facecolor="#0b0f19")
        self.ax.set_facecolor("#0b0f19")

        ar_grid = self.cached_ar_grid
        s_grid = self.cached_s_grid
        metric_idx = self.combo_metric.currentIndex()

        keys = ["endurance", "mtow", "energy_margin"]
        cmaps = ["viridis", "cividis", "plasma"]
        titles = ["Max Endurance (hr)", "Gross Mass (kg)", "Energy Margin (%)"]

        key = keys[metric_idx]
        cmap = cmaps[metric_idx]
        title = titles[metric_idx]
        z_grid = self.cached_data[key]

        # 3D Surface Mesh
        surf = self.ax.plot_surface(
            ar_grid,
            s_grid,
            z_grid,
            cmap=cmap,
            edgecolor="none",
            alpha=0.90,
            antialiased=True,
        )
        cbar = self.fig.colorbar(surf, ax=self.ax, shrink=0.55, aspect=10, pad=0.08)
        cbar.set_label(title, color="#e2e8f0", fontsize=9)
        cbar.ax.yaxis.set_tick_params(color="#94a3b8")
        for t in cbar.ax.get_yticklabels():
            t.set_color("#94a3b8")

        # Active Design Marker
        if self.active_design is not None:
            ar_pt = self.active_design.get("aspect_ratio", 12.0)
            s_pt = self.active_design.get("wing_area", 0.8)
            z_pt = self.active_design.get(
                "max_endurance"
                if key == "endurance"
                else "MTOW"
                if key == "mtow"
                else "energy_margin",
                0.0,
            )
            self.ax.scatter(
                [ar_pt],
                [s_pt],
                [z_pt],
                color="#38bdf8",
                s=120,
                marker="o",
                edgecolors="white",
                linewidths=1.5,
                zorder=6,
            )

        # Axis Labels & Camera Angles
        self.ax.set_title(
            title, color="#e2e8f0", fontsize=10, fontweight="bold", pad=10
        )
        self.ax.set_xlabel("Aspect Ratio (AR)", color="#94a3b8", fontsize=9, labelpad=8)
        self.ax.set_ylabel("Wing Area ($m^2$)", color="#94a3b8", fontsize=9, labelpad=8)
        self.ax.set_zlabel(title, color="#94a3b8", fontsize=9, labelpad=8)
        self.ax.tick_params(colors="#94a3b8")
        self.ax.view_init(elev=self.current_elev, azim=self.current_azim)

        self.fig.tight_layout()
        self.canvas.draw()
