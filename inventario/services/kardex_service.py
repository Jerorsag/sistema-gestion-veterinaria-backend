from inventario.models import Notificacion
from inventario.patrones import GestorInventario  # ✨ NUEVO IMPORT


class KardexService:

    def __init__(self):
        from inventario.services.stock_service import StockService
        from inventario.services.notificacion_service import NotificacionService

        self.stock_service = StockService()
        self.notificacion_service = NotificacionService()
        self.gestor = GestorInventario()  # ✨ Singleton

    def procesar_movimiento(self, kardex, usuario=None):  # ✨ usuario opcional

        producto = kardex.producto
        cantidad = int(kardex.cantidad)  # ✔ Conversión a entero

        # Actualizar stock según el tipo
        if kardex.tipo == 'entrada':
            self.stock_service.agregar_stock(producto, cantidad)
        elif kardex.tipo == 'salida':
            self.stock_service.restar_stock(producto, cantidad)

        # Verificar alertas
        self.notificacion_service.verificar_alertas_producto(producto)

        # Registrar en Singleton
        self.gestor.registrar_movimiento(
            producto=producto,
            cantidad=cantidad,
            tipo=f"KARDEX_{kardex.tipo.upper()}",
            usuario=usuario
        )


    def anular_movimiento(self, kardex, usuario=None):

        # Evitar anular dos veces
        if "ANULADO" in (kardex.detalle or ""):
            return

        producto = kardex.producto
        cantidad = int(kardex.cantidad)

        # Revertir efecto
        if kardex.tipo == 'entrada':
            self.stock_service.restar_stock(producto, cantidad)
        else:
            self.stock_service.agregar_stock(producto, cantidad)

        kardex.detalle = f"{kardex.detalle or ''} - ANULADO"
        kardex.save()

        self.notificacion_service.verificar_alertas_producto(producto)

        # Registrar en Singleton
        self.gestor.registrar_movimiento(
            producto=producto,
            cantidad=cantidad,
            tipo=f"ANULACIÓN_{kardex.tipo.upper()}",
            usuario=usuario
        )

    # dentro de NotificacionService
    def crear_info(self, titulo: str, mensaje: str):
        Notificacion.objects.create(
            titulo=titulo,
            mensaje=mensaje,
            modulo="inventario",
            nivel="info"
        )
