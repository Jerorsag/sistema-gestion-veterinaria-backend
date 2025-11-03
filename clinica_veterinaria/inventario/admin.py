from django.contrib import admin
from django.utils.html import format_html
from .models import Marca, Categoria, Producto, Kardex


#PRODUCTO
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "marca",
        "categoria",
        "stock",
        "precio_venta",
        "fecha_vencimiento",
    )
    list_filter = ("marca", "categoria")
    search_fields = ("nombre", "descripcion")


    fields = (
        "nombre",
        "descripcion",
        "marca",
        "categoria",
        "stock",
        "stock_minimo",
        "codigo_barras",
        "codigo_interno",
        "precio_venta",
        "precio_compra",
        "fecha_vencimiento",
    )


# KARDEX
@admin.register(Kardex)
class KardexAdmin(admin.ModelAdmin):
    #    El Kardex no se elimina físicamente, si el usuario selecciona "Eliminar", se ejecuta el metodo delete() del modelo, que marca el movimiento como anulado
    list_display = ('codigo_interno_producto', "producto", "tipo", "cantidad", "detalle", "fecha")
    list_filter = ["tipo"]
    search_fields = ["detalle", "producto__nombre",  'producto__codigo_interno']


    def codigo_interno_producto(self, obj):
        return obj.producto.codigo_interno or '---'
    codigo_interno_producto.short_description = 'Código Interno'


    def has_delete_permission(self, request, obj=None):
        # Permitimos la opción de borrar, pero internamente será una anulación
        return True

    def delete_model(self, request, obj):
        """
        Llamada cuando se elimina un solo objeto desde la vista de detalle en el admin.
        En lugar de eliminarlo, se anula (marca como "anulado" y revierte stock).
        """
        obj.delete()

    def delete_queryset(self, request, queryset):
        """
        El admin por defecto usa queryset.delete() para eliminar en lote.
        Esto no invocaría el método delete() del modelo, así que iteramos manualmente.
        """
        for obj in queryset:
            obj.delete()


#MARCA y CATEGORIA
@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ("descripcion",)
    search_fields = ("descripcion",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("descripcion", "color")
    search_fields = ("descripcion",)
