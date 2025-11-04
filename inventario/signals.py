from datetime import timedelta

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.template.defaultfilters import date

from .models import Kardex, Producto

#  ACTUALIZA STOCK DESPUÉS DE GUARDAR UN MOVIMIENTO
@receiver(post_save, sender=Kardex)
def actualizar_stock(sender, instance, created, **kwargs):
    if not created:
        return

    producto = instance.producto

    # Entradas aumentan el stock
    if instance.tipo.startswith('entrada'):
        producto.stock += instance.cantidad
        producto.save()

    # Salidas reducen el stock
    elif instance.tipo.startswith('salida'):
        if producto.stock >= instance.cantidad:
            producto.stock -= instance.cantidad
            producto.save()
        else:
            raise ValueError("Stock insuficiente para realizar la salida.")



@receiver(pre_delete, sender=Kardex)
def anular_kardex(sender, instance, **kwargs):
    if "anulado" not in instance.tipo:
        if instance.tipo == "entrada":
            instance.producto.stock -= instance.cantidad
        elif instance.tipo == "salida":
            instance.producto.stock += instance.cantidad
        instance.producto.save()

        instance.tipo = f"{instance.tipo}-anulado"
        instance.detalle = f"{instance.detalle} - ANULADO" if instance.detalle else "Registro ANULADO"
        instance.save()

    # Cancelamos la eliminación de forma silenciosa
    kwargs["signal"].disconnect(anular_kardex)


