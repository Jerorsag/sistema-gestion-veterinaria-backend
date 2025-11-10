from django.contrib import admin
from django.utils.html import format_html

from .models import Marca, Categoria, Producto, Kardex


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("descripcion", "marca", "categoria", "stock", "precio_venta")
    list_filter = ("marca", "categoria")
    search_fields = ("descripcion",)

@admin.register(Kardex)
class KardexAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'tipo', 'cantidad', 'detalle', 'fecha')
    list_filter = ['tipo']
    search_fields = ['detalle', 'producto__descripcion']

    def has_delete_permission(self, request, obj=None):
        # Permitimos la acción de borrar en el admin (para que el usuario vea Eliminar)
        return True

    def delete_model(self, request, obj):
        """
        Llamada cuando se elimina un solo objeto desde el admin detail view.
        Llamamos al delete() del modelo (que anula en vez de borrar).
        """
        obj.delete()

    def delete_queryset(self, request, queryset):
        """
        Importante: el admin por defecto usa queryset.delete() para bulk delete,
        eso no llamaría a model.delete(). Recorremos e invocamos delete() por cada objeto.
        """
        for obj in queryset:
            obj.delete()


admin.site.register(Marca)
admin.site.register(Categoria)
