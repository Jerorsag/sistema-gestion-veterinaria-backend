"""
Servicios de lógica de negocio relacionados con las Consultas
Sara Sanchez
03 Noviembre 2025
"""

def get_datos_personales(consulta):
    """
    Retorna los datos personales de la mascota para auto-rellenar el formulario.
    """
    mascota = consulta.mascota
    return {
        'nombre_mascota': mascota.nombre,
        'nombre_propietario': mascota.propietario.get_full_name(),
        'edad': mascota.calcular_edad(),
        'tipo_especie': mascota.especie,
        'raza': mascota.raza.nombre if mascota.raza else "No especificada",
        'estado_vacunacion': mascota.estado_vacunacion,
    }


def get_estado_vacunacion_consulta(consulta):
    """
    Retorna el estado de vacunación registrado en esta consulta.
    """
    vacuna = consulta.vacunas.first()
    return vacuna.get_estado_display() if vacuna else "No registrado"
