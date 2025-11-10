
from ..models import Cita
from .state import EstadoCita

def notificar_observadores(evento: str, cita: Cita):
    """
    Simula un notificador (Patrón Observer).
    se espera que mas adelante, se llame a un servicio de Celery/Redis
    para enviar emails (RF-008).
    
    """
    print(f"--- 📣 NOTIFICACIÓN ({evento}) ---")
    print(f"    Cita: {cita.id}")
    print(f"    Mascota: {cita.mascota.nombre}")
    print(f"    Fecha: {cita.fecha_hora}")
    print(f"    Estado: {cita.estado}")
    print("---------------------------------")