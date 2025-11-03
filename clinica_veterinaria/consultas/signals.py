"""
Señales automáticas del módulo de Consultas y Prescripciones
Sara Sanchez
03 Noviembre 2025
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Consulta, Prescripcion, HistoriaClinica
from .services.historia_service import gestionar_historia_clinica
from .services.prescripcion_service import descontar_inventario, devolver_inventario
from .patterns.memento import GestorMementos

gestor_mementos = GestorMementos()

@receiver(post_save, sender=Consulta)
def crear_o_actualizar_historia(sender, instance, created, **kwargs):
    """
    Al crear una consulta, crea o actualiza automáticamente
    la historia clínica y el estado de vacunación.
    """
    if created:
        gestionar_historia_clinica(instance)


@receiver(post_save, sender=Prescripcion)
def actualizar_inventario_post_save(sender, instance, created, **kwargs):
    """
    Al crear una prescripción, descuenta stock y genera alerta si es necesario.
    """
    if created:
        descontar_inventario(instance)


@receiver(post_delete, sender=Prescripcion)
def devolver_inventario_post_delete(sender, instance, **kwargs):
    """
    Al eliminar una prescripción, devuelve el stock al inventario.
    """
    devolver_inventario(instance)

@receiver(post_save, sender=HistoriaClinica)
def guardar_version_historia(sender, instance, **kwargs):
    gestor_mementos.guardar(instance)