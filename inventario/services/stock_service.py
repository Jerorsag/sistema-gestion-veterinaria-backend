from inventario.models import Producto
from inventario.services.notificacion_service import NotificacionService


class StockService:

    def __init__(self):
        self.notificaciones = NotificacionService()

    def agregar_stock(self, producto: Producto, cantidad: int) -> None:

        cantidad = int(cantidad)

        producto.stock += cantidad
        producto.save(update_fields=['stock'])

        self.notificaciones.crear_info(
            titulo=f"Entrada de stock: {producto.nombre}",
            mensaje=f"Se agregaron {cantidad} unidades al producto '{producto.nombre}'."
        )

    def restar_stock(self, producto: Producto, cantidad: int) -> None:

        cantidad = int(cantidad)

        if producto.stock < cantidad:
            raise ValueError(
                f"Stock insuficiente para el producto '{producto.nombre}'. "
                f"Stock actual: {producto.stock}, solicitado: {cantidad}"
            )

        producto.stock -= cantidad
        producto.save(update_fields=['stock'])

        # Notificación informativa
        self.notificaciones.crear_info(
            titulo=f"Salida de stock: {producto.nombre}",
            mensaje=f"Se descontaron {cantidad} unidades del producto '{producto.nombre}'."
        )

    @staticmethod
    def tiene_stock_suficiente(producto: Producto, cantidad: int) -> bool:
        cantidad = int(cantidad)
        return producto.stock >= cantidad

    @staticmethod
    def esta_en_stock_minimo(producto: Producto) -> bool:
        return producto.stock <= producto.stock_minimo
