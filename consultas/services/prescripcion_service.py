from decimal import Decimal
from django.db.models.signals import post_save
from inventario.models import Kardex

"""
Servicios para la gestión de prescripciones y actualización de inventario
Sara Sanchez
03 Noviembre 2025
"""


def descontar_inventario(producto, cantidad, detalle="Salida por prescripción"):
    """
    Descuenta la cantidad del stock del producto y registra el movimiento en el Kardex.
    IMPORTANTE: Desactiva temporalmente la señal de inventario para evitar doble descuento.
    """
    cantidad = Decimal(cantidad)

    if producto.stock < cantidad:
        raise ValueError(
            f"Stock insuficiente para {producto.descripcion}. "
            f"Disponible: {producto.stock}, solicitado: {cantidad}"
        )

    # Descontar del stock
    producto.stock -= cantidad
    producto.save(update_fields=['stock'])

    # Desconectar la señal de inventario temporalmente
    from inventario.signals import actualizar_stock
    post_save.disconnect(actualizar_stock, sender=Kardex)

    try:
        # Registrar el movimiento en el Kardex (sin activar la señal)
        Kardex.objects.create(
            tipo='salida',
            cantidad=cantidad,
            detalle=detalle,
            producto=producto
        )
    finally:
        # Reconectar la señal
        post_save.connect(actualizar_stock, sender=Kardex)

    return producto


def devolver_inventario(prescripcion, detalle="Devolución por eliminación de prescripción"):
    """
    Devuelve la cantidad al inventario si se elimina o anula la prescripción.
    También registra el movimiento en el Kardex.
    """
    producto = prescripcion.medicamento
    cantidad = Decimal(prescripcion.cantidad)

    # Sumar nuevamente al stock
    producto.stock += cantidad
    producto.save(update_fields=['stock'])

    # Desconectar la señal de inventario temporalmente
    from inventario.signals import actualizar_stock
    post_save.disconnect(actualizar_stock, sender=Kardex)

    try:
        # Registrar el movimiento en el Kardex
        Kardex.objects.create(
            tipo='entrada',
            cantidad=cantidad,
            detalle=detalle,
            producto=producto
        )
    finally:
        # Reconectar la señal
        post_save.connect(actualizar_stock, sender=Kardex)

    return producto