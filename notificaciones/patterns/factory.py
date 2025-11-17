from .template_method import BaseNotification
# Importamos desde nuestra subcarpeta de estrategias
# Import strategies
from .strategies.strategy_cita import (CitaAgendadaEmail,CitaCanceladaEmail,CitaReagendadaEmail)
from .strategies.strategy_reset import ResetPasswordEmail
# Futuro: 
# from .strategies.strategy_consulta import ConsultaFinalizadaEmail

"""
Implementa el Patrón Factory Method.
"""

class NotificationFactory:
    """
    Fábrica que decide qué tipo de notificación construir
    basado en un "evento".
    Su única responsabilidad es la "creación" del objeto correcto.
    """
    
    @staticmethod
    def get_notification(evento: str, context: dict, to_email: str) -> BaseNotification:
        """
        El método "Factory".
        """
        
        # Mapeamos el string del evento a la Clase constructora
        estrategias = {
            # --- Eventos de Citas ---
            "CITA_CREADA": CitaAgendadaEmail,
            "CITA_CANCELADA": CitaCanceladaEmail,
            "CITA_REAGENDADA": CitaReagendadaEmail,
            
            # --- Eventos de Consultas (Futuro) ---
            # "CONSULTA_FINALIZADA": ConsultaFinalizadaEmail, 
            # --- Eventos de Reset Password ---
            "RESET_PASSWORD": ResetPasswordEmail,
        }

        ConstructorDeNotificacion = estrategias.get(evento)

        if ConstructorDeNotificacion:
            return ConstructorDeNotificacion(context, to_email)
        else:
            raise ValueError(f"Evento de notificación desconocido: {evento}")