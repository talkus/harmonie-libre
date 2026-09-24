from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Tuple

@dataclass
class HomologousPair:
    left: Any = None
    right: Any = None

@dataclass
class PairedMemoryBank:
    """Topologie expérimentale optionnelle. 24 n'est pas une constante de conscience."""
    pair_count: int = 24
    pairs: List[HomologousPair] = field(init=False)

    def __post_init__(self):
        if self.pair_count < 1:
            raise ValueError("pair_count must be positive")
        self.pairs = [HomologousPair() for _ in range(self.pair_count)]

    def write(self, index: int, left: Any, right: Any) -> None:
        self.pairs[index] = HomologousPair(left, right)

    def read(self, index: int) -> Tuple[Any, Any]:
        p = self.pairs[index]
        return p.left, p.right
