from django.db import models
from common.models import BaseModel
from usuarios.models import Cliente

# Jeronimo Rodriguez - 11/03/2025
"""
Modelos del módulo `mascotas`.

Contienen las entidades principales del dominio de mascotas:
- Especie: tipos de animales (Perro, Gato, ...)
- Raza: razas asociadas a una especie
- Mascota: registro de una mascota perteneciente a un Cliente
- HistoriaClinica: historia clínica asociada (1:1) a una mascota

Todos los modelos heredan (directa o indirectamente) de `BaseModel`,
que aporta campos de auditoría (`id` UUID, `created_at`, `updated_at`, `deleted_at`).
"""

class Especie(BaseModel):
    """Representa una especie animal (Perro, Gato, etc.)."""
    nombre = models.CharField('Nombre', max_length=100, unique=True)

    class Meta:
        db_table = 'especies'
        verbose_name = 'Especie'
        verbose_name_plural = 'Especies'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Raza(BaseModel):
    """Representa una raza asociada a una especie."""
    nombre = models.CharField('Nombre', max_length=100)
    especie = models.ForeignKey(Especie, on_delete=models.CASCADE, related_name='razas')

    class Meta:
        db_table = 'razas'
        verbose_name = 'Raza'
        verbose_name_plural = 'Razas'
        unique_together = ['nombre', 'especie']
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.especie.nombre})"


class Mascota(BaseModel):
    """Modelo principal que representa una mascota registrada por un cliente."""
    SEXOS = [
        ('M', 'Macho'),
        ('H', 'Hembra'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='mascotas')
    especie = models.ForeignKey(Especie, on_delete=models.SET_NULL, null=True, related_name='mascotas')
    raza = models.ForeignKey(Raza, on_delete=models.SET_NULL, null=True, related_name='mascotas')
    nombre = models.CharField('Nombre', max_length=100)
    sexo = models.CharField('Sexo', max_length=1, choices=SEXOS)
    fecha_nacimiento = models.DateField('Fecha de nacimiento', null=True, blank=True)
    peso = models.DecimalField('Peso (kg)', max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'mascotas'
        verbose_name = 'Mascota'
        verbose_name_plural = 'Mascotas'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.cliente.usuario.get_full_name()}"


class HistoriaClinica(BaseModel):
    """Historial clínico básico asociado a una mascota."""
    mascota = models.OneToOneField(Mascota, on_delete=models.CASCADE, related_name='historia_clinica')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    observaciones_generales = models.TextField('Observaciones generales', blank=True)

    class Meta:
        db_table = 'historias_clinicas'
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'

    def __str__(self):
        return f"Historia clínica de {self.mascota.nombre}"