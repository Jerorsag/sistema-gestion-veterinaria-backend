class GestorInventario:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(GestorInventario, cls).__new__(cls)
        return cls._instancia

    def registrar_movimiento(self, producto, cantidad, tipo):
        print(f"{tipo}: {cantidad} unidades de {producto.descripcion}")
