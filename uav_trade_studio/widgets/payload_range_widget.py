# Interactive Payload–Range envelope and battery sensitivity diagram widget

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class PayloadRangeWidget(QWidget):
    # Renders payload-range curves comparing battery chemistries and operational degradation
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_tech_data = None
        self.cached_deg_data = None
        self.active_point = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Display Mode Header
        header = QHBoxLayout()
        header_lbl = QLabel("Envelope Mode:")
        header_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(
            [
                "Battery Chemistry Comparison (Li-ion vs Li-S vs Solid-State)",
                "Operational Life Capacity Degradation (0% vs 15% vs 30% Fade)",
            ]
        )
        self.combo_mode.currentIndexChanged.connect(self.replot)
        header.addWidget(header_lbl)
        header.addWidget(self.combo_mode)
        header.addStretch()
        layout.addLayout(header)

        # Canvas
        self.fig = Figure(figsize=(6, 4.5), facecolor="#0f172a")
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111, facecolor="#0b0f19")
        layout.addWidget(self.canvas)

    def update_data(self, tech_data: dict, deg_data: dict, active_point: tuple = None):
        # Caches computed envelopes and active design marker
        self.cached_tech_data = tech_data
        self.cached_deg_data = deg_data
        self.active_point = active_point
        self.replot()

    def update_active_point(self, active_point: tuple):
        # Updates active payload-range marker
        self.active_point = active_point
        self.replot()

    def replot(self):
        # Draws payload-range lines and active operating point
        if self.cached_tech_data is None:
            return

        self.fig.clear()
        self.ax = self.fig.add_subplot(111, facecolor="#0b0f19")

        mode_idx = self.combo_mode.currentIndex()
        if mode_idx == 0:
            # Battery Technology Mode
            data = self.cached_tech_data
            payloads = data["payload_vec"]
            curves = data["curves"]
            colors = ["#0284c7", "#10b981", "#8b5cf6"]
            title = "Payload–Range: Advanced Battery Chemistries"
        else:
            # Lifecycle Degradation Mode
            data = self.cached_deg_data
            payloads = data["payload_vec"]
            curves = data["curves"]
            colors = ["#10b981", "#f59e0b", "#ef4444"]
            title = "Payload–Range: Operational Battery Aging Fade"

        # Plot Range Curves
        for (label, ranges), color in zip(curves.items(), colors):
            self.ax.plot(ranges, payloads, label=label, color=color, linewidth=2.0)

        # Active Design Point Marker
        if self.active_point is not None:
            range_pt, payload_pt = self.active_point
            self.ax.scatter(
                range_pt,
                payload_pt,
                color="#38bdf8",
                s=120,
                marker="*",
                edgecolors="white",
                linewidths=1.2,
                zorder=5,
                label=f"Current Config ({range_pt:.1f} km, {payload_pt:.1f} kg)",
            )
            self.ax.axvline(range_pt, color="#38bdf8", linestyle=":", alpha=0.35)
            self.ax.axhline(payload_pt, color="#38bdf8", linestyle=":", alpha=0.35)

        # Styling
        self.ax.set_title(title, color="#e2e8f0", fontsize=10, fontweight="bold")
        self.ax.set_xlabel("Flight Range (km)", color="#94a3b8", fontsize=9)
        self.ax.set_ylabel("Payload Mass (kg)", color="#94a3b8", fontsize=9)
        self.ax.tick_params(colors="#94a3b8")
        self.ax.grid(True, linestyle=":", alpha=0.25, color="#64748b")
        self.ax.legend(loc="upper right", framealpha=0.85, fontsize=8)

        self.fig.tight_layout()
        self.canvas.draw()
