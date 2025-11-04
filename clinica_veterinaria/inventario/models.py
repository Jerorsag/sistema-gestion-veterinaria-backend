from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


# Modelo Marca
class Marca(models.Model):
    descripcion = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        # Normalizar a Title Case antes de guardar para validaciones
        if self.descripcion:
            self.descripcion = self.descripcion.strip().title()
        super().save(*args, **kwargs)

    def clean(self):
        # Validación adicional para evitar duplicados
        if self.descripcion:
            self.descripcion = self.descripcion.strip().title()
            qs = Marca.objects.filter(descripcion__iexact=self.descripcion)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'descripcion': 'Ya existe una marca con este nombre.'})

    def __str__(self):
        return self.descripcion

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"


# Modelo Categoria
class Categoria(models.Model):
    descripcion = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Normalizar a Title Case antes de guardar para validaciones
        if self.descripcion:
            self.descripcion = self.descripcion.strip().title()
        super().save(*args, **kwargs)

    def clean(self):
        # Validación adicional para evitar duplicados
        if self.descripcion:
            self.descripcion = self.descripcion.strip().title()
            qs = Categoria.objects.filter(descripcion__iexact=self.descripcion)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'descripcion': 'Ya existe una categoría con este nombre.'})

    def __str__(self):
        return self.descripcion

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


# Modelo Producto
class Producto(models.Model):
    nombre = models.CharField(max_length=150, default="sin nombre")
    descripcion = models.TextField(null=True, blank=True)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    codigo_barras = models.CharField(max_length=50, null=True, blank=True)
    codigo_interno = models.CharField(max_length=50, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Normalizar nombre a Title Case para validaciones
        if self.nombre:
            self.nombre = self.nombre.strip().title()

        # Normalizar códigos (trim espacios)
        if self.codigo_barras:
            self.codigo_barras = self.codigo_barras.strip()
        if self.codigo_interno:
            self.codigo_interno = self.codigo_interno.strip()

        super().save(*args, **kwargs)

    def clean(self):
        errors = {}

        # Normalizar antes de validar
        if self.nombre:
            self.nombre = self.nombre.strip().title()
        if self.codigo_barras:
            self.codigo_barras = self.codigo_barras.strip()
        if self.codigo_interno:
            self.codigo_interno = self.codigo_interno.strip()

        # Validar nombre único
        if self.nombre:
            qs = Producto.objects.filter(nombre__iexact=self.nombre)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['nombre'] = 'Ya existe un producto con este nombre.'

        # Validar código de barras único (si se proporciona)
        if self.codigo_barras:
            qs = Producto.objects.filter(codigo_barras__iexact=self.codigo_barras)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['codigo_barras'] = 'Ya existe un producto con este código de barras.'

        # Validar código interno único (si se proporciona)
        if self.codigo_interno:
            qs = Producto.objects.filter(codigo_interno__iexact=self.codigo_interno)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['codigo_interno'] = 'Ya existe un producto con este código interno.'
            # Stock mínimo debe ser menor o igual al stock
        if self.stock_minimo > self.stock:
            errors['stock_minimo'] = 'El stock mínimo no puede ser mayor al stock actual.'

            # Precio de compra debe ser menor al precio de venta
        if self.precio_compra >= self.precio_venta and self.precio_venta > 0:
            errors['precio_compra'] = 'El precio de compra debe ser menor al precio de venta.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"


# Modelo Kardex
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

    class Meta:
        verbose_name = "Kardex"
        verbose_name_plural = "Kardex"
        ordering = ['-fecha']