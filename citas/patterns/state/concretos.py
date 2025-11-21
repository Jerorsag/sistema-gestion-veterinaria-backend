from rest_framework.exceptions import ValidationError
from .base import EstadoCita

class EstadoAgendada(EstadoCita):
    def cancelar(self, cita):
        # Actualizamos el estado usando la constante de la base
        cita.estado = EstadoCita.CANCELADA
        cita.save()

    def reagendar(self, cita, nueva_fecha):
        cita.fecha_hora = nueva_fecha
        # Se mantiene en estado AGENDADA
        cita.estado = EstadoCita.AGENDADA 
        cita.save()

    def completar(self, cita):
        cita.estado = EstadoCita.COMPLETADA
        cita.save()


class EstadoCancelada(EstadoCita):
    def cancelar(self, cita):
        raise ValidationError("Esta cita ya ha sido cancelada previamente.")

    def reagendar(self, cita, nueva_fecha):
        raise ValidationError("No se puede reagendar una cita cancelada. Debe crear una nueva.")

    def completar(self, cita):
        raise ValidationError("No se puede completar una cita cancelada.")


class EstadoCompletada(EstadoCita):
    def cancelar(self, cita):
        raise ValidationError("No se puede cancelar una cita que ya fue completada.")

    def reagendar(self, cita, nueva_fecha):
        raise ValidationError("No se puede reagendar una cita completada.")

    def completar(self, cita):
        raise ValidationError("La cita ya está marcada como completada.")