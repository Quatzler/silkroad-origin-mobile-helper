from abc import ABC, abstractmethod


class FocusService(ABC):
    @abstractmethod
    def is_waydroid_active(self) -> bool:
        """Prüft ob Waydroid überhaupt läuft."""
        pass

    @abstractmethod
    def is_waydroid_focused(self) -> bool:
        """Prüft ob das Waydroid Fenster gerade den Fokus hat."""
        pass

    @abstractmethod
    def get_active_window_title(self) -> str | None:
        """Gibt den Titel des aktuell fokussierten Fensters zurück."""
        pass
