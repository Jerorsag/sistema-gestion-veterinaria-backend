from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from inventario.models import Kardex, kardex


class KardexSerializer(serializers.ModelSerializer):
    codigo_interno = serializers.CharField(source='producto.codigo_interno', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = Kardex
        fields = '__all__'
        read_only_fields = ['fecha']

    def validar_movimiento_no_anulado(self):
        """
        Evita eliminar un movimiento ya anulado.
        """
        if kardex.detalle and "ANULADO" in kardex.detalle:
            raise ValidationError(
                "Este movimiento ya está anulado y no puede eliminarse su registro."
            )