from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class KeyBind(BaseModel):
    action: str
    description: Optional[str] = None

class StateConfig(BaseModel):
    keybinds: Dict[str, KeyBind] = Field(default_factory=dict)

class AppConfig(BaseModel):
    states: Dict[str, StateConfig] = Field(default_factory=dict)

    # Allgemeine Einstellungen
    refresh_rate_ms: int = 1000
    debug_mode: bool = False
