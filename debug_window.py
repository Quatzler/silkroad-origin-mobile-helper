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
import re
import numpy as np
from threading import Thread, Event
from typing import Optional, Tuple

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
    QLineEdit,
    QGroupBox,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QKeyEvent, QPixmap, QImage
from silkroad_companion.infrastructure.kwin_focus_service import KWinFocusService
from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
from silkroad_companion.infrastructure.adb_service import ADBService
from silkroad_companion.domain.models import WindowInfo


class GlobalHotkeyListener(QObject):
    """Listener für globale Hotkeys (F9) mit pynput"""
    f9_pressed = Signal()
    
    def __init__(self):
        super().__init__()
        self._stop_event = Event()
        self._listener = None
        self._start_listener()
    
    def _start_listener(self):
        """Startet den globalen Hotkey-Listener"""
        try:
            from pynput.keyboard import Listener, Key
            
            def on_press(key):
                if key == Key.f9:
                    self.f9_pressed.emit()
            
            self._listener = Listener(on_press=on_press, daemon=True)
            self._listener.start()
        except Exception as e:
            print(f"Warnung: Globaler Hotkey-Listener konnte nicht gestartet werden: {e}")
    
    def stop(self):
        """Stoppt den Listener"""
        if self._listener:
            self._listener.stop()


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
        self.adb_service = ADBService()
        
        # Picker-Modus Status
        self._picker_mode = False
        
        # Kalibrierungsdaten
        self._calibration_offset_x = 0
        self._calibration_offset_y = 0
        self._calibration_scale_x = 1.0
        self._calibration_scale_y = 1.0
        self._game_resolution = (0, 0)  # (Breite, Höhe) des Spiels
        self._waydroid_window_size = (0, 0)  # (Breite, Höhe) des Waydroid-Fensters
        
        # Letzte Cursor-Position für Anzeige
        self._last_cursor_pos = (0, 0)
        self._last_window_info = None
        
        # Setup UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header_label = QLabel("WINDOW DEBUGGER")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Kalibrierungs-Controls
        calib_layout = QHBoxLayout()
        self.calib_button = QPushButton("Automatische Kalibrierung (F7)")
        self.calib_button.clicked.connect(self.auto_calibrate)
        calib_layout.addWidget(self.calib_button)
        
        self.calib_info_label = QLabel("Kalibrierung: Nicht durchgeführt")
        self.calib_info_label.setStyleSheet("font-family: monospace;")
        calib_layout.addWidget(self.calib_info_label)
        layout.addLayout(calib_layout)
        
        # Picker Mode Control
        picker_layout = QHBoxLayout()
        self.picker_button = QPushButton("Picker Modus: INAKTIV (F8)")
        self.picker_button.clicked.connect(self.toggle_picker_mode)
        picker_layout.addWidget(self.picker_button)
        layout.addLayout(picker_layout)
        
        # Cursor Capture Display (dauerhaft sichtbar)
        self.cursor_group = QGroupBox("Cursor Position (Live)")
        self.cursor_layout = QVBoxLayout()
        self.cursor_info_label = QLabel("Picker Modus aktivieren, um Cursor-Position zu sehen")
        self.cursor_info_label.setStyleSheet("font-family: monospace;")
        self.cursor_layout.addWidget(self.cursor_info_label)
        self.cursor_group.setLayout(self.cursor_layout)
        layout.addWidget(self.cursor_group)
        
        # Info Display (für Fenster-Geometrie etc.)
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
        
        # Global Hotkey Listener für F9
        self.hotkey_listener = GlobalHotkeyListener()
        self.hotkey_listener.f9_pressed.connect(self.capture_cursor_position)
        
        # Timer für regelmäßige Updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)  # Standard: 1 Sekunde
        
        # Schnellere Updates im Picker-Modus
        self.picker_timer = QTimer(self)
        self.picker_timer.timeout.connect(self.update_cursor_info)
        
        # ADB Info Timer (alle 5 Sekunden)
        self.adb_timer = QTimer(self)
        self.adb_timer.timeout.connect(self.update_adb_info)
        self.adb_timer.start(5000)
        
        # Erstes Update
        self.update_info()
        self.update_adb_info()
        
        # Enable key press events für F8 und F7
        self.setFocusPolicy(Qt.StrongFocus)

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

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events für F8 und F7"""
        if event.key() == Qt.Key_F8:
            self.toggle_picker_mode()
        elif event.key() == Qt.Key_F7:
            self.auto_calibrate()
        else:
            super().keyPressEvent(event)

    def update_adb_info(self):
        """Aktualisiert die ADB-Informationen (Spiel-Auflösung, Aktivität)"""
        if not self.adb_service.is_waydroid_running():
            return
        
        # Aktuelle Aktivität abfragen
        activity = self.adb_service.get_current_activity()
        if activity:
            self._current_activity = activity
        
        # Display-Größe abfragen
        display_size = self.adb_service.get_display_size()
        if display_size:
            self._game_resolution = display_size
            self.touch_service.calibration_scale_x = 1.0
            self.touch_service.calibration_scale_y = 1.0
            
            # Prüfe, ob die Display-Größe von der Waydroid-Fenstergröße abweicht
            window_info = self.focus_service.get_window_info()
            if window_info.width > 0 and window_info.height > 0:
                self._waydroid_window_size = (window_info.width, window_info.height)
                
                # Skalierungsfaktor berechnen
                scale_x = window_info.width / display_size[0]
                scale_y = window_info.height / display_size[1]
                
                # Wenn die Skalierung nicht 1.0 ist, anpassen
                if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
                    self.touch_service.calibration_scale_x = scale_x
                    self.touch_service.calibration_scale_y = scale_y
                    self.calib_info_label.setText(
                        f"Kalibrierung: Auto (Scale: {scale_x:.2f}x{scale_y:.2f}, "
                        f"Spiel: {display_size[0]}x{display_size[1]}, "
                        f"Waydroid: {window_info.width}x{window_info.height})"
                    )

    def auto_calibrate(self):
        """
        Führt eine automatische Kalibrierung durch:
        1. ADB: Spiel-Auflösung abfragen
        2. OpenCV: Spiel-Fenster im Waydroid-Fenster erkennen
        3. Offset und Skalierung berechnen
        """
        self.info_display.append("\n" + "=" * 60)
        self.info_display.append("AUTOMATISCHE KALIBRIERUNG GESTARTET (F7)")
        self.info_display.append("=" * 60)
        
        # 1. ADB: Spiel-Auflösung abfragen
        if not self.adb_service.is_waydroid_running():
            self.info_display.append("Fehler: Waydroid läuft nicht oder ADB ist nicht verfügbar.")
            self.info_display.append("=" * 60)
            return
        
        display_size = self.adb_service.get_display_size()
        if not display_size:
            self.info_display.append("Fehler: Konnte Spiel-Auflösung nicht abfragen.")
            self.info_display.append("=" * 60)
            return
        
        self._game_resolution = display_size
        self.info_display.append(f"Spiel-Auflösung (ADB): {display_size[0]}x{display_size[1]}")
        
        # 2. Waydroid-Fenstergröße abfragen
        window_info = self.focus_service.get_window_info()
        if not window_info or window_info.width <= 0:
            self.info_display.append("Fehler: Kein Waydroid-Fenster gefunden.")
            self.info_display.append("=" * 60)
            return
        
        self._waydroid_window_size = (window_info.width, window_info.height)
        self.info_display.append(f"Waydroid-Fenstergröße: {window_info.width}x{window_info.height}")
        
        # 3. Skalierungsfaktor berechnen
        scale_x = window_info.width / display_size[0]
        scale_y = window_info.height / display_size[1]
        self.info_display.append(f"Skalierungsfaktor: {scale_x:.2f}x{scale_y:.2f}")
        
        # 4. OpenCV: Spiel-Fenster-Rahmen erkennen (falls Skalierung != 1.0)
        if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
            self.info_display.append("Skalierung != 1.0 → Suche nach Spiel-Fenster-Rahmen...")
            game_window_offset = self._find_game_window_with_opencv(window_info)
            if game_window_offset:
                offset_x, offset_y, game_w, game_h = game_window_offset
                self.info_display.append(
                    f"Spiel-Fenster im Waydroid-Fenster: Offset=({offset_x}, {offset_y}), "
                    f"Größe={game_w}x{game_h}"
                )
                # Kalibrierung anpassen
                self._calibration_offset_x = offset_x / window_info.width
                self._calibration_offset_y = offset_y / window_info.height
                self.touch_service.calibration_offset_x = offset_x
                self.touch_service.calibration_offset_y = offset_y
            else:
                self.info_display.append("Warnung: Konnte Spiel-Fenster-Rahmen nicht erkennen.")
        else:
            self.info_display.append("Skalierung = 1.0 → Keine Rahmen-Erkennung nötig.")
        
        # 5. Kalibrierung anwenden
        self.touch_service.calibration_scale_x = scale_x
        self.touch_service.calibration_scale_y = scale_y
        
        self.calib_info_label.setText(
            f"Kalibrierung: Auto (Scale: {scale_x:.2f}x{scale_y:.2f}, "
            f"Offset: {self._calibration_offset_x:.3f}, {self._calibration_offset_y:.3f})"
        )
        
        self.info_display.append("Kalibrierung abgeschlossen!")
        self.info_display.append("=" * 60)

    def _find_game_window_with_opencv(self, window_info: WindowInfo) -> Optional[Tuple[int, int, int, int]]:
        """
        Versucht, das Spiel-Fenster innerhalb des Waydroid-Fensters mit OpenCV zu erkennen.
        
        Returns:
            (offset_x, offset_y, width, height) oder None, falls nicht gefunden.
        """
        try:
            import cv2
            from PySide6.QtGui import QScreen, QPixmap
            
            # Screenshot des Waydroid-Fensters machen
            screen = QApplication.primaryScreen()
            if not screen:
                return None
            
            # Fenster-Bereich als Screenshot
            screenshot = screen.grabWindow(
                0,  # 0 = gesamten Bildschirm (wir schneiden später zu)
                window_info.x,
                window_info.y,
                window_info.width,
                window_info.height
            )
            
            if not screenshot.isNull():
                # In OpenCV-Format konvertieren
                img = screenshot.toImage()
                img = img.convertToFormat(QImage.Format.Format_RGB888)
                width, height = img.width(), img.height()
                ptr = img.bits()
                ptr.setsize(img.byteCount())
                arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 3))
                frame = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                
                # Bildverarbeitung: Suche nach schwarzen Rändern (typisch für Waydroid)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
                
                # Konturen finden
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Größtes Rechteck suchen (wahrscheinlich das Spiel-Fenster)
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    # Filtere zu kleine Konturen raus
                    if w > 100 and h > 100:
                        # Prüfe, ob es sich um einen Rahmen handelt (dünnes Rechteck)
                        aspect_ratio = w / h
                        if 0.8 < aspect_ratio < 1.2:  # Quadratisch/Rechteckig
                            # Prüfe, ob der Rahmen am Rand des Bildes ist
                            if (x < 10 or y < 10 or 
                                (x + w) > width - 10 or 
                                (y + h) > height - 10):
                                # Das ist wahrscheinlich der äußere Rahmen → überspringen
                                continue
                            # Das ist wahrscheinlich das Spiel-Fenster
                            return (x, y, w, h)
                
                # Falls kein Rahmen gefunden wurde: Nimm das gesamte Fenster
                return (0, 0, window_info.width, window_info.height)
        except Exception as e:
            self.info_display.append(f"Fehler bei OpenCV-Erkennung: {e}")
        
        return None

    def toggle_picker_mode(self) -> None:
        """Aktiviert/Deaktiviert den Picker-Modus"""
        self._picker_mode = not self._picker_mode
        if self._picker_mode:
            self.picker_button.setText("Picker Modus: AKTIV (F8 zum Deaktivieren)")
            self.cursor_group.setTitle("Cursor Position (Live - F9 zum Capturen)")
            # Schnellere Updates starten (100ms)
            self.picker_timer.start(100)
        else:
            self.picker_button.setText("Picker Modus: INAKTIV (F8)")
            self.cursor_group.setTitle("Cursor Position (Live)")
            self.picker_timer.stop()
            self.cursor_info_label.setText("Picker Modus aktivieren, um Cursor-Position zu sehen")

    def update_cursor_info(self) -> None:
        """Aktualisiert die Cursor-Positions-Info in Echtzeit"""
        if not self._picker_mode:
            return
        
        cursor_pos = self.focus_service.get_cursor_pos()
        window_info = self.focus_service.get_window_info()
        
        if not window_info or window_info.width <= 0:
            self.cursor_info_label.setText("Kein Fenster gefunden")
            return
        
        abs_x, abs_y = cursor_pos
        
        # Relative Koordinaten berechnen (relativ zum Waydroid-Fenster)
        rel_x = (abs_x - window_info.x) / window_info.width
        rel_y = (abs_y - window_info.y) / window_info.height
        
        # Kalibrierung anwenden (Offset und Skalierung)
        calibrated_rel_x = (rel_x - self._calibration_offset_x) / self._calibration_scale_x
        calibrated_rel_y = (rel_y - self._calibration_offset_y) / self._calibration_scale_y
        
        # Prüfung ob Cursor im Fenster liegt
        in_window = 0 <= rel_x <= 1 and 0 <= rel_y <= 1
        status = "IM FENSTER" if in_window else "AUSSERHALB"
        
        # uinput-Koordinaten berechnen (absolut auf dem Bildschirm)
        calibrated_x = (abs_x * self.touch_service.calibration_scale_x) + self.touch_service.calibration_offset_x
        calibrated_y = (abs_y * self.touch_service.calibration_scale_y) + self.touch_service.calibration_offset_y
        
        tx = int(((calibrated_x - self.touch_service.offset_x) / self.touch_service.screen_width) * self.touch_service.max_x)
        ty = int(((calibrated_y - self.touch_service.offset_y) / self.touch_service.screen_height) * self.touch_service.max_y)
        
        # Ausgabe aktualisieren
        info_text = (
            f"Absolut: ({abs_x}, {abs_y}) | "
            f"Relativ (Waydroid): ({rel_x:.4f}, {rel_y:.4f}) | "
            f"Relativ (Spiel): ({calibrated_rel_x:.4f}, {calibrated_rel_y:.4f}) | "
            f"uinput: ({tx}, {ty}) | "
            f"Status: {status}"
        )
        self.cursor_info_label.setText(info_text)
        
        # Für die Capture-Funktion speichern
        self._last_cursor_pos = cursor_pos
        self._last_window_info = window_info

    def capture_cursor_position(self) -> None:
        """Captures the current cursor position and displays coordinates"""
        cursor_pos = self.focus_service.get_cursor_pos()
        window_info = self.focus_service.get_window_info()
        
        if not window_info or window_info.width <= 0:
            self.info_display.append("\nFehler: Kein Fenster gefunden zum Berechnen der Koordinaten.")
            return
        
        abs_x, abs_y = cursor_pos
        
        # Relative Koordinaten berechnen (relativ zum Waydroid-Fenster)
        rel_x = (abs_x - window_info.x) / window_info.width
        rel_y = (abs_y - window_info.y) / window_info.height
        
        # Kalibrierung anwenden
        calibrated_rel_x = (rel_x - self._calibration_offset_x) / self._calibration_scale_x
        calibrated_rel_y = (rel_y - self._calibration_offset_y) / self._calibration_scale_y
        
        # Prüfung ob Cursor im Fenster liegt
        in_window = 0 <= rel_x <= 1 and 0 <= rel_y <= 1
        status = "IM FENSTER" if in_window else "AUSSERHALB"
        
        # uinput-Koordinaten berechnen (absolut auf dem Bildschirm)
        calibrated_x = (abs_x * self.touch_service.calibration_scale_x) + self.touch_service.calibration_offset_x
        calibrated_y = (abs_y * self.touch_service.calibration_scale_y) + self.touch_service.calibration_offset_y
        
        tx = int(((calibrated_x - self.touch_service.offset_x) / self.touch_service.screen_width) * self.touch_service.max_x)
        ty = int(((calibrated_y - self.touch_service.offset_y) / self.touch_service.screen_height) * self.touch_service.max_y)
        
        # Ausgabe
        self.info_display.append("\n" + "=" * 60)
        self.info_display.append("CAPTURED CURSOR POSITION (F9)")
        self.info_display.append("=" * 60)
        self.info_display.append(f"Absolute Position (Bildschirm): ({abs_x}, {abs_y})")
        self.info_display.append(f"Fenster-Position: ({window_info.x}, {window_info.y}), Größe: {window_info.width}x{window_info.height}")
        self.info_display.append(f"Relative Koordinaten (Waydroid): x: {rel_x:.4f}, y: {rel_y:.4f} ({status})")
        self.info_display.append(f"Relative Koordinaten (Spiel): x: {calibrated_rel_x:.4f}, y: {calibrated_rel_y:.4f}")
        self.info_display.append(f"uinput Koordinaten: ({tx}, {ty})")
        
        # WICHTIG: Für Touch-Klicks müssen wir die kalibrierten relativen Koordinaten verwenden!
        self.info_display.append(f"\n-> Für Touch-Klicks diese relativen Koordinaten verwenden: ({calibrated_rel_x:.4f}, {calibrated_rel_y:.4f})")
        self.info_display.append("=" * 60)
        
        if not in_window:
            self.info_display.append(f"Hinweis: Cursor liegt außerhalb des Fensters!")

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
        info_text += f"Cursor Position: {cursor_pos}\n"
        info_text += f"Picker Modus: {'AKTIV' if self._picker_mode else 'INAKTIV'} (F8 zum Umschalten)\n"
        info_text += f"Letzte Capture: {self._last_cursor_pos} (F9)\n"
        
        # ADB-Info
        if self.adb_service.is_waydroid_running():
            activity = getattr(self, '_current_activity', None)
            if activity:
                info_text += f"Aktuelle Aktivität (ADB): {activity}\n"
            if self._game_resolution != (0, 0):
                info_text += f"Spiel-Auflösung (ADB): {self._game_resolution[0]}x{self._game_resolution[1]}\n"
        else:
            info_text += "ADB: Nicht verfügbar (Waydroid läuft nicht oder ADB nicht verbunden)\n"
        
        info_text += "\n"
        
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
        
        # Kalibrierung anwenden
        calibrated_x = (x * self._calibration_scale_x) + self._calibration_offset_x
        calibrated_y = (y * self._calibration_scale_y) + self._calibration_offset_y
        
        self.info_display.append(f"\nTeste Touch bei ({x}, {y}) mit Kalibrierung ({calibrated_x:.4f}, {calibrated_y:.4f})...")
        QApplication.processEvents()
        
        # Touch ausführen
        self.touch_service.click_relative(calibrated_x, calibrated_y, window_info, slot=0)
        
        self.info_display.append(f"Touch bei ({calibrated_x:.4f}, {calibrated_y:.4f}) ausgeführt - beobachte Position im Spiel")

    def get_window_info(self) -> WindowInfo:
        """Gibt die aktuelle Fenster-Info zurück"""
        return self.focus_service.get_window_info()

    def get_touch_service(self):
        """Gibt den Touch-Service zurück für direkte Nutzung"""
        return self.touch_service

    def get_focus_service(self):
        """Gibt den Focus-Service zurück für direkte Nutzung"""
        return self.focus_service

    def closeEvent(self, event):
        """Cleanup beim Schließen"""
        self.hotkey_listener.stop()
        super().closeEvent(event)


def main():
    """Standalone-Einstiegspunkt"""
    app = QApplication(sys.argv)
    app.setApplicationName("Silkroad Companion - Window Debugger")
    
    debugger = WindowDebugger()
    debugger.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
