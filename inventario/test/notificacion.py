from time import timezone

from inventario import models


class Notificacion(models.Model):
    MODULOS = [
        ("inventario", "Inventario"),
        #("otros", "Otros") aquí luego agregamos el módulo al que le vamos a implementar las notificaciones
    ]

    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    modulo = models.CharField(max_length=50, choices=MODULOS, default="otros")
    nivel = models.CharField(
        max_length=20,
        choices=[("info", "Info"), ("warning", "Advertencia"), ("error", "Error")],
        default="info"
    )
    fecha = models.DateTimeField(default=timezone.now)
    leida = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.modulo.upper()}] {self.titulo}"

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha']