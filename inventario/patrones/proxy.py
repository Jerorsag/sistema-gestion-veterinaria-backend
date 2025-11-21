class InventarioProxy:
    def __init__(self, usuario, gestor):
        self.usuario = usuario
        self.gestor = gestor

    def modificar_stock(self, producto, cantidad):
        if not self.usuario.is_staff:
            raise PermissionError("No tiene permisos para modificar el stock.")
        self.gestor.registrar_movimiento(producto, cantidad, "MODIFICACIÓN")
