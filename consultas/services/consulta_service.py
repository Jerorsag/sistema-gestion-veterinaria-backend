"""
Servicios de lógica de negocio relacionados con las Consultas
Sara Sanchez
03 Noviembre 2025
"""

from django.db import transaction
from citas.patterns.state.state_factory import EstadoCitaFactory
from consultas.models import (
    Consulta,
    Prescripcion,
    Examen,
    HistorialVacuna
)



@transaction.atomic
def crear_consulta_completa(validated_data):
    """
    Crea una Consulta completa con prescripciones, exámenes y vacunas,
    garantizando integridad con transacciones.
    """

    # Extraer datos anidados
    prescripciones_data = validated_data.pop('prescripciones', [])
    examenes_data = validated_data.pop('examenes', [])
    vacunas_data = validated_data.pop('vacunas', None)

    # Crear consulta principal
    consulta = Consulta.objects.create(**validated_data)

    if consulta.cita:
        try:
            # Obtenemos el manejador del estado actual de la cita (Ej: EstadoAgendada)
            estado_handler = EstadoCitaFactory.obtener_estado(consulta.cita.estado)

            # Ejecutamos la transición a 'COMPLETADA'
            estado_handler.completar(consulta.cita)

        except Exception as e:
            # Opcional: Loguear el error, pero no interrumpir la creación de la consulta
            # o lanzar un error si es estricto que la cita cambie de estado.
            print(f"Advertencia: No se pudo completar la cita {consulta.cita.id}: {e}")

    # Crear prescripciones
    for p_data in prescripciones_data:
        Prescripcion.objects.create(
            consulta=consulta,
            **p_data
        )

    # Crear exámenes
    for e_data in examenes_data:
        Examen.objects.create(
            consulta=consulta,
            **e_data
        )

    # Crear registro de vacunas
    if vacunas_data:
        # Asegurar que vacunas_descripcion nunca sea None
        if vacunas_data.get('vacunas_descripcion') is None:
            vacunas_data['vacunas_descripcion'] = ""
        HistorialVacuna.objects.create(
            consulta=consulta,
            **vacunas_data
        )

    return consulta

def crear_consulta(data, veterinario):
    """
    Crea una consulta y procesa su historia clínica, vacunas, etc.
    """
    consulta = Consulta.objects.create(
        veterinario=veterinario,
        **data
    )

    # ▶ Aquí llamas a servicios externos:
    from .historia_service import gestionar_historia_clinica
    gestionar_historia_clinica(consulta)

    return consulta


def obtener_datos_personales(consulta):
    """
    Delegación para datos personales.
    """
    return consulta.get_datos_personales()