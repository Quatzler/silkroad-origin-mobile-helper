from enum import Enum, auto

from pydantic import BaseModel


class AppState(Enum):
    LOGIN = auto()
    GAME = auto()
    MENU = auto()
    CHAT = auto()
    MAP = auto()
    NPC_DIALOG = auto()
    SKILLS = auto()
    LOADING = auto()
    UNKNOWN = auto()

class WindowInfo(BaseModel):
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    dpi: float = 1.0
    focused: bool = False
