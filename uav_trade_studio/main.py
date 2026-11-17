# UAV Trade Studio — Main native PyQt6 desktop application entrypoint

import os
import sys
import ctypes

# Pre-load libxcb-cursor on Linux if missing from system ld cache
for _lib_path in [
    os.path.expanduser("~/.local/lib/libxcb-cursor.so.0"),
    os.path.expanduser("~/.local/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0"),
]:
    if os.path.exists(_lib_path):
        try:
            ctypes.CDLL(_lib_path)
            break
        except Exception:
            pass

# Ensure root of Project 2 is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from mdo_core.analysis.battery_sensitivity import (
    compute_degradation_curves,
    compute_payload_range_curves,
)
from mdo_core.optimization.design_space import (
    evaluate_grid,
    generate_regular_grid,
    get_benchmark_missions,
)
from mdo_core.sizing.converged_sizing_loop import solve_converged_sizing
from uav_trade_studio.export.export_plots import export_all_publication_figures
from uav_trade_studio.widgets.aircraft_spec_card import AircraftSpecCard
from uav_trade_studio.widgets.constraint_contour_widget import (
    ConstraintContourWidget,
)
from uav_trade_studio.widgets.design_controls import DesignControlsWidget
from uav_trade_studio.widgets.payload_range_widget import PayloadRangeWidget
from uav_trade_studio.widgets.trade_space_3d_widget import TradeSpace3DWidget


class UAVTradeStudioMainWindow(QMainWindow):
    # Main application window integrating sizing engine, controls, and 3D visualizers
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UAV Trade Studio — Multidisciplinary Design Optimization")
        self.resize(1400, 880)
        self.missions = get_benchmark_missions()
        self.current_mission = self.missions[0]

        self.init_ui()
        self.load_stylesheet()
        self.recompute_grid_and_curves()
        self.on_parameters_changed(self.controls_widget.get_current_parameters())

    def init_ui(self):
        # 1. Top Navigation Toolbar
        toolbar = QToolBar("Main Operations", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        action_export = QAction("Export All Publication Figures (PDF/PNG)", self)
        action_export.triggered.connect(self.on_export_figures)
        toolbar.addAction(action_export)

        action_recompute = QAction("Recompute Grid Manifold", self)
        action_recompute.triggered.connect(self.recompute_grid_and_curves)
        toolbar.addAction(action_recompute)

        # 2. Left Dock Widget: Controls & HUD Telemetry Card
        left_dock = QDockWidget("Design Configuration & Telemetry", self)
        left_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(8)

        self.controls_widget = DesignControlsWidget()
        self.controls_widget.parametersChanged.connect(self.on_parameters_changed)
        left_layout.addWidget(self.controls_widget)

        self.spec_card = AircraftSpecCard()
        left_layout.addWidget(self.spec_card)
        left_container.setLayout(left_layout)

        left_dock.setWidget(left_container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)

        # 3. Center Area: Multi-View Tabbed Visualizations
        self.tabs = QTabWidget()

        self.widget_3d = TradeSpace3DWidget()
        self.tabs.addTab(self.widget_3d, "3D Trade Space Exploration")

        self.widget_contour = ConstraintContourWidget()
        self.tabs.addTab(self.widget_contour, "2D Feasibility & Constraint Contours")

        self.widget_payload_range = PayloadRangeWidget()
        self.tabs.addTab(
            self.widget_payload_range, "Payload–Range & Battery Sensitivity"
        )

        self.setCentralWidget(self.tabs)

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("UAV Trade Studio Ready — Coupled Sizing Active")

    def load_stylesheet(self):
        # Loads dark aerospace theme stylesheet
        qss_path = os.path.join(
            os.path.dirname(__file__), "styles", "dark_aerospace.qss"
        )
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def recompute_grid_and_curves(self):
        # Re-evaluates 2D/3D response manifold across aspect ratio and wing area
        self.status_bar.showMessage(
            "Evaluating design grid manifold across design space..."
        )
        QApplication.processEvents()

        params = self.controls_widget.get_current_parameters()
        ar_vec, s_vec, ar_grid, s_grid = generate_regular_grid(n_ar=18, n_s=18)

        mission_dict = {
            "payload_kg": params["payload_mass"],
            "V_cruise": params["V_cruise"],
            "range_km": params["range_km"],
            "loiter_hr": params["t_loiter"],
            "battery_fraction": 0.35,
        }

        grid_data = evaluate_grid(
            ar_vec,
            s_vec,
            mission_dict,
            specific_energy=params["specific_energy"],
            degradation=params["degradation"],
        )

        self.widget_3d.update_surface(ar_grid, s_grid, grid_data)
        self.widget_contour.update_contours(ar_vec, s_vec, grid_data)

        # Update Payload-Range Curves
        pr_tech_data = compute_payload_range_curves(
            aspect_ratio=params["aspect_ratio"],
            wing_area=params["wing_area"],
            V_cruise=params["V_cruise"],
        )
        pr_deg_data = compute_degradation_curves(
            aspect_ratio=params["aspect_ratio"],
            wing_area=params["wing_area"],
            V_cruise=params["V_cruise"],
            base_specific_energy=params["specific_energy"],
        )
        self.widget_payload_range.update_data(pr_tech_data, pr_deg_data)
        self.status_bar.showMessage("Manifold update complete.")

    def on_parameters_changed(self, params: dict):
        # Solves converged Picard sizing in sub-milliseconds and updates HUD and markers
        res = solve_converged_sizing(
            aspect_ratio=params["aspect_ratio"],
            wing_area=params["wing_area"],
            m_payload=params["payload_mass"],
            V_cruise=params["V_cruise"],
            range_km=params["range_km"],
            t_loiter=params["t_loiter"],
            battery_spec_energy=params["specific_energy"],
            battery_degradation=params["degradation"],
            battery_fraction=0.35,
        )

        # Update spec card
        self.spec_card.update_specs(res)

        # Update active design markers
        ar_pt = params["aspect_ratio"]
        s_pt = params["wing_area"]
        self.widget_contour.update_active_point((ar_pt, s_pt))
        self.widget_3d.update_active_marker(res)

        # Update payload-range point
        if res["converged"]:
            flight_time = res["E_batt_usable"] / res["P_cruise"]
            curr_range = flight_time * (params["V_cruise"] * 3.6)
            self.widget_payload_range.update_active_point(
                (curr_range, params["payload_mass"])
            )

    def on_export_figures(self):
        # Triggers batch export of publication figures to output_figures directory
        self.status_bar.showMessage(
            "Exporting publication figures (300 DPI PDF & PNG)..."
        )
        QApplication.processEvents()

        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "output_figures"
        )
        export_all_publication_figures(output_dir=out_dir, dpi=300)

        self.status_bar.showMessage(
            f"All publication figures successfully exported to: {out_dir}"
        )
        QMessageBox.information(
            self,
            "Export Complete",
            f"Successfully generated all publication-ready figures in:\n{out_dir}",
        )


def main():
    app = QApplication(sys.argv)
    window = UAVTradeStudioMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
