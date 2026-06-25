import os
import tempfile
import yaml
from silkroad_companion.infrastructure.config_loader import ConfigLoader
from silkroad_companion.domain.config import AppConfig

def test_config_loader_default():
    # Testet das Laden ohne existierende Datei
    loader = ConfigLoader(config_path="/tmp/non_existent_config.yaml")
    config = loader.load()
    assert isinstance(config, AppConfig)
    assert config.refresh_rate_ms == 1000

def test_config_loader_with_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({
            "refresh_rate_ms": 500,
            "states": {
                "game": {
                    "keybinds": {
                        "1": {"action": "test_action"}
                    }
                }
            }
        }, f)
        temp_path = f.name

    try:
        loader = ConfigLoader(config_path=temp_path)
        config = loader.load()
        assert config.refresh_rate_ms == 500
        assert config.states["game"].keybinds["1"].action == "test_action"
    finally:
        os.unlink(temp_path)
