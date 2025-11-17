from datetime import datetime, time, timedelta
from django.utils import timezone
from ..models import Cita
from .state import EstadoCita

def obtener_horarios_disponibles(veterinario_id: str, fecha: datetime.date) -> list:
    """
    Servicio que calcula los horarios disponibles (Patrón Composite).
    Cumple con RF-005 (Visualizar Calendario) y CP-021.
    
    RESPONSABILIDAD ÚNICA: Calcular la disponibilidad de un veterinario 
    en una fecha específica.
    """

    # 1. Definir el horario base (Composite Principal): 8am a 5pm, bloques de 30 min
    horario_base_dia = []
    hora_inicio = time(8, 0)
    hora_fin = time(17, 0) # 5 PM
    intervalo = timedelta(minutes=30)


    # Combinamos la fecha (ej. 2025-11-03) con la hora (ej. 08:00)

    hora_actual = datetime.combine(fecha, hora_inicio)
    hora_fin_dt = datetime.combine(fecha, hora_fin)

    while hora_actual < hora_fin_dt:
        # Hacemos que la hora sea "consciente" de la zona horaria
        hora_actual_aware = timezone.make_aware(hora_actual)

        if fecha == timezone.now().date(): # Si la cita es para hoy
            if hora_actual_aware > timezone.now(): # Solo mostrar horas que no hayan pasado
                horario_base_dia.append(hora_actual.time())
        elif fecha > timezone.now().date(): # Si es un día futuro
            horario_base_dia.append(hora_actual.time()) # Mostrar todas las horas

        hora_actual += intervalo

    # 2. Obtener los horarios ocupados (Composite a restar)
    citas_programadas = Cita.objects.filter(
        veterinario_id=veterinario_id,
        fecha_hora__date=fecha,
        estado=EstadoCita.AGENDADA# Solo contamos las AGENDADAS
    ).values_list('fecha_hora', flat=True)


# Convertimos los datetimes completos a solo la hora (ej. 09:30:00)
    horarios_ocupados = {
        cita_dt.astimezone(timezone.get_current_timezone()).time() 
        for cita_dt in citas_programadas
    }

    # 3. Restar (Composite.Resultado = Base - Ocupados)
    horarios_libres = [hora for hora in horario_base_dia if hora not in horarios_ocupados]

# Formatear la salida a formato "HH:MM"
    return [hora.strftime("%H:%M") for hora in horarios_libres]