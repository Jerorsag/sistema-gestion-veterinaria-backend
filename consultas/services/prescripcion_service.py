"""
Servicios para la gestión de prescripciones y actualización de inventario
Sara Sanchez
03 Noviembre 2025
"""

def descontar_inventario(prescripcion):
    """
    Descuenta la cantidad prescrita del inventario y genera alerta si llega al stock mínimo.
    """
    medicamento = prescripcion.medicamento
    medicamento.cantidad_disponible -= prescripcion.cantidad
    medicamento.save(update_fields=['cantidad_disponible'])

    if medicamento.cantidad_disponible <= medicamento.stock_minimo:
        from apps.notificaciones.services import generar_alerta_stock_bajo
        generar_alerta_stock_bajo(medicamento)


def devolver_inventario(prescripcion):
    """
    Devuelve la cantidad al inventario si se elimina la prescripción.
    """
    medicamento = prescripcion.medicamento
    medicamento.cantidad_disponible += prescripcion.cantidad
    medicamento.save(update_fields=['cantidad_disponible'])