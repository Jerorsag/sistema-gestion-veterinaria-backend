from .estrategia_lotes import EstrategiaSeleccionLote, EstrategiaFIFO, EstrategiaFEFO, EstrategiaLIFO, \
    EstrategiaCostoPromedio, GestorLotes, Lote
from .gestor_inventario import GestorInventario
from .inventario_proxy import InventarioProxy

__all__ = [
    # Singleton
    'GestorInventario',

    # Proxy
    'InventarioProxy',

    # Strategy
    'EstrategiaSeleccionLote',
    'EstrategiaFIFO',
    'EstrategiaFEFO',
    'EstrategiaLIFO',
    'EstrategiaCostoPromedio',
    'GestorLotes',
    'Lote',
]