from abc import ABC, abstractmethod

class EstadoCita(ABC):
    """
    Clase base abstracta y contenedor de constantes para los estados de una cita.
    """
    
    # --- Constantes para el Modelo (Persistencia) ---
    AGENDADA = 'AGENDADA'
    CANCELADA = 'CANCELADA'
    COMPLETADA = 'COMPLETADA'

    CHOICES = [
        (AGENDADA, 'Agendada'),
        (CANCELADA, 'Cancelada'),
        (COMPLETADA, 'Completada'),
    ]

    # --- Contrato de Comportamiento (Patrón State) ---
    
    @abstractmethod
    def cancelar(self, cita):
        pass

    @abstractmethod
    def reagendar(self, cita, nueva_fecha):
        pass

    @abstractmethod
    def completar(self, cita):
        pass