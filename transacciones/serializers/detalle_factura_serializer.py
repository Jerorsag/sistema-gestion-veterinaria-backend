from rest_framework import serializers
from transacciones.models.detalle_factura import DetalleFactura


class DetalleFacturaSerializer(serializers.ModelSerializer):

    class Meta:
        model = DetalleFactura
        fields = [
            'id',
            'producto',
            'servicio',
            'descripcion',
            'cantidad',
            'precio_unitario',
            'subtotal'
        ]
        read_only_fields = ['subtotal']

    def validate(self, attrs):
        producto = attrs.get('producto')
        servicio = attrs.get('servicio')

        # Validación XOR
        if (producto and servicio) or (not producto and not servicio):
            raise serializers.ValidationError(
                "Debe seleccionar un producto O un servicio, pero no ambos."
            )

        return attrs