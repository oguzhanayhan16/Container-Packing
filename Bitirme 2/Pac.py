from typing import List
from ContainerPacking.Packing.Porperties.Container import Container
from ContainerPacking.Packing.Porperties.Item import Item
from  ContainerPacking.Packing.Porperties.ContainerPackingResult import ContainerPackingResult
from  ContainerPacking.PackingService import PackingService


class ContainerPackingRequest:
    def __init__(self, containers, items_to_pack, algorithm_type_ids):
        self.containers = containers
        self.items_to_pack = items_to_pack
        self.algorithm_type_ids = algorithm_type_ids

def pack_containers(containers: List[Container], items_to_pack: List[Item], algorithm_type_ids: List[int]) -> List[ContainerPackingResult]:
    results = []
    for algorithm_id in algorithm_type_ids:
        result = PackingService.pack(containers, items_to_pack, algorithm_id)
        results.append(result)
    
    return results

