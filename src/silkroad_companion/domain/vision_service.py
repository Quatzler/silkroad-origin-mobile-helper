from abc import ABC, abstractmethod
from typing import Any
import numpy as np

class VisionService(ABC):
    @abstractmethod
    def capture_window(self, window_info: Any) -> np.ndarray:
        """Erfasst einen Screenshot des angegebenen Fensters."""
        pass

    @abstractmethod
    def find_template(self, image: np.ndarray, template: np.ndarray, threshold: float = 0.8) -> bool:
        """Sucht ein Template im Bild und gibt True zurück, wenn gefunden."""
        pass
