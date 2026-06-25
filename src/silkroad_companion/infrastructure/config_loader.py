import yaml
import pathlib
from typing import Optional
from silkroad_companion.domain.config import AppConfig

class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = pathlib.Path(config_path)
        else:
            # Standardpfad: Projektroot / config / settings.yaml
            self.config_path = pathlib.Path(__file__).parent.parent.parent.parent / "config" / "settings.yaml"

    def load(self) -> AppConfig:
        if not self.config_path.exists():
            # Wenn keine Datei existiert, geben wir Default-Werte zurück
            return AppConfig()

        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f)
                if data is None:
                    return AppConfig()
                return AppConfig.model_validate(data)
        except Exception as e:
            print(f"Warnung: Konfiguration konnte nicht geladen werden ({e}). Nutze Defaults.")
            return AppConfig()
