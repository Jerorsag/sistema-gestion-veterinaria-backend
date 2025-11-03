from rest_framework import serializers
from .models import Marca, Categoria, Producto, Kardex

class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = '__all__'


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    # Representación anidada para lectura
    marca = MarcaSerializer(read_only=True)
    categoria = CategoriaSerializer(read_only=True)

    # Campos para escritura (aceptan IDs)
    marca_id = serializers.PrimaryKeyRelatedField(
        queryset=Marca.objects.all(), source='marca', write_only=True, required=False
    )
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True, required=False
    )

    class Meta:
        model = Producto
        # incluir los campos de escritura y los del modelo
        fields = [
            'id', 'nombre','descripcion', 'marca', 'categoria', 'marca_id', 'categoria_id',
            'stock', 'stock_minimo', 'codigo_barras', 'codigo_interno',
            'precio_venta', 'precio_compra', 'fecha_vencimiento'
        ]

    def validate(self, data):
        #validaciones a implementar
        return data


class KardexSerializer(serializers.ModelSerializer):
    codigo_interno = serializers.CharField(source='producto.codigo_interno', read_only=True)
    producto_nombre = serializers.CharField(source='producto.descripcion', read_only=True)
    class Meta:
        model = Kardex
        fields = '__all__'
        read_only_fields = ['fecha']
