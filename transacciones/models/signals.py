from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from transacciones.models.detalle_factura import DetalleFactura
from transacciones.models.factura import Factura

@receiver(post_save, sender=DetalleFactura)
def detalle_guardado_recalcular(sender, instance, created, **kwargs):
    """
    Cuando un detalle se guarda, recalcular la factura asociada.
    """
    factura = instance.factura
    if factura:
        factura.recalcular_totales()

@receiver(post_delete, sender=DetalleFactura)
def detalle_eliminado_recalcular(sender, instance, **kwargs):
    factura = instance.factura
    if factura:
        factura.recalcular_totales()