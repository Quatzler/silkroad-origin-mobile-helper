import logging
import threading
from typing import Callable
import evdev
from evdev import ecodes
import os

from silkroad_companion.domain.input_service import InputService

logger = logging.getLogger(__name__)

class KeyboardInputService(InputService):
    def __init__(self) -> None:
        self._callbacks: dict[int, Callable[[], None]] = {}
        self._devices: list[evdev.InputDevice] = []
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._key_names_to_codes = self._build_key_map()

    def _build_key_map(self) -> dict[str, int]:
        """Erstellt ein Mapping von gängigen Tastennamen auf evdev Keycodes."""
        mapping = {}
        # Wir mappen bekannte Tasten. evdev.ecodes.KEY_F8 etc.
        for name in dir(ecodes):
            if name.startswith("KEY_"):
                key_name = name[4:].lower()
                mapping[key_name] = getattr(ecodes, name)

        # Manuelle Korrekturen/Aliase falls nötig
        mapping["esc"] = ecodes.KEY_ESC
        return mapping

    def bind_key(self, key: str, callback: Callable[[], None]) -> None:
        normalized_key = key.lower()
        if normalized_key in self._key_names_to_codes:
            code = self._key_names_to_codes[normalized_key]
            self._callbacks[code] = callback
            print(f"Evdev: Hotkey registriert: {key} (Code: {code})", flush=True)
            logger.info(f"Hotkey registriert: {key} (Code: {code})")
        else:
            print(f"Evdev: Unbekannte Taste: {key}", flush=True)
            logger.warning(f"Unbekannte Taste: {key}")

    def start_listener(self) -> None:
        if self._threads:
            self.stop_listener()

        self._devices = self._find_keyboard_devices()
        if not self._devices:
            logger.error("Keine Tastatur-Geräte gefunden oder keine Berechtigungen für /dev/input/")
            print("Fehler: Keine Tastatur gefunden oder keine Berechtigungen für /dev/input/.", flush=True)
            print("Hast du die udev-Regeln erstellt und dich der Gruppe 'input' hinzugefügt?", flush=True)
            return

        print(f"Starte Listener für {len(self._devices)} Tastaturen...", flush=True)
        self._stop_event.clear()
        for device in self._devices:
            print(f"  - Überwache: {device.name} ({device.path})", flush=True)
            thread = threading.Thread(
                target=self._listen_to_device,
                args=(device,),
                daemon=True,
                name=f"EvdevListener-{device.name}"
            )
            thread.start()
            self._threads.append(thread)

        logger.info(f"Hintergrund-Listener für {len(self._devices)} Geräte gestartet.")

    def _find_keyboard_devices(self) -> list[evdev.InputDevice]:
        devices = []
        try:
            device_paths = evdev.list_devices()
            logger.info(f"Gefundene Input-Geräte unter /dev/input/: {device_paths}")
            for path in device_paths:
                try:
                    dev = evdev.InputDevice(path)
                    capabilities = dev.capabilities()
                    # Prüfen ob das Gerät Tasten hat (KEY_A ist ein guter Indikator für eine Tastatur)
                    if ecodes.EV_KEY in capabilities:
                        if ecodes.KEY_A in capabilities[ecodes.EV_KEY]:
                            logger.info(f"Tastatur erkannt: {dev.name} ({dev.path})")
                            devices.append(dev)
                except (PermissionError, OSError) as e:
                    logger.warning(f"Zugriff auf {path} verweigert: {e}")
        except Exception as e:
            logger.error(f"Fehler beim Scannen der Eingabegeräte: {e}")
        return devices

    def _listen_to_device(self, device: evdev.InputDevice) -> None:
        try:
            logger.debug(f"Höre auf {device.name}...")
            for event in device.read_loop():
                if self._stop_event.is_set():
                    break

                if event.type == ecodes.EV_KEY:
                    # value 1 = key down, 0 = key up, 2 = key hold
                    if event.value == 1:
                        if event.code in self._callbacks:
                            print(f"Evdev: Hotkey erkannt! Code={event.code} ({device.name})", flush=True)
                            self._callbacks[event.code]()
        except (OSError, Exception) as e:
            # Errno 9 (Bad file descriptor) tritt auf, wenn wir das Device schließen
            # während der read_loop noch blockiert. Das ist ein beabsichtigter Abbruch.
            if self._stop_event.is_set() or (isinstance(e, OSError) and e.errno == 9):
                logger.debug(f"Listener für {device.name} sauber beendet.")
            else:
                logger.warning(f"Listener für {device.name} unerwartet beendet: {e}")

    def stop_listener(self) -> None:
        self._stop_event.set()
        # Da read_loop blockiert, können wir die Threads nicht sofort beenden.
        # Aber durch das Schließen der Devices wird der Loop unterbrochen.
        for device in self._devices:
            try:
                device.close()
            except:
                pass

        self._threads.clear()
        self._devices.clear()
        logger.info("Evdev-Listener gestoppt.")

    def unbind_all(self) -> None:
        self.stop_listener()
        self._callbacks.clear()
        logger.info("Alle Hotkeys entfernt.")
