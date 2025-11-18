from rest_framework import serializers
from transacciones.models.factura import Factura
from transacciones.serializers.detalle_factura_serializer import DetalleFacturaSerializer


class FacturaSerializer(serializers.ModelSerializer):
    detalles = DetalleFacturaSerializer(many=True)

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
        read_only_fields = ['total', 'fecha']

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
        factura.actualizar_total()

        return factura