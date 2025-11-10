# citas/choices.py

class EstadoCita:
    """
    Define los estados posibles para el ciclo de vida de una Cita.
    Agrupa la lógica de negocio de los estados en un solo lugar.
    """

    # --- Implementación de Patrón State ---
    # Definimos los únicos estados posibles (Patrón State)
    
    AGENDADA = 'AGENDADA'
    CANCELADA = 'CANCELADA'
    COMPLETADA = 'COMPLETADA'


    # Si se añade un nuevo estado, SOLO se modifica este archivo.
    CHOICES = [
        (AGENDADA, 'Agendada'),
        (CANCELADA, 'Cancelada'),
        (COMPLETADA, 'Completada'),
    ]

    @classmethod
    def es_estado_valido(cls, estado):
        return estado in [cls.AGENDADA, cls.CANCELADA, cls.COMPLETADA]