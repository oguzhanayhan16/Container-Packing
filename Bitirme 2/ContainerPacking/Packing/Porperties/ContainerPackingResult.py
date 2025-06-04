from dataclasses import dataclass, field
from typing import List
from .Item import Item

@dataclass
class AlgorithmPackingResult:
    algorithm_id: int
    algorithm_name: str
    pack_time: float
    percent_container_volume_packed: float
    packed_items: List[Item]  # Packed items
    unpacked_items: List[Item]  # Unpacked items

@dataclass
class ContainerPackingResult:
    container_id: int
    algorithm_packing_results: List[AlgorithmPackingResult] = field(default_factory=list)
