from rest_framework import serializers
from transacciones.models.pago import Pago


class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = [
            'id',
            'factura',
            'metodo_pago',
            'monto',
            'fecha'
        ]
        read_only_fields = ['fecha']