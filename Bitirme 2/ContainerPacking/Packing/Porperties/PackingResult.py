from dataclasses import dataclass, field
from typing import List
from ContainerPacking.Packing.Porperties.Item import Item

@dataclass
class Item:
    name: str  # Örnek olarak basit bir Item sınıfı


@dataclass
class AlgorithmPackingResult:
    
    algorithm_id: int
    algorithm_name: str
    is_complete_pack: bool
    packed_items: List[Item] = field(default_factory=list)
    pack_time_in_milliseconds: int = 0
    percent_container_volume_packed: float = 0.0
    percent_item_volume_packed: float = 0.0
    unpacked_items: List[Item] = field(default_factory=list)