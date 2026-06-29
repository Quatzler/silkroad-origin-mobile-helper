#!/usr/bin/env python3
"""
Beispielskript für die Touch-Kalibrierung.

Dieses Skript zeigt, wie man die Touch-Kalibrierung manuell durchführt
und die optimalen Parameter findet.

Verwendung:
    uv run python examples/calibration_example.py
"""

import sys
import os
import time

# Add src directory to python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
from silkroad_companion.infrastructure.kwin_focus_service import KWinFocusService
from silkroad_companion.domain.models import WindowInfo
from silkroad_companion.domain.config import TouchCalibration


def print_header(text):
    print("\n" + "="*60)
    print(text)
    print("="*60)


def main():
    print_header("SILKROAD COMPANION - KALIBRIERUNGSBEISPIEL")
    
    # Services initialisieren
    touch_service = EvdevTouchService()
    focus_service = KWinFocusService()
    
    # Bildschirmgröße setzen (anpassen an deine Auflösung)
    # Für Dual-Monitor: 4054x1200 (wie in deinem Fall)
    touch_service.set_screen_size(4054, 1200, 0, 0)
    
    print("\n1. WARTEN AUF WAYDROID FOKUS...")
    print("   Bitte öffne Silkroad Origin Mobile in Waydroid und fokussiere es.")
    
    # Warten bis Waydroid fokussiert ist
    max_attempts = 30
    for i in range(max_attempts):
        if focus_service.is_waydroid_focused():
            print("   ✓ Waydroid fokussiert!")
            break
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Warten... ({i+1}/{max_attempts})")
    else:
        print("   ✗ Waydroid wurde nicht fokussiert. Abbruch.")
        return
    
    # Fenster-Info holen
    window_info = focus_service.get_window_info()
    print(f"\n2. FENSTER-INFORMATIONEN:")
    print(f"   Position: ({window_info.x}, {window_info.y})")
    print(f"   Größe: {window_info.width}x{window_info.height}")
    print(f"   Fokussiert: {window_info.focused}")
    
    print_header("KALIBRIERUNGSTEST")
    
    # Test 1: Mitte des Fensters
    print("\n3. TESTE MITTE DES FENSTERS (0.5, 0.5)")
    print("   Beobachte, wo der Touch im Spiel ankommt.")
    print("   Erwartet: Mitte des Spiel-Fensters")
    
    touch_service.click_relative(0.5, 0.5, window_info, slot=0)
    time.sleep(1)
    
    print("\n   Frage: Wo kam der Touch an?")
    print("   - Zu weit links? → scale_x erhöhen")
    print("   - Zu weit rechts? → scale_x verringern")
    print("   - Zu weit oben? → scale_y erhöhen")
    print("   - Zu weit unten? → scale_y verringern")
    
    # Test 2: Ecken
    print("\n4. TESTE ECKE (0.0, 0.0) - Oben links")
    touch_service.click_relative(0.0, 0.0, window_info, slot=0)
    time.sleep(1)
    
    print("\n5. TESTE ECKE (1.0, 1.0) - Unten rechts")
    touch_service.click_relative(1.0, 1.0, window_info, slot=0)
    time.sleep(1)
    
    print_header("KALIBRIERUNGSPARAMETER BERECHNEN")
    
    print("\n6. BEISPIEL-BERECHNUNG:")
    print("   Angenommen:")
    print("   - Erwartet: (0.5, 0.5) = Mitte")
    print("   - Tatsächlich: Touch kommt bei 45% von links und 55% von oben an")
    print()
    print("   Dann:")
    print("   - scale_x = 0.5 / 0.45 ≈ 1.11")
    print("   - scale_y = 0.5 / 0.55 ≈ 0.91")
    print()
    print("   Wenn der Touch um 10 Pixel nach rechts verschoben ist:")
    print("   - offset_x = -10")
    print("   Wenn der Touch um 5 Pixel nach oben verschoben ist:")
    print("   - offset_y = 5")
    
    print_header("KONFIGURATION GENERIEREN")
    
    # Beispiel-Konfiguration
    calibration = TouchCalibration(
        scale_x=1.0,
        scale_y=1.0,
        offset_x=0,
        offset_y=0
    )
    
    print("\n7. BEISPIEL-KONFIGURATION (anpassen!):")
    print("\n   Füge dies zu config/settings.yaml hinzu:")
    print()
    print("   touch_calibration:")
    print(f"     scale_x: {calibration.scale_x}")
    print(f"     scale_y: {calibration.scale_y}")
    print(f"     offset_x: {calibration.offset_x}")
    print(f"     offset_y: {calibration.offset_y}")
    
    print("\n8. TEST MIT KALIBRIERUNG:")
    print("   Passe die Werte in der Konfiguration an und starte die Anwendung neu.")
    print("   Oder teste direkt mit:")
    
    # Teste mit verschiedenen Kalibrierungen
    test_calibrations = [
        ("Standard", TouchCalibration(scale_x=1.0, scale_y=1.0, offset_x=0, offset_y=0)),
        ("Skalierung 0.95", TouchCalibration(scale_x=0.95, scale_y=0.95, offset_x=0, offset_y=0)),
        ("Skalierung 1.05", TouchCalibration(scale_x=1.05, scale_y=1.05, offset_x=0, offset_y=0)),
        ("Offset +10", TouchCalibration(scale_x=1.0, scale_y=1.0, offset_x=10, offset_y=10)),
        ("Offset -10", TouchCalibration(scale_x=1.0, scale_y=1.0, offset_x=-10, offset_y=-10)),
    ]
    
    for name, calib in test_calibrations:
        print(f"\n   Test: {name}")
        touch_service.set_calibration(calib)
        touch_service.click_relative(0.5, 0.5, window_info, slot=0)
        time.sleep(0.5)
    
    print_header("FERTIG")
    print("\n   Für eine interaktive Kalibrierung verwende:")
    print("   uv run python calibrate_touch.py")
    print()
    print("   Für detaillierte Fenster-Informationen verwende:")
    print("   uv run python debug_window.py")
    print()


if __name__ == "__main__":
    main()
