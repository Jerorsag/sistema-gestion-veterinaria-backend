from django.db import models
from django.utils import timezone

#modelo marca
class Marca(models.Model):
    descripcion = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.descripcion

#modelo categoria
class Categoria(models.Model):
    descripcion = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.descripcion

#modelo producto
class Producto(models.Model):
    nombre = models.CharField(max_length=150, default="sin nombre")  # se modificó "descripción" por "nombre"
    descripcion = models.TextField(null=True, blank=True)  # se añade descripción según requisitos
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    codigo_barras = models.CharField(max_length=50, null=True, blank=True)
    codigo_interno = models.CharField(max_length=50, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    fecha_vencimiento = models.DateField(null=True, blank=True) # se añadió fecha de vencimiento

    def __str__(self):
        return self.nombre

#modelo kardex
class Kardex(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    detalle = models.TextField(blank=True, null=True)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='movimientos')

    def delete(self, *args, **kwargs):
        # Evitar anular dos veces
        if "ANULADO" not in (self.detalle or ""):
            # Revertir el efecto del movimiento en el stock
            if self.tipo == "entrada":
                self.producto.stock -= self.cantidad
            elif self.tipo == "salida":
                self.producto.stock += self.cantidad
            self.producto.save()

            # Mantiene el tipo original para mantener trazabilidad en la información
            # y marca el detalle como anulado (en lugar de eliminarse)
            self.detalle = f"{(self.detalle or '').strip()} - ANULADO" if (
                        self.detalle or '').strip() else "Registro ANULADO"
            self.save(update_fields=['detalle'])

        return

    def __str__(self):
        estado = " - ANULADO" if "ANULADO" in (self.detalle or "") else ""
        return f"{self.tipo.capitalize()} - {self.producto.nombre}{estado}"
