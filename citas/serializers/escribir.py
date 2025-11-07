# Estos serializers se usan para recibir datos (POST/PUT/PATCH). Validan y llaman a la capa de servicios.
from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied 
from ..services import (
    agendar_nueva_cita, 
    reagendar_cita
)

from citas.models.Choices import EstadoCita


class CrearCitaSerializer(serializers.Serializer):
    """
    Serializer para CREAR (POST) una Cita.
    Valida y llama al servicio agendar_nueva_cita.
    """
    mascota_id = serializers.UUIDField(required=True)
    veterinario_id = serializers.UUIDField(required=True)
    servicio_id = serializers.UUIDField(required=True)
    fecha_hora = serializers.DateTimeField(required=True)
    observaciones = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_fecha_hora(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("No se pueden agendar citas en el pasado.")
        return value

    def create(self, validated_data):
        """Llama al servicio para crear la cita."""
        usuario = self.context['request'].user

        # 1. Sacamos el objeto datetime del diccionario
        fecha_dt = validated_data.pop('fecha_hora') 
        
        # 2. La convertimos de vuelta a "texto" (string)
        fecha_str = fecha_dt.isoformat()
        
        # 3. Nos aseguramos que el texto termine en 'Z' (formato UTC)
        if fecha_dt.tzinfo == timezone.utc:
             fecha_str = fecha_str.replace('+00:00', 'Z')
        
        # 4. Volvemos a meterla al diccionario, pero ahora como "texto"
        validated_data['fecha_hora'] = fecha_str
        
        try:
            return agendar_nueva_cita(data=validated_data, usuario=usuario)
        except (ValidationError, PermissionDenied) as e:
            raise e
        except Exception as e:
            raise serializers.ValidationError(f"Error inesperado al agendar: {e}")


class ReagendarCitaSerializer(serializers.Serializer):
    """
    Serializer para REAGENDAR (PUT/PATCH) una Cita.
    Valida y llama al servicio reagendar_cita.
    """
    fecha_hora = serializers.DateTimeField(required=True)

    def validate_fecha_hora(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("No se pueden reagendar citas al pasado.")
        return value

    def update(self, instance, validated_data):
        """Llama al servicio para reagendar (actualizar) la cita."""
        usuario = self.context['request'].user
        
        nueva_fecha_dt = validated_data['fecha_hora']
        nueva_fecha_str = nueva_fecha_dt.isoformat()
        
        if nueva_fecha_dt.tzinfo == timezone.utc:
             nueva_fecha_str = nueva_fecha_str.replace('+00:00', 'Z')

        try:
            # 'instance' es la cita que se está actualizando
            return reagendar_cita(
                cita_id=instance.id, 
                nueva_fecha_hora_str=nueva_fecha_str, 
                usuario=usuario
            )
        except (ValidationError, PermissionDenied) as e:
            raise e
        except Exception as e:
            raise serializers.ValidationError(f"Error inesperado al reagendar: {e}")
