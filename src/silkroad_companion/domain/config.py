from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class KeyBind(BaseModel):
    action: str
    description: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None

class JoystickConfig(BaseModel):
    center_x: float = 0.15
    center_y: float = 0.75
    radius: float = 0.05

class StateConfig(BaseModel):
    keybinds: Dict[str, KeyBind] = Field(default_factory=dict)
    joystick: Optional[JoystickConfig] = None

class TouchCalibration(BaseModel):
    """Kalibrierung für den virtuellen Touchscreen.
    
    scale_x/y: Skalierungsfaktor (1.0 = keine Skalierung)
    offset_x/y: Pixel-Offset (wird nach der Skalierung addiert)
    """
    scale_x: float = 1.0
    scale_y: float = 1.0
    offset_x: int = 0
    offset_y: int = 0

class AppConfig(BaseModel):
    states: Dict[str, StateConfig] = Field(default_factory=dict)
    touch_calibration: TouchCalibration = TouchCalibration()
    
    # Allgemeine Einstellungen
    refresh_rate_ms: int = 1000
    debug_mode: bool = False
