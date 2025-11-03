"""
Modelo temporal para pruebas del módulo de Consultas
(MascotaMock reemplazará a Mascota hasta implementar la app 'mascotas')

Sara Sánchez
03 Noviembre 2025
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class MascotaMock(models.Model):
    """
    Modelo temporal para simular la app 'mascotas' y permitir pruebas
    en el módulo de consultas, historias clínicas y prescripciones.
    """

    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre de la mascota")
    )

    especie = models.CharField(
        max_length=50,
        default='Perro',
        verbose_name=_("Especie")
    )

    raza = models.CharField(
        max_length=50,
        default='Criollo',
        verbose_name=_("Raza")
    )

    edad = models.PositiveIntegerField(
        default=2,
        verbose_name=_("Edad (años)")
    )

    propietario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mascotas_mock',
        verbose_name=_("Propietario")
    )

    estado_vacunacion = models.CharField(
        max_length=20,
        default='AL_DIA',
        verbose_name=_("Estado de vacunación")
    )

    class Meta:
        verbose_name = _("Mascota (Prueba)")
        verbose_name_plural = _("Mascotas (Pruebas)")
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.especie})"
