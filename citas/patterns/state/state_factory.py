from rest_framework.exceptions import ValidationError
from citas.patterns.state import EstadoAgendada, EstadoCancelada, EstadoCompletada
from citas.patterns.state.base import EstadoCita

class EstadoCitaFactory:
    """
    Factory Method para instanciar el Estado correcto
    basado en el string almacenado en la base de datos.
    """
    
    @staticmethod
    def obtener_estado(estado_db: str):
        if estado_db == EstadoCita.AGENDADA:
            return EstadoAgendada()
        elif estado_db == EstadoCita.CANCELADA:
            return EstadoCancelada()
        elif estado_db == EstadoCita.COMPLETADA:
            return EstadoCompletada()
        else:
            raise ValidationError(f"Estado de cita desconocido o inválido: {estado_db}")