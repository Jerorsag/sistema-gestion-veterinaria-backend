# Importamos las funciones "públicas" que queremos exponer
# al resto de la aplicación (especialmente a views.py)

from citas.patterns.composite import obtener_horarios_disponibles
from  citas.patterns.command import agendar_nueva_cita, cancelar_cita, reagendar_cita

# Nota cómo NO exponemos "notificar_observadores".
# Esa función es un detalle interno de la capa de servicios.
# El view.py no necesita saber que existe.