from abc import ABC, abstractmethod
from typing import List
from ContainerPacking.Packing.Porperties.Item import Item

class PackingAlgorithm(ABC):
    @abstractmethod
    def run(self, container, items: List['Item']):
        pass  # Alt sınıf tarafından implement edilmesi beklenen metod

