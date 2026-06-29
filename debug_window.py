#!/usr/bin/env python3
"""
Debug-Tool für Fenstergeometrie und Touch-Koordinaten.

Zeigt Echtzeit-Informationen über das Waydroid-Fenster an und hilft
bei der Kalibrierung der Touch-Positionen.

Verwendung als Standalone:
    uv run python debug_window.py

Verwendung als Klasse:
    from debug_window import WindowDebugger
    debugger = WindowDebugger()
    debugger.show()
"""

import sys
import os
import time

# Add src directory to python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout, 
    QWidget, 
    QLabel, 
    QPushButton, 
    QTextEdit, 
    QHBoxLayout,
    QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from silkroad_companion.infrastructure.kwin_focus_service import KWinFocusService
from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
from silkroad_companion.domain.models import WindowInfo


class WindowDebugger(QMainWindow):
    """
    GUI-Klasse für Debug-Informationen über Fenstergeometrie und Touch-Koordinaten.
    
    Kann als Standalone-Tool oder als eingebettete Komponente verwendet werden.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Silkroad Companion - Window Debugger")
        self.resize(800, 600)
        
        self.focus_service = KWinFocusService()
        self.touch_service = EvdevTouchService()
        
        # Setup UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header_label = QLabel("WINDOW DEBUGGER")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Info Display
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.info_display)
        
        # Test Controls
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Test X:"))
        self.test_x_input = QLineEdit("0.5")
        test_layout.addWidget(self.test_x_input)
        test_layout.addWidget(QLabel("Test Y:"))
        self.test_y_input = QLineEdit("0.5")
        test_layout.addWidget(self.test_y_input)
        self.test_button = QPushButton("Test Touch Position")
        self.test_button.clicked.connect(self.test_touch_position)
        test_layout.addWidget(self.test_button)
        layout.addLayout(test_layout)
        
        # Setup screen size
        self.setup_screen_size()
        
        # Timer für regelmäßige Updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)  # 1 Sekunde
        
        # Erstes Update
        self.update_info()

    def setup_screen_size(self):
        """Setup der Bildschirmgröße für den Touch-Service"""
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

    def update_info(self):
        """Aktualisiert die Debug-Informationen"""
        window_info = self.focus_service.get_window_info()
        is_focused = self.focus_service.is_waydroid_focused()
        cursor_pos = self.focus_service.get_cursor_pos()
        
        info_text = "=" * 60 + "\n"
        info_text += "WINDOW DEBUG INFO\n"
        info_text += "=" * 60 + "\n\n"
        
        info_text += f"Waydroid fokussiert: {is_focused}\n"
        info_text += f"Fenster-Titel: {self.focus_service.get_active_window_title() or 'Unbekannt'}\n"
        info_text += f"Cursor Position: {cursor_pos}\n\n"
        
        if window_info.width > 0:
            info_text += "Fenster-Geometrie:\n"
            info_text += f"  Position: ({window_info.x}, {window_info.y})\n"
            info_text += f"  Größe: {window_info.width}x{window_info.height}\n"
            info_text += f"  Fokussiert: {window_info.focused}\n\n"
            
            # Testpositionen berechnen
            info_text += "Testpositionen (relativ -> absolut):\n"
            test_positions = [
                (0.0, 0.0, "Oben links"),
                (1.0, 1.0, "Unten rechts"),
                (0.5, 0.5, "Mitte"),
                (0.5, 0.0, "Oben Mitte"),
                (0.5, 1.0, "Unten Mitte"),
                (0.0, 0.5, "Links Mitte"),
                (1.0, 0.5, "Rechts Mitte"),
                (0.25, 0.25, "Oben links Viertel"),
                (0.75, 0.75, "Unten rechts Viertel"),
            ]
            
            for rel_x, rel_y, desc in test_positions:
                abs_x = window_info.x + (window_info.width * rel_x)
                abs_y = window_info.y + (window_info.height * rel_y)
                info_text += f"  {desc:18} ({rel_x:.2f}, {rel_y:.2f}) -> ({int(abs_x):6d}, {int(abs_y):6d})\n"
            
            # Touch-Koordinaten berechnen
            info_text += "\nTouch-Koordinaten (uinput 0-32767):\n"
            for rel_x, rel_y, desc in test_positions:
                abs_x = window_info.x + (window_info.width * rel_x)
                abs_y = window_info.y + (window_info.height * rel_y)
                
                # Mit Kalibrierung
                calibrated_x = (abs_x * self.touch_service.calibration_scale_x) + self.touch_service.calibration_offset_x
                calibrated_y = (abs_y * self.touch_service.calibration_scale_y) + self.touch_service.calibration_offset_y
                
                tx = int(((calibrated_x - self.touch_service.offset_x) / self.touch_service.screen_width) * self.touch_service.max_x)
                ty = int(((calibrated_y - self.touch_service.offset_y) / self.touch_service.screen_height) * self.touch_service.max_y)
                info_text += f"  {desc:18} ({rel_x:.2f}, {rel_y:.2f}) -> uinput ({tx:6d}, {ty:6d})\n"
            
            # Kalibrierungsinfo
            info_text += "\nTouch-Service Konfiguration:\n"
            info_text += f"  Screen Size: {self.touch_service.screen_width}x{self.touch_service.screen_height}\n"
            info_text += f"  Offset: ({self.touch_service.offset_x}, {self.touch_service.offset_y})\n"
            info_text += f"  Kalibrierung: scale=({self.touch_service.calibration_scale_x}, {self.touch_service.calibration_scale_y}), "
            info_text += f"offset=({self.touch_service.calibration_offset_x}, {self.touch_service.calibration_offset_y})\n"
        else:
            info_text += "Kein Fenster gefunden oder Fenster hat keine Größe\n"
        
        info_text += "\n" + "=" * 60
        
        self.info_display.setPlainText(info_text)

    def test_touch_position(self):
        """Testet eine Touch-Position"""
        try:
            x = float(self.test_x_input.text())
            y = float(self.test_y_input.text())
        except ValueError:
            self.info_display.append("\nUngültige Koordinaten - bitte Zahlen eingeben (0.0 - 1.0)")
            return
        
        window_info = self.focus_service.get_window_info()
        if not window_info or window_info.width <= 0:
            self.info_display.append("\nKein Fenster gefunden - ist Waydroid fokussiert?")
            return
        
        self.info_display.append(f"\nTeste Touch bei ({x}, {y})...")
        QApplication.processEvents()
        
        # Touch ausführen
        self.touch_service.click_relative(x, y, window_info, slot=0)
        
        self.info_display.append(f"Touch bei ({x}, {y}) ausgeführt - beobachte Position im Spiel")

    def get_window_info(self) -> WindowInfo:
        """Gibt die aktuelle Fenster-Info zurück"""
        return self.focus_service.get_window_info()

    def get_touch_service(self):
        """Gibt den Touch-Service zurück für direkte Nutzung"""
        return self.touch_service

    def get_focus_service(self):
        """Gibt den Focus-Service zurück für direkte Nutzung"""
        return self.focus_service


def main():
    """Standalone-Einstiegspunkt"""
    app = QApplication(sys.argv)
    app.setApplicationName("Silkroad Companion - Window Debugger")
    
    debugger = WindowDebugger()
    debugger.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
