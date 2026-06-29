#!/usr/bin/env python3
"""
Touchscreen Kalibrierungs-Tool für Silkroad Companion.

Dieses Tool hilft dabei, die richtigen Kalibrierungsparameter zu finden,
damit Touch-Events an der richtigen Position ankommen.

Verwendung:
    uv run python calibrate_touch.py

Das Tool zeigt Anweisungen an und testet verschiedene Touch-Positionen.
"""

import sys
import os
import time

# Add src directory to python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QLineEdit, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
from silkroad_companion.infrastructure.kwin_focus_service import KWinFocusService
from silkroad_companion.domain.models import WindowInfo
from silkroad_companion.domain.config import TouchCalibration


class CalibrationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Silkroad Companion - Touch Kalibrierung")
        self.resize(600, 400)
        
        self.touch_service = EvdevTouchService()
        self.focus_service = KWinFocusService()
        
        # Setup UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Info Label
        self.info_label = QLabel(
            "Touch Kalibrierungs-Tool\n\n"
            "1. Stelle sicher, dass Silkroad Origin Mobile in Waydroid läuft und fokussiert ist.\n"
            "2. Klicke auf 'Test Position' um einen Touch an einer bestimmten Position zu testen.\n"
            "3. Beobachte, wo der Touch im Spiel ankommt.\n"
            "4. Passe die Kalibrierungsparameter an, bis die Position stimmt.\n"
        )
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Test Position Controls
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Test X:"))
        self.test_x_input = QLineEdit("0.5")
        test_layout.addWidget(self.test_x_input)
        test_layout.addWidget(QLabel("Test Y:"))
        self.test_y_input = QLineEdit("0.5")
        test_layout.addWidget(self.test_y_input)
        self.test_button = QPushButton("Test Position")
        self.test_button.clicked.connect(self.test_position)
        test_layout.addWidget(self.test_button)
        layout.addLayout(test_layout)
        
        # Calibration Controls
        calib_layout = QVBoxLayout()
        calib_layout.addWidget(QLabel("Kalibrierungsparameter:"))
        
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale X:"))
        self.scale_x_input = QLineEdit("1.0")
        scale_layout.addWidget(self.scale_x_input)
        scale_layout.addWidget(QLabel("Scale Y:"))
        self.scale_y_input = QLineEdit("1.0")
        scale_layout.addWidget(self.scale_y_input)
        calib_layout.addLayout(scale_layout)
        
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("Offset X:"))
        self.offset_x_input = QLineEdit("0")
        offset_layout.addWidget(self.offset_x_input)
        offset_layout.addWidget(QLabel("Offset Y:"))
        self.offset_y_input = QLineEdit("0")
        offset_layout.addWidget(self.offset_y_input)
        calib_layout.addLayout(offset_layout)
        
        self.apply_calib_button = QPushButton("Kalibrierung anwenden")
        self.apply_calib_button.clicked.connect(self.apply_calibration)
        calib_layout.addWidget(self.apply_calib_button)
        
        layout.addLayout(calib_layout)
        
        # Result Label
        self.result_label = QLabel("Bereit für Kalibrierung")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)
        
        # Setup screen size
        self.setup_screen_size()
        
        # Timer für regelmäßige Updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_window_info)
        self.timer.start(500)
        
        self.update_window_info()

    def setup_screen_size(self):
        app = QApplication.instance()
        if app:
            total_rect = None
            for screen in app.screens():
                if total_rect is None:
                    total_rect = screen.geometry()
                else:
                    total_rect = total_rect.united(screen.geometry())
            
            if total_rect:
                self.touch_service.set_screen_size(
                    total_rect.width(),
                    total_rect.height(),
                    total_rect.x(),
                    total_rect.y()
                )

    def update_window_info(self):
        window_info = self.focus_service.get_window_info()
        is_focused = self.focus_service.is_waydroid_focused()
        
        if is_focused and window_info.width > 0:
            self.result_label.setText(
                f"Waydroid fokussiert: {window_info.width}x{window_info.height} @ ({window_info.x}, {window_info.y})"
            )
        else:
            self.result_label.setText("Waydroid nicht fokussiert - bitte Silkroad fokussieren")

    def test_position(self):
        try:
            x = float(self.test_x_input.text())
            y = float(self.test_y_input.text())
        except ValueError:
            self.result_label.setText("Ungültige Koordinaten - bitte Zahlen eingeben (0.0 - 1.0)")
            return
        
        window_info = self.focus_service.get_window_info()
        if not window_info or window_info.width <= 0:
            self.result_label.setText("Kein Fenster gefunden - ist Waydroid fokussiert?")
            return
        
        self.result_label.setText(f"Teste Position: ({x}, {y})")
        QApplication.processEvents()  # UI aktualisieren
        
        # Touch ausführen
        self.touch_service.click_relative(x, y, window_info, slot=0)
        
        self.result_label.setText(f"Touch bei ({x}, {y}) ausgeführt - beobachte Position im Spiel")

    def apply_calibration(self):
        try:
            scale_x = float(self.scale_x_input.text())
            scale_y = float(self.scale_y_input.text())
            offset_x = int(self.offset_x_input.text())
            offset_y = int(self.offset_y_input.text())
        except ValueError:
            self.result_label.setText("Ungültige Parameter - bitte gültige Zahlen eingeben")
            return
        
        # Erstelle TouchCalibration-Objekt
        calibration = TouchCalibration(
            scale_x=scale_x,
            scale_y=scale_y,
            offset_x=offset_x,
            offset_y=offset_y
        )
        
        self.touch_service.set_calibration(calibration)
        
        self.result_label.setText(
            f"Kalibrierung angewendet: scale=({scale_x}, {scale_y}), offset=({offset_x}, {offset_y})"
        )
        
        # YAML-Konfiguration generieren
        yaml_config = f"""touch_calibration:
  scale_x: {scale_x}
  scale_y: {scale_y}
  offset_x: {offset_x}
  offset_y: {offset_y}
"""
        print("\n" + "="*50)
        print("Füge diese Konfiguration zu deiner settings.yaml hinzu:")
        print("="*50)
        print(yaml_config)
        print("="*50)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Silkroad Companion - Touch Kalibrierung")
    
    window = CalibrationWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
