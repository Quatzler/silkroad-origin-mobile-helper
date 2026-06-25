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

class AppConfig(BaseModel):
    states: Dict[str, StateConfig] = Field(default_factory=dict)

    # Allgemeine Einstellungen
    refresh_rate_ms: int = 1000
    debug_mode: bool = False
