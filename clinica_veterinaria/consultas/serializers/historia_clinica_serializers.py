# apps/consultas/serializers/historia_clinica_serializers.py

"""
Serializers para el modelo HistoriaClinica.
Implementa el COMPOSITE PATTERN:

"""

from rest_framework import serializers
from clinica_veterinaria.consultas.models import HistoriaClinica
from apps.mascotas.models import Mascota
from .consulta_serializers import ConsultaDetailSerializer


class HistoriaClinicaSerializer(serializers.ModelSerializer):
    """
    Serializer básico para Historia Clínica.
    Usado en listas y vistas generales.
    """

    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    propietario_nombre = serializers.CharField(
        source='mascota.propietario.get_full_name',
        read_only=True
    )
    estado_vacunacion_display = serializers.CharField(
        source='get_estado_vacunacion_actual_display',
        read_only=True
    )
    total_consultas = serializers.SerializerMethodField()
    ultima_consulta_fecha = serializers.SerializerMethodField()

    class Meta:
        model = HistoriaClinica
        fields = [
            'id',
            'mascota',
            'mascota_nombre',
            'propietario_nombre',
            'fecha_creacion',
            'fecha_actualizacion',
            'estado_vacunacion_actual',
            'estado_vacunacion_display',
            'total_consultas',
            'ultima_consulta_fecha',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

    def get_total_consultas(self, obj):
        """Retorna el número total de consultas"""
        return obj.get_total_consultas()

    def get_ultima_consulta_fecha(self, obj):
        """Retorna la fecha de la última consulta"""
        ultima = obj.get_ultima_consulta()
        return ultima.fecha_consulta if ultima else None


class HistoriaClinicaDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para Historia Clínica consolidada.
    """

    # Datos de la mascota (Composite root)
    mascota_datos = serializers.SerializerMethodField(
        help_text="Datos completos de la mascota"
    )

    # Propietario
    propietario = serializers.SerializerMethodField(
        help_text="Datos del propietario de la mascota"
    )

    # Lista de consultas (Components)
    consultas = serializers.SerializerMethodField(
        help_text="Todas las consultas ordenadas cronológicamente (más recientes primero)"
    )

    # Estadísticas generales
    estadisticas = serializers.SerializerMethodField(
        help_text="Estadísticas generales de la historia clínica"
    )

    # Medicamentos más frecuentes
    medicamentos_frecuentes = serializers.SerializerMethodField(
        help_text="Top 5 medicamentos más prescritos"
    )

    class Meta:
        model = HistoriaClinica
        fields = [
            'id',
            'mascota',
            'mascota_datos',
            'propietario',
            'fecha_creacion',
            'fecha_actualizacion',
            'estado_vacunacion_actual',
            'consultas',
            'estadisticas',
            'medicamentos_frecuentes',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

    def get_mascota_datos(self, obj):
        """
        Retorna datos completos de la mascota.
        """
        mascota = obj.mascota
        return {
            'id': mascota.id,
            'nombre': mascota.nombre,
            'edad': mascota.calcular_edad(),
            'especie': mascota.especie,
            'raza': mascota.raza.nombre if mascota.raza else "No especificada",
            'sexo': mascota.get_sexo_display() if hasattr(mascota, 'sexo') else None,
            'fecha_nacimiento': mascota.fecha_nacimiento,
        }

    def get_propietario(self, obj):
        """
        Retorna datos del propietario.
        """
        propietario = obj.mascota.propietario
        return {
            'id': propietario.id,
            'nombre_completo': propietario.get_full_name(),
            'email': propietario.email,
            'telefono': getattr(propietario, 'telefono', None),
        }

    def get_consultas(self, obj):
        """
        Retorna todas las consultas con sus relaciones.
        """
        consultas = obj.get_consultas_ordenadas()
        return ConsultaDetailSerializer(consultas, many=True, context=self.context).data

    def get_estadisticas(self, obj):
        """
        Retorna estadísticas generales de la historia clínica.
        """
        ultima_consulta = obj.get_ultima_consulta()
        primera_consulta = obj.mascota.consultas.order_by('fecha_consulta').first()

        return {
            'total_consultas': obj.get_total_consultas(),
            'total_prescripciones': obj.get_total_prescripciones(),
            'primera_consulta': primera_consulta.fecha_consulta if primera_consulta else None,
            'ultima_consulta': ultima_consulta.fecha_consulta if ultima_consulta else None,
        }

    def get_medicamentos_frecuentes(self, obj):
        """
        Retorna los 5 medicamentos más prescritos en la historia de esta mascota.
        """
        return list(obj.get_medicamentos_frecuentes(limit=5))


class UltimaConsultaSerializer(serializers.Serializer):
    """
    Serializer para la vista "Ver Ultima Historia Clinica".
    """

    mascota_nombre = serializers.CharField()
    propietario_nombre = serializers.CharField()
    ultima_consulta = ConsultaDetailSerializer()

    def to_representation(self, historia_clinica):
        """
        Transforma la HistoriaClinica en el formato esperado.
        """
        ultima = historia_clinica.get_ultima_consulta()

        if not ultima:
            return {
                'mascota_nombre': historia_clinica.mascota.nombre,
                'propietario_nombre': historia_clinica.mascota.propietario.get_full_name(),
                'ultima_consulta': None,
                'mensaje': 'Esta mascota no tiene consultas registradas'
            }

        return {
            'mascota_nombre': historia_clinica.mascota.nombre,
            'propietario_nombre': historia_clinica.mascota.propietario.get_full_name(),
            'ultima_consulta': ConsultaDetailSerializer(ultima, context=self.context).data
        }