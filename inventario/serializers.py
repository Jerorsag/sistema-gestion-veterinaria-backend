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
    marca = MarcaSerializer(read_only=True)
    categoria = CategoriaSerializer(read_only=True)

    class Meta:
        model = Producto
        fields = '__all__'

class KardexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kardex
        fields = '__all__'
        read_only_fields = ['fecha']
