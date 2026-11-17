# Real-time HUD aircraft telemetry and mass budget specification card

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
)


class AircraftSpecCard(QFrame):
    # Displays real-time sizing metrics, mass breakdown, and airworthiness status
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Airworthiness status badge
        self.badge_label = QLabel("AIRWORTHY & FEASIBLE")
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.setStyleSheet(
            "background-color: #065f46; color: #34d399; font-weight: bold; "
            "padding: 6px; border-radius: 4px; font-size: 11px; letter-spacing: 1px;"
        )
        main_layout.addWidget(self.badge_label)

        # Core Flight Performance Telemetry
        perf_group = QGroupBox("Flight Performance")
        perf_layout = QGridLayout(perf_group)
        self.labels = {}

        metrics = [
            ("Takeoff Mass (MTOW)", "0.0 kg"),
            ("Wing Span (b)", "0.0 m"),
            ("Wing Loading (W/S)", "0.0 N/m²"),
            ("Lift-to-Drag (L/D)", "0.0"),
            ("Cruise Power", "0.0 W"),
            ("Stall Speed", "0.0 m/s"),
            ("Max Endurance", "0.0 hr"),
            ("Energy Margin", "0.0 %"),
        ]

        for idx, (name, init_val) in enumerate(metrics):
            row = idx // 2
            col = (idx % 2) * 2
            name_lbl = QLabel(name + ":")
            name_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            val_lbl = QLabel(init_val)
            val_lbl.setStyleSheet("font-weight: 600; color: #38bdf8; font-size: 12px;")
            perf_layout.addWidget(name_lbl, row, col)
            perf_layout.addWidget(val_lbl, row, col + 1)
            self.labels[name] = val_lbl

        main_layout.addWidget(perf_group)

        # Mass Budget Breakdown
        mass_group = QGroupBox("Mass Budget Breakdown")
        mass_layout = QGridLayout(mass_group)
        self.mass_labels = {}

        mass_items = [
            ("Payload", "0.0 kg"),
            ("Battery Pack", "0.0 kg"),
            ("Wing Structure", "0.0 kg"),
            ("Fuselage & Tail", "0.0 kg"),
            ("Avionics / Hotel", "0.0 kg"),
            ("Structural Spar", "0.0 kg"),
        ]

        for idx, (name, init_val) in enumerate(mass_items):
            row = idx // 2
            col = (idx % 2) * 2
            name_lbl = QLabel(name + ":")
            name_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            val_lbl = QLabel(init_val)
            val_lbl.setStyleSheet("font-weight: 600; color: #e2e8f0; font-size: 12px;")
            mass_layout.addWidget(name_lbl, row, col)
            mass_layout.addWidget(val_lbl, row, col + 1)
            self.mass_labels[name] = val_lbl

        main_layout.addWidget(mass_group)
        main_layout.addStretch()

    def update_specs(self, res: dict):
        # Updates telemetry readout values and status badge based on sizing output
        if not res.get("converged", False):
            self.badge_label.setText("NUMERICAL DIVERGENCE / OVERLOAD")
            self.badge_label.setStyleSheet(
                "background-color: #7f1d1d; color: #f87171; font-weight: bold; "
                "padding: 6px; border-radius: 4px; font-size: 11px;"
            )
            return

        # Update flight metrics
        self.labels["Takeoff Mass (MTOW)"].setText(f"{res['MTOW']:.2f} kg")
        self.labels["Wing Span (b)"].setText(f"{res['span']:.2f} m")
        self.labels["Wing Loading (W/S)"].setText(f"{res['wing_loading']:.1f} N/m²")
        self.labels["Lift-to-Drag (L/D)"].setText(f"{res['lift_to_drag_cruise']:.1f}")
        self.labels["Cruise Power"].setText(f"{res['P_cruise']:.0f} W")
        self.labels["Stall Speed"].setText(f"{res['V_stall']:.1f} m/s")
        self.labels["Max Endurance"].setText(f"{res['max_endurance']:.2f} hr")
        self.labels["Energy Margin"].setText(f"{res['energy_margin']:+.1f} %")

        # Update mass breakdown
        self.mass_labels["Payload"].setText(f"{res['m_payload']:.2f} kg")
        self.mass_labels["Battery Pack"].setText(f"{res['m_batt']:.2f} kg")
        self.mass_labels["Wing Structure"].setText(f"{res.get('m_wing', 0.0):.2f} kg")
        self.mass_labels["Fuselage & Tail"].setText(
            f"{res.get('m_fuse_tail', 0.0):.2f} kg"
        )
        self.mass_labels["Avionics / Hotel"].setText(f"{res['m_avionics']:.2f} kg")
        self.mass_labels["Structural Spar"].setText(f"{res.get('m_spar', 0.0):.2f} kg")

        # Update safety status
        if res.get("feasible", False):
            self.badge_label.setText("AIRWORTHY & FEASIBLE")
            self.badge_label.setStyleSheet(
                "background-color: #065f46; color: #34d399; font-weight: bold; "
                "padding: 6px; border-radius: 4px; font-size: 11px;"
            )
        else:
            reasons = []
            c = res.get("constraints", {})
            if not c.get("stall_valid", True):
                reasons.append("STALL")
            if not c.get("mtow_valid", True):
                reasons.append("MTOW")
            if not c.get("energy_valid", True):
                reasons.append("ENERGY")
            reason_str = " / ".join(reasons) if reasons else "CONSTRAINT VIOLATION"
            self.badge_label.setText(f"INFEASIBLE ({reason_str})")
            self.badge_label.setStyleSheet(
                "background-color: #7f1d1d; color: #f87171; font-weight: bold; "
                "padding: 6px; border-radius: 4px; font-size: 11px;"
            )
