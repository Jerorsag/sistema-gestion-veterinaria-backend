"""
Servicios de gestión y actualización de Historias Clínicas
Sara Sanchez
03 Noviembre 2025
"""

from ..models import HistoriaClinica
from consultas.patterns.composite import HistoriaClinicaCompuesta, ConsultaHoja
from consultas.patterns.builder import HistoriaClinicaBuilder

def gestionar_historia_clinica(consulta):
    """
    Crea automáticamente una HistoriaClinica si no existe
    y actualiza el estado de vacunación con base en la consulta.
    """
    historia, _ = HistoriaClinica.objects.get_or_create(mascota=consulta.mascota)

    vacuna_registro = consulta.vacunas.first()
    if vacuna_registro:
        historia.actualizar_estado_vacunacion(vacuna_registro.estado)

def generar_estructura_historia(historia_clinica):
    historia_compuesta = HistoriaClinicaCompuesta(historia_clinica)
    for consulta in historia_clinica.mascota.consultas.all():
        historia_compuesta.agregar(ConsultaHoja(consulta))
    return historia_compuesta.mostrar()

def crear_historia_completa(mascota, veterinario, descripcion, diagnostico, medicamento, cantidad):
    builder = HistoriaClinicaBuilder(mascota)
    historia = (
        builder.crear_historia()
        .agregar_consulta(veterinario, descripcion, diagnostico)
        .agregar_prescripcion(medicamento, cantidad)
        .obtener_historia()
    )
    return historia