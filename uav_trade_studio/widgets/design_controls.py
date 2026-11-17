# Interactive slider and selection controls for real-time MDO trade exploration

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class DesignControlsWidget(QWidget):
    # Emits parameter dictionary when any control or slider is adjusted
    parametersChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.block_signals = False
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Mission Preset Selector
        mission_group = QGroupBox("Mission Scenario Preset")
        mission_layout = QVBoxLayout(mission_group)
        self.combo_mission = QComboBox()
        self.combo_mission.addItems(
            [
                "Mission 1: Surveillance & Mapping (Long Endurance)",
                "Mission 2: Heavy Payload Transport",
                "Mission 3: High-Speed Tactical Dash",
                "Custom Mission Specification",
            ]
        )
        self.combo_mission.currentIndexChanged.connect(self.on_mission_preset_changed)
        mission_layout.addWidget(self.combo_mission)
        main_layout.addWidget(mission_group)

        # Aircraft Geometric Design Sliders
        geom_group = QGroupBox("Airframe Geometry")
        geom_layout = QVBoxLayout(geom_group)

        # Aspect Ratio slider (6.0 to 18.0)
        self.slider_ar, self.label_ar_val = self.create_slider_row(
            "Aspect Ratio (AR):", 60, 180, 120, 0.1, ""
        )
        geom_layout.addLayout(self.slider_ar)

        # Wing Area slider (0.5 to 2.5 m^2)
        self.slider_s, self.label_s_val = self.create_slider_row(
            "Wing Area (S):", 50, 250, 80, 0.01, " m²"
        )
        geom_layout.addLayout(self.slider_s)
        main_layout.addWidget(geom_group)

        # Payload & Mission Operational Parameters
        ops_group = QGroupBox("Payload & Operational Flight")
        ops_layout = QVBoxLayout(ops_group)

        # Payload Mass slider (0.5 to 4.0 kg)
        self.slider_payload, self.label_payload_val = self.create_slider_row(
            "Payload Mass:", 5, 40, 12, 0.1, " kg"
        )
        ops_layout.addLayout(self.slider_payload)

        # Cruise Airspeed slider (15 to 30 m/s)
        self.slider_vcruise, self.label_vcruise_val = self.create_slider_row(
            "Cruise Speed:", 15, 30, 18, 1.0, " m/s"
        )
        ops_layout.addLayout(self.slider_vcruise)

        # Transit Range slider (20 to 120 km)
        self.slider_range, self.label_range_val = self.create_slider_row(
            "Transit Range:", 20, 120, 60, 1.0, " km"
        )
        ops_layout.addLayout(self.slider_range)

        # Loiter Duration slider (0.5 to 4.0 hr)
        self.slider_loiter, self.label_loiter_val = self.create_slider_row(
            "Loiter Duration:", 5, 40, 25, 0.1, " hr"
        )
        ops_layout.addLayout(self.slider_loiter)
        main_layout.addWidget(ops_group)

        # Electrochemical Battery Parameters
        batt_group = QGroupBox("Battery Technology & State")
        batt_layout = QVBoxLayout(batt_group)

        self.combo_battery = QComboBox()
        self.combo_battery.addItems(
            [
                "Lithium-Ion (220 Wh/kg — Baseline)",
                "Lithium-Sulfur (400 Wh/kg — Advanced)",
                "Solid-State (500 Wh/kg — Next-Gen)",
            ]
        )
        self.combo_battery.currentIndexChanged.connect(self.emit_all_parameters)
        batt_layout.addWidget(self.combo_battery)

        # Battery Capacity Degradation (0% to 30%)
        self.slider_deg, self.label_deg_val = self.create_slider_row(
            "Capacity Fade (EOL):", 0, 30, 0, 1.0, " %"
        )
        batt_layout.addLayout(self.slider_deg)
        main_layout.addWidget(batt_group)

        main_layout.addStretch()

    def create_slider_row(
        self,
        title: str,
        min_val: int,
        max_val: int,
        default_val: int,
        scale: float,
        unit: str,
    ):
        # Helper to construct a labeled slider row with live numerical feedback
        row = QHBoxLayout()
        name_lbl = QLabel(title)
        name_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        name_lbl.setFixedWidth(120)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)

        val_lbl = QLabel(f"{default_val * scale:.2f}{unit}")
        val_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        val_lbl.setFixedWidth(65)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        slider.valueChanged.connect(
            lambda v, s=scale, u=unit, l=val_lbl: self.on_slider_value_changed(
                v, s, u, l
            )
        )

        row.addWidget(name_lbl)
        row.addWidget(slider)
        row.addWidget(val_lbl)
        return row, val_lbl

    def on_slider_value_changed(
        self, raw_val: int, scale: float, unit: str, label: QLabel
    ):
        # Updates numerical text and triggers parameter broadcast
        label.setText(f"{raw_val * scale:.2f}{unit}")
        self.emit_all_parameters()

    def on_mission_preset_changed(self, index: int):
        # Automatically updates sliders to match chosen benchmark mission specifications
        presets = [
            {"payload": 1.2, "speed": 18.0, "range": 60.0, "loiter": 2.5},  # M1
            {"payload": 2.8, "speed": 20.0, "range": 80.0, "loiter": 0.5},  # M2
            {"payload": 1.0, "speed": 26.0, "range": 100.0, "loiter": 0.5},  # M3
        ]
        if index < len(presets):
            p = presets[index]
            self.block_signals = True
            self.slider_payload.itemAt(1).widget().setValue(int(p["payload"] * 10))
            self.slider_vcruise.itemAt(1).widget().setValue(int(p["speed"]))
            self.slider_range.itemAt(1).widget().setValue(int(p["range"]))
            self.slider_loiter.itemAt(1).widget().setValue(int(p["loiter"] * 10))
            self.block_signals = False
            self.emit_all_parameters()

    def get_current_parameters(self) -> dict:
        # Packages active slider settings into a clean parameter dictionary
        ar = self.slider_ar.itemAt(1).widget().value() * 0.1
        s = self.slider_s.itemAt(1).widget().value() * 0.01
        payload = self.slider_payload.itemAt(1).widget().value() * 0.1
        vcruise = float(self.slider_vcruise.itemAt(1).widget().value())
        range_km = float(self.slider_range.itemAt(1).widget().value())
        loiter = self.slider_loiter.itemAt(1).widget().value() * 0.1
        degradation = self.slider_deg.itemAt(1).widget().value() * 0.01

        tech_energies = [220.0, 400.0, 500.0]
        spec_energy = tech_energies[self.combo_battery.currentIndex()]

        return {
            "aspect_ratio": float(ar),
            "wing_area": float(s),
            "payload_mass": float(payload),
            "V_cruise": float(vcruise),
            "range_km": float(range_km),
            "t_loiter": float(loiter),
            "specific_energy": float(spec_energy),
            "degradation": float(degradation),
        }

    def emit_all_parameters(self):
        # Broadcasts parameter dictionary when not blocked during preset switching
        if not self.block_signals:
            params = self.get_current_parameters()
            self.parametersChanged.emit(params)
