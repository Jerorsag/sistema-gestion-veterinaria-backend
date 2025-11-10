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
    color = models.CharField(max_length=20, default="", blank=True)

    def __str__(self):
        return self.descripcion

#modelo producto
class Producto(models.Model):
    descripcion = models.CharField(max_length=150)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    codigo_barras = models.CharField(max_length=50, default="", blank=True)
    codigo_interno = models.CharField(max_length=50, default="", blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.descripcion

#modelo kardex
class Kardex(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    detalle = models.TextField(blank=True, default="")
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='movimientos')

    def delete(self, *args, **kwargs):
        #Anulación lógica: cuando se intenta eliminar un movimiento, en vez de borrarlo físicamente se marca como anulado y se revierte el stock.
        # Evitar duplicar la anulación si ya está marcada
        if "anulado" not in (self.tipo or ""):
            # Revertir stock del producto: deshacer el efecto original
            if self.tipo == "entrada":
                # si originalmente fue entrada al stock, al anularla restamos
                self.producto.stock -= self.cantidad
            elif self.tipo == "salida":
                # si originalmente fue salida, al anularla sumamos
                self.producto.stock += self.cantidad
            # Guardar stock
            self.producto.save()

            # Marcar el movimiento como anulado (modifica tipo y detalle)
            self.tipo = f"{self.tipo}-anulado"
            self.detalle = f"{(self.detalle or '').strip()} - ANULADO" if (self.detalle or "").strip() else "Registro ANULADO"

            # Guardamos los cambios (usando update_fields para ser explícitos)
            self.save(update_fields=['tipo', 'detalle'])

        # No llamar a super().delete(): no se borra físicamente

    def __str__(self):
        return f"{self.tipo} - {self.producto.descripcion}"
