from rest_framework import serializers
from inventario.models import Kardex


class KardexSerializer(serializers.ModelSerializer):
    codigo_interno = serializers.CharField(source='producto.codigo_interno', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = Kardex
        fields = '__all__'
        read_only_fields = ['fecha']