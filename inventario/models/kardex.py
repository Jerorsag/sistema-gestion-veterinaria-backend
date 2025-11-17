from django.db import models

class Kardex(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.IntegerField()
    detalle = models.TextField(blank=True, null=True)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='movimientos')

    def __str__(self):
        return f"{self.tipo.capitalize()} - {self.producto.nombre}"

    def delete(self, using=None, keep_parents=False):
        # Si ya está anulado → error
        if self.detalle and "ANULADO" in self.detalle:
            raise ValueError("Este movimiento ya está anulado y no puede eliminarse su registro.")

        # Importar el servicio
        from inventario.services.kardex_service import KardexService

        servicio = KardexService()
        servicio.anular_movimiento(self)

        return

    class Meta:
        verbose_name = "Kardex"
        verbose_name_plural = "Kardex"
        ordering = ['-fecha']
