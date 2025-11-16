# notificaciones/handlers/_helpers.py

from citas.models import Cita
from consultas.models import Consulta # Importamos el modelo de Consulta
from usuarios.models import Usuario, Cliente

"""
Responsabilidad Única: Convertir instancias de modelo (Cita, Consulta)
en el "contexto" genérico que nuestros servicios de notificación esperan.
"""

def preparar_contexto_cita(cita: Cita) -> dict:
    """Extrae datos de una Cita para el contexto de notificación."""
    try:
        # Hacemos la consulta optimizada aquí
        cita_con_datos = Cita.objects.select_related(
            'mascota__cliente__usuario', 'veterinario', 'servicio'
        ).get(id=cita.id)
        
        usuario_cliente = cita_con_datos.mascota.cliente.usuario

        context = {
            # Datos del destinatario
            'propietario_nombre': usuario_cliente.nombre,
            'to_email': usuario_cliente.email,
            
            # Datos específicos del evento
            'mascota_nombre': cita_con_datos.mascota.nombre,
            'fecha_hora': cita_con_datos.fecha_hora.strftime('%d-%b-%Y %I:%M %p'),
            'veterinario_nombre': cita_con_datos.veterinario.get_full_name(),
            'servicio_nombre': cita_con_datos.servicio.nombre
        }
        return context
    except Exception as e:
        print(f"Error al preparar contexto de Cita {cita.id}: {e}")
        return None


def preparar_contexto_consulta(consulta: Consulta) -> dict:
    """Extrae datos de una Consulta para el contexto de notificación."""
    try:
        # Optimizamos la consulta para los datos de una consulta
        consulta_con_datos = Consulta.objects.select_related(
            'mascota__cliente__usuario', 'veterinario'
        ).get(id=consulta.id)
        
        usuario_cliente = consulta_con_datos.mascota.cliente.usuario

        context = {
            # Datos del destinatario
            'propietario_nombre': usuario_cliente.nombre,
            'to_email': usuario_cliente.email,
            
            # Datos específicos del evento
            'mascota_nombre': consulta_con_datos.mascota.nombre,
            'fecha_consulta': consulta_con_datos.fecha_consulta.strftime('%d-%b-%Y'),
            'veterinario_nombre': consulta_con_datos.veterinario.get_full_name(),
            'diagnostico': consulta_con_datos.diagnostico
        }
        return context
    except Exception as e:
        print(f"Error al preparar contexto de Consulta {consulta.id}: {e}")
        return None