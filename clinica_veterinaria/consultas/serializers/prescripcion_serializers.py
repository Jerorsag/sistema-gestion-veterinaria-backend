"""
Serializers para el modelo Prescripcion.
"""

from rest_framework import serializers
from clinica_veterinaria.consultas.models import Prescripcion
from inventario.models import Medicamento


class PrescripcionListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar prescripciones.
    """

    medicamento_nombre = serializers.CharField(
        source='medicamento.nombre',
        read_only=True
    )


    class Meta:
        model = Prescripcion
        fields = [
            'id',
            'medicamento',
            'medicamento_nombre',
            'cantidad',
            'indicaciones',
        ]


class PrescripcionSerializer(serializers.ModelSerializer):
    """
    Incluye información detallada del medicamento completo para lectura de prescripciones.
    """

    medicamento_nombre = serializers.CharField(
        source='medicamento.nombre',
        read_only=True
    )

    medicamento_descripcion = serializers.CharField(
        source='medicamento.descripcion',
        read_only=True
    )

    stock_disponible = serializers.IntegerField(
        source='medicamento.cantidad_disponible',
        read_only=True
    )


    class Meta:
        model = Prescripcion
        fields = [
            'id',
            'consulta',
            'medicamento',
            'medicamento_nombre',
            'medicamento_descripcion',
            'cantidad',
            'stock_disponible',
            'indicaciones',
            'fecha_prescripcion',
        ]
        read_only_fields = ['id', 'fecha_prescripcion']


class PrescripcionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear prescripciones.
    """

    medicamento_nombre = serializers.CharField(
        source='medicamento.nombre',
        read_only=True
    )

    stock_disponible = serializers.IntegerField(
        source='medicamento.cantidad_disponible',
        read_only=True
    )

    class Meta:
        model = Prescripcion
        fields = [
            'consulta',
            'medicamento',
            'medicamento_nombre',
            'cantidad',
            'stock_disponible',
            'indicaciones',
        ]

    def validate_medicamento(self, value):
        """
        Valida que el medicamento esté disponible.
        """
        if not value:
            raise serializers.ValidationError("Debe seleccionar un medicamento del inventario")

        # Validar que no esté vencido
        if value.esta_vencido():
            raise serializers.ValidationError(
                f"El medicamento '{value.nombre}' está vencido. "
                f"Fecha de vencimiento: {value.fecha_vencimiento.strftime('%d/%m/%Y')}"
            )

        return value

    def validate_cantidad(self, value):
        """Valida que la cantidad sea al menos 1"""
        if value < 1:
            raise serializers.ValidationError("La cantidad debe ser al menos 1")
        return value

    def validate(self, data):
        """
        Validación cruzada: medicamento vs cantidad.
        """
        medicamento = data.get('medicamento')
        cantidad = data.get('cantidad')

        if medicamento and cantidad:
            if medicamento.cantidad_disponible < cantidad:
                raise serializers.ValidationError({
                    'cantidad': (
                        f'Stock insuficiente. Solo hay {medicamento.cantidad_disponible} '
                        f'unidades disponibles de {medicamento.nombre}'
                    )
                })

        return data

    def to_representation(self, instance):
        """Usar el serializer completo para la respuesta"""
        return PrescripcionSerializer(instance).data