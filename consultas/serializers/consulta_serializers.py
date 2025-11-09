# apps/consultas/serializers/consulta_serializers.py

"""
Serializers para el modelo Consulta.
Representa el formulario completo "Crear Historias Clínicas".
"""

from rest_framework import serializers
from consultas.models import Consulta, Prescripcion, Examen, HistorialVacuna
from mascotas.models import Mascota
from django.contrib.auth import get_user_model

from .prescripcion_serializers import (
    PrescripcionSerializer,
    PrescripcionCreateSerializer
)
from .examen_serializers import ExamenSerializer, ExamenCreateSerializer
from .vacuna_serializers import HistorialVacunaSerializer, HistorialVacunaCreateSerializer

User = get_user_model()

VETERINARIO_GET = 'veterinario.get_full_name';
class ConsultaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar consultas.
    """

    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    veterinario_nombre = serializers.CharField(
        source='veterinario.get_full_name',
        read_only=True
    )
    estado_vacunacion = serializers.SerializerMethodField()
    total_prescripciones = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = [
            'id',
            'mascota_nombre',
            'veterinario_nombre',
            'fecha_consulta',
            'diagnostico',
            'estado_vacunacion',
            'total_prescripciones',
        ]

    def get_estado_vacunacion(self, obj):
        """Retorna el estado de vacunación registrado en esta consulta"""
        return obj.get_estado_vacunacion_consulta()

    def get_total_prescripciones(self, obj):
        """Retorna la cantidad de medicamentos prescritos"""
        return obj.get_prescripciones_count()


class ConsultaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver una consulta específica como los datos la prescripcion y
    todo lo que fue ordenado.
    """
    # Datos personales (auto-rellenados desde Mascota)
    datos_personales = serializers.SerializerMethodField(
        help_text="Datos de la mascota que se auto-rellenan en el formulario"
    )

    # Veterinario que atendió
    veterinario_nombre = serializers.CharField(
        source=VETERINARIO_GET,
        read_only=True
    )
    prescripciones = PrescripcionSerializer(many=True, read_only=True)
    examenes = ExamenSerializer(many=True, read_only=True)
    vacunas = HistorialVacunaSerializer(many=True, read_only=True)


    class Meta:
        model = Consulta
        fields = [
            'id',
            'mascota',
            'datos_personales',
            'veterinario',
            'veterinario_nombre',
            'fecha_consulta',
            'descripcion_consulta',
            'diagnostico',
            'notas_adicionales',
            'prescripciones',
            'examenes',
            'vacunas',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_datos_personales(self, obj):
        cliente = obj.mascota.cliente if hasattr(obj, 'mascota') and obj.mascota else None
        if cliente:
            return {
                "nombre": f"{cliente.usuario.nombre} {cliente.usuario.apellido}",
                "telefono": getattr(cliente, "telefono", None),
                "direccion": getattr(cliente, "direccion", None),
            }
        return None


class ConsultaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear una consulta completa.
    """

    # Nested serializers para crear en una sola petición
    prescripciones = PrescripcionCreateSerializer(many=True, required=False)
    examenes = ExamenCreateSerializer(many=True, required=False)
    vacunas = HistorialVacunaCreateSerializer(required=False)

    class Meta:
        model = Consulta
        fields = [
            'mascota',
            'veterinario',
            'fecha_consulta',
            'descripcion_consulta',
            'diagnostico',
            'notas_adicionales',
            'prescripciones',
            'examenes',
            'vacunas',
        ]

    def validate_mascota(self, value):
        """Valida que la mascota exista"""
        if not Mascota.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("La mascota seleccionada no existe")
        return value

    def validate_descripcion_consulta(self, value):
        """
        Valida que la descripción no esté vacía."
        """
        if not value or value.strip() == '':
            raise serializers.ValidationError("La descripción de la consulta es obligatoria")
        return value

    def validate_diagnostico(self, value):
        """
        Valida que el diagnóstico no esté vacío.
        """
        if not value or value.strip() == '':
            raise serializers.ValidationError("Debe ingresar un diagnóstico")
        return value

    def create(self, validated_data):
        """
        Crea la consulta con todas sus relaciones anidadas.
        """

        prescripciones_data = validated_data.pop('prescripciones', [])
        examenes_data = validated_data.pop('examenes', [])
        vacunas_data = validated_data.pop('vacunas', None)

        # Crear consulta principal
        consulta = Consulta.objects.create(**validated_data)

        # Crear prescripciones
        for prescripcion_data in prescripciones_data:
            Prescripcion.objects.create(
                consulta=consulta,
                **prescripcion_data
            )

        # Crear exámenes
        for examen_data in examenes_data:
            Examen.objects.create(
                consulta=consulta,
                **examen_data
            )

        # Crear registro de vacunas
        if vacunas_data:
            HistorialVacuna.objects.create(
                consulta=consulta,
                **vacunas_data
            )

        return consulta

    def to_representation(self, instance):
        """Retorna la representación completa después de crear"""
        return ConsultaDetailSerializer(instance, context=self.context).data

class ConsultaUpdateSerializer(serializers.ModelSerializer):
    """
       Serializer para actualizar una consulta completa con sus relaciones anidadas.
        Permite actualizar prescripciones, exámenes y vacunas en una sola petición.
    """
    prescripciones = PrescripcionCreateSerializer(many=True, required=False)
    examenes = ExamenCreateSerializer(many=True, required=False)
    vacunas = HistorialVacunaCreateSerializer(required=False)

    class Meta:
        model = Consulta
        fields = [
            'mascota',
            'veterinario',
            'fecha_consulta',
            'descripcion_consulta',
            'diagnostico',
            'notas_adicionales',
            'prescripciones',
            'examenes',
            'vacunas',
        ]
        read_only_fields = ['mascota']  # No se puede cambiar la mascota de una consulta

    def validate_descripcion_consulta(self, value):
        """Valida que la descripción no esté vacía."""
        if not value or value.strip() == '':
            raise serializers.ValidationError("La descripción de la consulta es obligatoria")
        return value

    def validate_diagnostico(self, value):
        """Valida que el diagnóstico no esté vacío."""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Debe ingresar un diagnóstico")
        return value

    def update(self, instance, validated_data):
        """
        Actualiza la consulta y sus relaciones anidadas.
        """
        # Extraer datos anidados
        prescripciones_data = validated_data.pop('prescripciones', None)
        examenes_data = validated_data.pop('examenes', None)
        vacunas_data = validated_data.pop('vacunas', None)

        # Actualizar campos básicos de la consulta
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Actualizar prescripciones si se proporcionaron
        if prescripciones_data is not None:
            # Eliminar prescripciones existentes
            instance.prescripciones.all().delete()

            # Crear nuevas prescripciones
            for prescripcion_data in prescripciones_data:
                Prescripcion.objects.create(
                    consulta=instance,
                    **prescripcion_data
                )

        # Actualizar exámenes si se proporcionaron
        if examenes_data is not None:
            # Eliminar exámenes existentes
            instance.examenes.all().delete()

            # Crear nuevos exámenes
            for examen_data in examenes_data:
                Examen.objects.create(
                    consulta=instance,
                    **examen_data
                )

        # Actualizar vacunas si se proporcionaron
        if vacunas_data is not None:
            # Eliminar registro de vacunas existente
            instance.vacunas.all().delete()

            # Crear nuevo registro de vacunas
            HistorialVacuna.objects.create(
                consulta=instance,
                **vacunas_data
            )

        return instance

    def to_representation(self, instance):
        """Retorna la representación completa después de actualizar"""
        return ConsultaDetailSerializer(instance, context=self.context).data

class ConsultaSerializer(serializers.ModelSerializer):
    """
    Serializer general para Consulta.
    Usado para operaciones básicas de lectura/escritura.
    """

    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    veterinario_nombre = serializers.CharField(
        source=VETERINARIO_GET,
        read_only=True
    )

    class Meta:
        model = Consulta
        fields = [
            'id',
            'mascota',
            'mascota_nombre',
            'veterinario',
            'veterinario_nombre',
            'fecha_consulta',
            'descripcion_consulta',
            'diagnostico',
            'notas_adicionales',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']