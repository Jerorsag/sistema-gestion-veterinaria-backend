from rest_framework import serializers
from transacciones.models.factura import Factura
from transacciones.serializers.detalle_factura_serializer import DetalleFacturaSerializer


class FacturaSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(read_only=True)
    detalles = DetalleFacturaSerializer(many=True, read_only=True)

    class Meta:
        model = Factura
        fields = [
            'id',
            'estado',
            'cliente',
            'cita',
            'consulta',
            'fecha',
            'total',
            'detalles'
        ]
        read_only_fields = ['total', 'fecha', 'cliente']

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles', [])

        factura = Factura.objects.create(**validated_data)

        # Crear detalles
        for detalle_data in detalles_data:
            DetalleFacturaSerializer().create({
                **detalle_data,
                "factura": factura
            })

        # Forzar recálculo del total
        factura.recalcular_totales()

        return factura