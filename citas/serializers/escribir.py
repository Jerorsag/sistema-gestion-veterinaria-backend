# Estos serializers se usan para recibir datos (POST/PUT/PATCH). Validan y llaman a la capa de servicios.
from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied 
from citas.models import Cita,Servicio
from ..services import agendar_nueva_cita, reagendar_cita
from citas.patterns.state import EstadoCita


class CrearCitaSerializer(serializers.Serializer):
    """
    Serializer para CREAR (POST) una Cita.
    Valida y llama al servicio agendar_nueva_cita.
    """
    mascota_id = serializers.IntegerField(required=True)
    veterinario_id = serializers.IntegerField(required=True)
    servicio_id = serializers.IntegerField(required=True)
    fecha_hora = serializers.DateTimeField(required=True)
    observaciones = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_fecha_hora(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("No se pueden agendar citas en el pasado.")
        return value

    def create(self, validated_data):
        """Llama al servicio para crear la cita."""
        usuario = self.context['request'].user
        
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
        
class ServicioWriteSerializer(serializers.ModelSerializer):
    """
    Serializer para CREAR (POST) Servicios.
    """
    class Meta:
        model = Servicio
        fields = ['nombre', 'costo']
