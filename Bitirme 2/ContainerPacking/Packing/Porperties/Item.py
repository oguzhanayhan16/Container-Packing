from dataclasses import dataclass, field

@dataclass
class Item:
    id: int  # <- BU ZORUNLU!
    dim1: float
    dim2: float
    dim3: float
    name: str  
    quantity: int
    is_packed: bool = False  # is_packed küçük harflerle yazılmış
    coord_x: float = 0.0
    coord_y: float = 0.0
    coord_z: float = 0.0
    pack_dim_x: float = 0.0
    pack_dim_y: float = 0.0
    pack_dim_z: float = 0.0
    total_quantity: int = 0  
    _volume: float = field(init=False)

    def __post_init__(self):
        """Volume hesaplamasını otomatik yapar."""
        self._volume = self.dim1 * self.dim2 * self.dim3

    @property
    def volume(self):
        """Volume değerini döndürür."""
        return self._volume
