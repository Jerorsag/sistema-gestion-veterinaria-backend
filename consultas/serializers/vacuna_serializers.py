"""
Serializers para el modelo HistorialVacuna.
"""

from rest_framework import serializers
from consultas.models import HistorialVacuna


class HistorialVacunaSerializer(serializers.ModelSerializer):
    """
    Serializer básico para lectura de historial de vacunas.
    """
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )

    class Meta:
        model = HistorialVacuna
        fields = [
            'id',
            'estado',
            'estado_display',
            'vacunas_descripcion',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']


class HistorialVacunaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar historial de vacunas.
    """
    class Meta:
        model = HistorialVacuna
        fields = [
            'estado',
            'vacunas_descripcion',
        ]

    def validate(self, data):
        """
        si presiona en pendiente o en proceso sale campo para poner cuales vacunes, si presiona al dia
        o ninguna no sale nada
        """
        estado = data.get('estado')
        vacunas_descripcion = data.get('vacunas_descripcion', '').strip()

        # Si NO está "Al día", debe haber descripción
        if estado in ['PENDIENTE', 'EN_PROCESO']:
            if not vacunas_descripcion:
                raise serializers.ValidationError({
                    'vacunas_descripcion': (
                        f'Debe especificar las vacunas cuando el estado es "{dict(HistorialVacuna.ESTADO_CHOICES)[estado]}"'
                    )
                })

        # Si está "al dia" o no tiene "ninguna vacuna" no tiene necesidad de llenar el campo
        if estado in ['AL_DIA', 'NINGUNA']:
            data['vacunas_descripcion'] = ""

        return data

    def to_representation(self, instance):
        """Usar el serializer de lectura para la respuesta"""
        return HistorialVacunaSerializer(instance).data

class HistorialVacunaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar historial de vacunas.
    """
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    consulta_id = serializers.IntegerField(source='consulta.id', read_only=True)
    mascota_nombre = serializers.CharField(
        source='consulta.mascota.nombre',
        read_only=True
    )
    veterinario_nombre = serializers.CharField(
        source='consulta.veterinario.usuario.get_full_name',
        read_only=True
    )

    class Meta:
        model = HistorialVacuna
        fields = [
            'id',
            'consulta_id',
            'mascota_nombre',
            'veterinario_nombre',
            'estado',
            'estado_display',
            'vacunas_descripcion',
            'fecha_registro',
        ]
